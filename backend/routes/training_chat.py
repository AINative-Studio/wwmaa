"""
Training Session Chat REST API Routes - US-050: Chat & Interaction Features

Provides REST API endpoints for training session chat as fallback to WebSocket.
Includes endpoints for:
- Sending messages
- Retrieving message history
- Managing reactions
- Raise/lower hand
- Chat moderation (delete, mute)
- Chat export
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel, Field

from backend.middleware.auth_middleware import get_current_user
from backend.services.session_chat_service import (
    SessionChatService,
    SessionChatError,
    RateLimitError,
    MutedUserError
)
from backend.services.zerodb_service import ZeroDBClient
from backend.models.schemas import UserRole, SessionChatMessage, ReactionType


# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/training/sessions", tags=["Training Chat"])


# Request/Response Models

class SendMessageRequest(BaseModel):
    """Request model for sending a chat message"""
    message: str = Field(..., min_length=1, max_length=2000, description="Message text")
    is_private: bool = Field(default=False, description="Whether this is a private message")
    recipient_id: Optional[str] = Field(None, description="Recipient user ID for private messages")


class AddReactionRequest(BaseModel):
    """Request model for adding a reaction"""
    message_id: str = Field(..., description="Message ID to react to")
    reaction: str = Field(..., description="Emoji reaction (👍, 👏, ❤️, 🔥)")


class MuteUserRequest(BaseModel):
    """Request model for muting a user"""
    user_id: str = Field(..., description="User ID to mute")
    duration_minutes: Optional[int] = Field(None, description="Mute duration in minutes (null for permanent)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for muting")


class MessageResponse(BaseModel):
    """Response model for a chat message"""
    id: str
    session_id: str
    user_id: str
    user_name: str
    message: str
    is_private: bool
    recipient_id: Optional[str]
    recipient_name: Optional[str]
    reactions: dict
    timestamp: datetime
    is_deleted: bool


class RaisedHandResponse(BaseModel):
    """Response model for a raised hand"""
    id: str
    session_id: str
    user_id: str
    user_name: str
    is_active: bool
    raised_at: datetime


# Helper functions

def get_chat_service() -> SessionChatService:
    """Get SessionChatService instance"""
    return SessionChatService()


def is_instructor(user: dict) -> bool:
    """Check if user is instructor"""
    return user.get("role") in [UserRole.INSTRUCTOR, UserRole.ADMIN, UserRole.BOARD_MEMBER]


def get_user_display_name(db: ZeroDBClient, user_id: str) -> str:
    """Get user display name from profile"""
    try:
        user = db.find_by_id("users", user_id)
        if not user:
            return "Unknown User"

        if user.get("profile_id"):
            profile = db.find_by_id("profiles", str(user["profile_id"]))
            if profile:
                display_name = profile.get("display_name")
                if display_name:
                    return display_name

                first_name = profile.get("first_name", "")
                last_name = profile.get("last_name", "")
                if first_name or last_name:
                    return f"{first_name} {last_name}".strip()

        return user.get("email", "Unknown User")

    except Exception as e:
        logger.error(f"Error getting user display name: {e}")
        return "Unknown User"


# Endpoints

@router.post(
    "/{session_id}/chat",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send chat message",
    description="Send a chat message in a training session (REST fallback for WebSocket)"
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Send a chat message in a training session

    This is a REST API fallback for WebSocket. For real-time chat,
    use the WebSocket endpoint at /ws/training/{session_id}/chat

    Args:
        session_id: Training session ID
        request: Message request
        current_user: Current authenticated user
        chat_service: Chat service instance

    Returns:
        Created message

    Raises:
        400: If user is muted or rate limit exceeded
        404: If session not found
        500: If message sending fails
    """
    try:
        user_id = current_user["id"]
        user_name = get_user_display_name(chat_service.db, user_id)
        is_instructor_user = is_instructor(current_user)

        # Get recipient name if private message
        recipient_name = None
        recipient_id = None
        if request.is_private and request.recipient_id:
            recipient_id = UUID(request.recipient_id)
            recipient_name = get_user_display_name(chat_service.db, request.recipient_id)

        # Send message
        message = chat_service.send_message(
            session_id=UUID(session_id),
            user_id=UUID(user_id),
            user_name=user_name,
            message=request.message,
            is_private=request.is_private,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            is_instructor=is_instructor_user
        )

        return MessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            user_id=str(message.user_id),
            user_name=message.user_name,
            message=message.message,
            is_private=message.is_private,
            recipient_id=str(message.recipient_id) if message.recipient_id else None,
            recipient_name=message.recipient_name,
            reactions=message.reactions,
            timestamp=message.timestamp,
            is_deleted=message.is_deleted
        )

    except MutedUserError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except SessionChatError as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.get(
    "/{session_id}/chat",
    response_model=list[MessageResponse],
    summary="Get chat messages",
    description="Get chat message history for a training session"
)
async def get_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Get chat message history for a training session

    Returns messages filtered based on user role:
    - Instructors see all messages (including private)
    - Participants see public messages and their private messages

    Args:
        session_id: Training session ID
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        current_user: Current authenticated user
        chat_service: Chat service instance

    Returns:
        List of messages

    Raises:
        404: If session not found
        500: If retrieval fails
    """
    try:
        user_id = current_user["id"]
        is_instructor_user = is_instructor(current_user)

        messages = chat_service.get_messages(
            session_id=UUID(session_id),
            user_id=UUID(user_id),
            is_instructor=is_instructor_user,
            limit=limit,
            offset=offset
        )

        return [
            MessageResponse(
                id=str(msg.id),
                session_id=str(msg.session_id),
                user_id=str(msg.user_id),
                user_name=msg.user_name,
                message=msg.message,
                is_private=msg.is_private,
                recipient_id=str(msg.recipient_id) if msg.recipient_id else None,
                recipient_name=msg.recipient_name,
                reactions=msg.reactions,
                timestamp=msg.timestamp,
                is_deleted=msg.is_deleted
            )
            for msg in messages
        ]

    except SessionChatError as e:
        logger.error(f"Error retrieving messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.delete(
    "/{session_id}/chat/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete chat message",
    description="Delete a chat message (instructor only)"
)
async def delete_message(
    session_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Delete a chat message (soft delete)

    Only instructors can delete messages.

    Args:
        session_id: Training session ID
        message_id: Message ID to delete
        current_user: Current authenticated user
        chat_service: Chat service instance

    Raises:
        403: If non-instructor tries to delete
        404: If message not found
        500: If deletion fails
    """
    try:
        is_instructor_user = is_instructor(current_user)

        chat_service.delete_message(
            message_id=UUID(message_id),
            deleted_by=UUID(current_user["id"]),
            is_instructor=is_instructor_user
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except SessionChatError as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.post(
    "/{session_id}/chat/mute",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mute user",
    description="Mute a user in a training session (instructor only)"
)
async def mute_user(
    session_id: str,
    request: MuteUserRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Mute a user in a training session

    Only instructors can mute users.

    Args:
        session_id: Training session ID
        request: Mute request
        current_user: Current authenticated user
        chat_service: Chat service instance

    Raises:
        403: If non-instructor tries to mute
        404: If user or session not found
        500: If mute fails
    """
    try:
        is_instructor_user = is_instructor(current_user)

        if not is_instructor_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can mute users"
            )

        chat_service.mute_user(
            session_id=UUID(session_id),
            user_id=UUID(request.user_id),
            muted_by=UUID(current_user["id"]),
            duration_minutes=request.duration_minutes,
            reason=request.reason
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except SessionChatError as e:
        logger.error(f"Error muting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mute user"
        )


@router.delete(
    "/{session_id}/chat/mute/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unmute user",
    description="Unmute a user in a training session (instructor only)"
)
async def unmute_user(
    session_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Unmute a user in a training session

    Only instructors can unmute users.

    Args:
        session_id: Training session ID
        user_id: User ID to unmute
        current_user: Current authenticated user
        chat_service: Chat service instance

    Raises:
        403: If non-instructor tries to unmute
        404: If user or session not found
        500: If unmute fails
    """
    try:
        is_instructor_user = is_instructor(current_user)

        if not is_instructor_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can unmute users"
            )

        chat_service.unmute_user(
            session_id=UUID(session_id),
            user_id=UUID(user_id)
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except SessionChatError as e:
        logger.error(f"Error unmuting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unmute user"
        )


@router.post(
    "/{session_id}/chat/reaction",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add reaction",
    description="Add an emoji reaction to a message"
)
async def add_reaction(
    session_id: str,
    request: AddReactionRequest,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Add an emoji reaction to a message

    Supported reactions: 👍, 👏, ❤️, 🔥

    Args:
        session_id: Training session ID
        request: Reaction request
        current_user: Current authenticated user
        chat_service: Chat service instance

    Raises:
        400: If invalid reaction or rate limit exceeded
        404: If message not found
        500: If adding reaction fails
    """
    try:
        is_instructor_user = is_instructor(current_user)

        chat_service.add_reaction(
            message_id=UUID(request.message_id),
            user_id=UUID(current_user["id"]),
            reaction=request.reaction,
            is_instructor=is_instructor_user
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except SessionChatError as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add reaction"
        )


@router.post(
    "/{session_id}/chat/raise-hand",
    response_model=RaisedHandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Raise hand",
    description="Raise hand in a training session"
)
async def raise_hand(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Raise hand in a training session

    Notifies the instructor that you have a question or need attention.

    Args:
        session_id: Training session ID
        current_user: Current authenticated user
        chat_service: Chat service instance

    Returns:
        Raised hand record

    Raises:
        404: If session not found
        500: If raise hand fails
    """
    try:
        user_id = current_user["id"]
        user_name = get_user_display_name(chat_service.db, user_id)

        raised_hand = chat_service.raise_hand(
            session_id=UUID(session_id),
            user_id=UUID(user_id),
            user_name=user_name
        )

        return RaisedHandResponse(
            id=str(raised_hand.id),
            session_id=str(raised_hand.session_id),
            user_id=str(raised_hand.user_id),
            user_name=raised_hand.user_name,
            is_active=raised_hand.is_active,
            raised_at=raised_hand.raised_at
        )

    except SessionChatError as e:
        logger.error(f"Error raising hand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to raise hand"
        )


@router.delete(
    "/{session_id}/chat/raise-hand",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Lower hand",
    description="Lower raised hand in a training session"
)
async def lower_hand(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Lower raised hand in a training session

    Args:
        session_id: Training session ID
        current_user: Current authenticated user
        chat_service: Chat service instance

    Raises:
        404: If session not found
        500: If lower hand fails
    """
    try:
        chat_service.lower_hand(
            session_id=UUID(session_id),
            user_id=UUID(current_user["id"])
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except SessionChatError as e:
        logger.error(f"Error lowering hand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lower hand"
        )


@router.get(
    "/{session_id}/chat/raise-hand",
    response_model=list[RaisedHandResponse],
    summary="Get raised hands",
    description="Get all active raised hands in a training session"
)
async def get_raised_hands(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Get all active raised hands in a training session

    Typically used by instructors to see who needs attention.

    Args:
        session_id: Training session ID
        current_user: Current authenticated user
        chat_service: Chat service instance

    Returns:
        List of raised hands

    Raises:
        404: If session not found
        500: If retrieval fails
    """
    try:
        hands = chat_service.get_raised_hands(
            session_id=UUID(session_id)
        )

        return [
            RaisedHandResponse(
                id=str(hand.id),
                session_id=str(hand.session_id),
                user_id=str(hand.user_id),
                user_name=hand.user_name,
                is_active=hand.is_active,
                raised_at=hand.raised_at
            )
            for hand in hands
        ]

    except SessionChatError as e:
        logger.error(f"Error retrieving raised hands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve raised hands"
        )


@router.get(
    "/{session_id}/chat/export",
    summary="Export chat",
    description="Export chat messages as JSON, CSV, or plain text (instructor only)"
)
async def export_chat(
    session_id: str,
    format: str = Query("json", regex="^(json|csv|txt)$", description="Export format"),
    include_private: bool = Query(False, description="Include private messages"),
    current_user: dict = Depends(get_current_user),
    chat_service: SessionChatService = Depends(get_chat_service)
):
    """
    Export chat messages as JSON, CSV, or plain text

    Only instructors can export chat.

    Args:
        session_id: Training session ID
        format: Export format (json, csv, txt)
        include_private: Whether to include private messages
        current_user: Current authenticated user
        chat_service: Chat service instance

    Returns:
        Exported chat data

    Raises:
        403: If non-instructor tries to export
        404: If session not found
        500: If export fails
    """
    try:
        is_instructor_user = is_instructor(current_user)

        if not is_instructor_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can export chat"
            )

        export_data = chat_service.export_chat(
            session_id=UUID(session_id),
            format=format,
            include_private=include_private
        )

        # Set appropriate content type
        if format == "json":
            media_type = "application/json"
            filename = f"chat_{session_id}.json"
        elif format == "csv":
            media_type = "text/csv"
            filename = f"chat_{session_id}.csv"
        else:  # txt
            media_type = "text/plain"
            filename = f"chat_{session_id}.txt"

        return Response(
            content=export_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except SessionChatError as e:
        logger.error(f"Error exporting chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export chat"
        )
