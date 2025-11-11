"""
WebSocket Server for Session Chat - US-050: Chat & Interaction Features

Provides real-time WebSocket communication for training session chat including:
- Real-time message delivery
- Emoji reactions
- Raise/lower hand notifications
- Typing indicators
- Private messages
- Moderation actions (message deletion, user muting)
- Connection management
"""

import json
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException, status
from jose import jwt, JWTError

from backend.config import settings
from backend.services.session_chat_service import SessionChatService, SessionChatError, RateLimitError, MutedUserError
from backend.services.zerodb_service import ZeroDBClient
from backend.models.schemas import UserRole


# Configure logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for session chat

    Tracks active connections per session and handles broadcasting
    messages to all connected clients.
    """

    def __init__(self):
        # session_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_info dict
        self.connection_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_info: dict):
        """
        Connect a WebSocket client to a session

        Args:
            websocket: WebSocket connection
            session_id: Training session ID
            user_info: User information dict (user_id, user_name, role)
        """
        await websocket.accept()

        # Add to active connections
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)
        self.connection_info[websocket] = user_info

        logger.info(
            f"User {user_info['user_id']} ({user_info['user_name']}) "
            f"connected to session {session_id}"
        )

    def disconnect(self, websocket: WebSocket, session_id: str):
        """
        Disconnect a WebSocket client from a session

        Args:
            websocket: WebSocket connection
            session_id: Training session ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        # Remove connection info
        user_info = self.connection_info.pop(websocket, None)

        if user_info:
            logger.info(
                f"User {user_info['user_id']} ({user_info['user_name']}) "
                f"disconnected from session {session_id}"
            )

    async def broadcast(self, session_id: str, message: dict, exclude: Set[WebSocket] = None):
        """
        Broadcast a message to all connected clients in a session

        Args:
            session_id: Training session ID
            message: Message dict to broadcast
            exclude: Set of websockets to exclude from broadcast
        """
        if session_id not in self.active_connections:
            return

        exclude = exclude or set()
        disconnected = set()

        for websocket in self.active_connections[session_id]:
            if websocket in exclude:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket, session_id)

    async def send_private(self, session_id: str, recipient_id: str, message: dict):
        """
        Send a private message to a specific user

        Args:
            session_id: Training session ID
            recipient_id: Recipient user ID
            message: Message dict to send
        """
        if session_id not in self.active_connections:
            return

        for websocket in self.active_connections[session_id]:
            user_info = self.connection_info.get(websocket)
            if user_info and str(user_info['user_id']) == str(recipient_id):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending private message: {e}")

    def get_active_users(self, session_id: str) -> list:
        """
        Get list of active users in a session

        Args:
            session_id: Training session ID

        Returns:
            List of user info dicts
        """
        if session_id not in self.active_connections:
            return []

        users = []
        for websocket in self.active_connections[session_id]:
            user_info = self.connection_info.get(websocket)
            if user_info:
                users.append({
                    "user_id": str(user_info['user_id']),
                    "user_name": user_info['user_name'],
                    "role": user_info['role']
                })

        return users


# Global connection manager
manager = ConnectionManager()


def verify_token(token: str) -> dict:
    """
    Verify JWT token and extract user information

    Args:
        token: JWT token string

    Returns:
        User info dict with user_id, role, email

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )

        return {
            "user_id": user_id,
            "role": payload.get("role", "public"),
            "email": payload.get("email", "")
        }

    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for session chat

    Path: /ws/training/{session_id}/chat?token=<jwt_token>

    Message Types (Client -> Server):
    - chat_message: Send a chat message
    - reaction_added: Add emoji reaction
    - hand_raised: Raise hand
    - hand_lowered: Lower hand
    - typing_start: Start typing
    - typing_stop: Stop typing
    - delete_message: Delete message (instructor only)
    - mute_user: Mute user (instructor only)
    - unmute_user: Unmute user (instructor only)

    Message Types (Server -> Client):
    - chat_message: New message broadcast
    - message_deleted: Message deleted notification
    - user_muted: User muted notification
    - user_unmuted: User unmuted notification
    - reaction_added: Reaction added notification
    - hand_raised: Hand raised notification
    - hand_lowered: Hand lowered notification
    - typing_start: User started typing
    - typing_stop: User stopped typing
    - private_message: Direct message to user
    - error: Error notification
    - user_joined: User joined session
    - user_left: User left session

    Args:
        websocket: WebSocket connection
        session_id: Training session ID
        token: JWT authentication token
    """
    # Verify authentication
    try:
        user_auth = verify_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get user profile for display name
    db = ZeroDBClient()
    try:
        user = db.find_by_id("users", user_auth["user_id"])
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get profile for display name
        profile = None
        if user.get("profile_id"):
            profile = db.find_by_id("profiles", str(user["profile_id"]))

        user_name = "Unknown User"
        if profile:
            user_name = profile.get("display_name") or f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

        if not user_name or user_name == "Unknown User":
            user_name = user.get("email", "Unknown User")

    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    # User info for connection tracking
    user_info = {
        "user_id": user_auth["user_id"],
        "user_name": user_name,
        "role": user_auth["role"]
    }

    is_instructor = user_auth["role"] in [UserRole.INSTRUCTOR, UserRole.ADMIN, UserRole.BOARD_MEMBER]

    # Initialize chat service
    chat_service = SessionChatService(db)

    # Connect to session
    await manager.connect(websocket, session_id, user_info)

    # Broadcast user joined
    await manager.broadcast(
        session_id,
        {
            "type": "user_joined",
            "user_id": str(user_info["user_id"]),
            "user_name": user_info["user_name"],
            "timestamp": str(datetime.utcnow())
        },
        exclude={websocket}
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")

            if not message_type:
                await websocket.send_json({
                    "type": "error",
                    "error": "Missing message type"
                })
                continue

            # Handle different message types
            if message_type == "chat_message":
                await handle_chat_message(
                    websocket, session_id, user_info, data,
                    chat_service, is_instructor
                )

            elif message_type == "reaction_added":
                await handle_reaction_added(
                    websocket, session_id, user_info, data,
                    chat_service, is_instructor
                )

            elif message_type == "hand_raised":
                await handle_hand_raised(
                    websocket, session_id, user_info, data,
                    chat_service
                )

            elif message_type == "hand_lowered":
                await handle_hand_lowered(
                    websocket, session_id, user_info, data,
                    chat_service
                )

            elif message_type == "typing_start":
                await handle_typing_start(
                    websocket, session_id, user_info, data,
                    chat_service
                )

            elif message_type == "typing_stop":
                await handle_typing_stop(
                    websocket, session_id, user_info, data,
                    chat_service
                )

            elif message_type == "delete_message":
                await handle_delete_message(
                    websocket, session_id, user_info, data,
                    chat_service, is_instructor
                )

            elif message_type == "mute_user":
                await handle_mute_user(
                    websocket, session_id, user_info, data,
                    chat_service, is_instructor
                )

            elif message_type == "unmute_user":
                await handle_unmute_user(
                    websocket, session_id, user_info, data,
                    chat_service, is_instructor
                )

            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

        # Broadcast user left
        await manager.broadcast(
            session_id,
            {
                "type": "user_left",
                "user_id": str(user_info["user_id"]),
                "user_name": user_info["user_name"],
                "timestamp": str(datetime.utcnow())
            }
        )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)


# Message handlers

async def handle_chat_message(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService,
    is_instructor: bool
):
    """Handle chat message"""
    from datetime import datetime

    try:
        message_text = data.get("message", "").strip()
        is_private = data.get("is_private", False)
        recipient_id = data.get("recipient_id")

        if not message_text:
            await websocket.send_json({
                "type": "error",
                "error": "Message cannot be empty"
            })
            return

        # Get recipient name if private message
        recipient_name = None
        if is_private and recipient_id:
            recipient_user = chat_service.db.find_by_id("users", recipient_id)
            if recipient_user and recipient_user.get("profile_id"):
                recipient_profile = chat_service.db.find_by_id("profiles", str(recipient_user["profile_id"]))
                if recipient_profile:
                    recipient_name = recipient_profile.get("display_name") or f"{recipient_profile.get('first_name', '')} {recipient_profile.get('last_name', '')}".strip()

        # Send message via service
        message = chat_service.send_message(
            session_id=UUID(session_id),
            user_id=UUID(user_info["user_id"]),
            user_name=user_info["user_name"],
            message=message_text,
            is_private=is_private,
            recipient_id=UUID(recipient_id) if recipient_id else None,
            recipient_name=recipient_name,
            is_instructor=is_instructor
        )

        # Broadcast to appropriate recipients
        message_data = {
            "type": "chat_message",
            "id": str(message.id),
            "user_id": str(message.user_id),
            "user_name": message.user_name,
            "message": message.message,
            "timestamp": message.timestamp.isoformat(),
            "is_private": message.is_private,
            "recipient_id": str(message.recipient_id) if message.recipient_id else None,
            "recipient_name": message.recipient_name,
            "reactions": message.reactions
        }

        if is_private and recipient_id:
            # Send to sender
            await websocket.send_json(message_data)
            # Send to recipient
            await manager.send_private(session_id, recipient_id, message_data)
        else:
            # Broadcast to all
            await manager.broadcast(session_id, message_data)

    except MutedUserError as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    except RateLimitError as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to send message"
        })


async def handle_reaction_added(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService,
    is_instructor: bool
):
    """Handle reaction added"""
    try:
        message_id = data.get("message_id")
        reaction = data.get("reaction")

        if not message_id or not reaction:
            await websocket.send_json({
                "type": "error",
                "error": "Missing message_id or reaction"
            })
            return

        # Add reaction via service
        chat_service.add_reaction(
            message_id=UUID(message_id),
            user_id=UUID(user_info["user_id"]),
            reaction=reaction,
            is_instructor=is_instructor
        )

        # Broadcast reaction
        await manager.broadcast(
            session_id,
            {
                "type": "reaction_added",
                "message_id": message_id,
                "reaction": reaction,
                "user_id": str(user_info["user_id"])
            }
        )

    except RateLimitError as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Error handling reaction: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to add reaction"
        })


async def handle_hand_raised(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService
):
    """Handle raise hand"""
    try:
        # Raise hand via service
        raised_hand = chat_service.raise_hand(
            session_id=UUID(session_id),
            user_id=UUID(user_info["user_id"]),
            user_name=user_info["user_name"]
        )

        # Broadcast to all (especially instructor)
        await manager.broadcast(
            session_id,
            {
                "type": "hand_raised",
                "user_id": str(raised_hand.user_id),
                "user_name": raised_hand.user_name,
                "raised_at": raised_hand.raised_at.isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Error raising hand: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to raise hand"
        })


async def handle_hand_lowered(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService
):
    """Handle lower hand"""
    try:
        acknowledged_by = data.get("acknowledged_by")

        # Lower hand via service
        chat_service.lower_hand(
            session_id=UUID(session_id),
            user_id=UUID(user_info["user_id"]),
            acknowledged_by=UUID(acknowledged_by) if acknowledged_by else None
        )

        # Broadcast to all
        await manager.broadcast(
            session_id,
            {
                "type": "hand_lowered",
                "user_id": str(user_info["user_id"]),
                "user_name": user_info["user_name"],
                "acknowledged_by": acknowledged_by
            }
        )

    except Exception as e:
        logger.error(f"Error lowering hand: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to lower hand"
        })


async def handle_typing_start(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService
):
    """Handle typing start"""
    try:
        # Set typing indicator
        chat_service.set_typing(
            session_id=UUID(session_id),
            user_id=UUID(user_info["user_id"]),
            user_name=user_info["user_name"],
            is_typing=True
        )

        # Broadcast to others (exclude sender)
        await manager.broadcast(
            session_id,
            {
                "type": "typing_start",
                "user_id": str(user_info["user_id"]),
                "user_name": user_info["user_name"]
            },
            exclude={websocket}
        )

    except Exception as e:
        logger.error(f"Error handling typing start: {e}")


async def handle_typing_stop(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService
):
    """Handle typing stop"""
    try:
        # Remove typing indicator
        chat_service.set_typing(
            session_id=UUID(session_id),
            user_id=UUID(user_info["user_id"]),
            user_name=user_info["user_name"],
            is_typing=False
        )

        # Broadcast to others (exclude sender)
        await manager.broadcast(
            session_id,
            {
                "type": "typing_stop",
                "user_id": str(user_info["user_id"]),
                "user_name": user_info["user_name"]
            },
            exclude={websocket}
        )

    except Exception as e:
        logger.error(f"Error handling typing stop: {e}")


async def handle_delete_message(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService,
    is_instructor: bool
):
    """Handle delete message (instructor only)"""
    try:
        message_id = data.get("message_id")

        if not message_id:
            await websocket.send_json({
                "type": "error",
                "error": "Missing message_id"
            })
            return

        # Delete message via service
        chat_service.delete_message(
            message_id=UUID(message_id),
            deleted_by=UUID(user_info["user_id"]),
            is_instructor=is_instructor
        )

        # Broadcast deletion
        await manager.broadcast(
            session_id,
            {
                "type": "message_deleted",
                "message_id": message_id,
                "deleted_by": str(user_info["user_id"])
            }
        )

    except PermissionError as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to delete message"
        })


async def handle_mute_user(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService,
    is_instructor: bool
):
    """Handle mute user (instructor only)"""
    if not is_instructor:
        await websocket.send_json({
            "type": "error",
            "error": "Only instructors can mute users"
        })
        return

    try:
        target_user_id = data.get("user_id")
        duration_minutes = data.get("duration_minutes")
        reason = data.get("reason")

        if not target_user_id:
            await websocket.send_json({
                "type": "error",
                "error": "Missing user_id"
            })
            return

        # Mute user via service
        chat_service.mute_user(
            session_id=UUID(session_id),
            user_id=UUID(target_user_id),
            muted_by=UUID(user_info["user_id"]),
            duration_minutes=duration_minutes,
            reason=reason
        )

        # Broadcast mute notification
        await manager.broadcast(
            session_id,
            {
                "type": "user_muted",
                "user_id": target_user_id,
                "muted_by": str(user_info["user_id"]),
                "duration_minutes": duration_minutes,
                "reason": reason
            }
        )

    except Exception as e:
        logger.error(f"Error muting user: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to mute user"
        })


async def handle_unmute_user(
    websocket: WebSocket,
    session_id: str,
    user_info: dict,
    data: dict,
    chat_service: SessionChatService,
    is_instructor: bool
):
    """Handle unmute user (instructor only)"""
    if not is_instructor:
        await websocket.send_json({
            "type": "error",
            "error": "Only instructors can unmute users"
        })
        return

    try:
        target_user_id = data.get("user_id")

        if not target_user_id:
            await websocket.send_json({
                "type": "error",
                "error": "Missing user_id"
            })
            return

        # Unmute user via service
        chat_service.unmute_user(
            session_id=UUID(session_id),
            user_id=UUID(target_user_id)
        )

        # Broadcast unmute notification
        await manager.broadcast(
            session_id,
            {
                "type": "user_unmuted",
                "user_id": target_user_id,
                "unmuted_by": str(user_info["user_id"])
            }
        )

    except Exception as e:
        logger.error(f"Error unmuting user: {e}")
        await websocket.send_json({
            "type": "error",
            "error": "Failed to unmute user"
        })
