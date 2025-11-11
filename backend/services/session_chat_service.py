"""
Session Chat Service - US-050: Chat & Interaction Features

Provides chat functionality for live training sessions including:
- Real-time messaging with WebSocket support
- Emoji reactions
- Raise hand feature
- Private messaging (instructor to participant)
- Chat moderation (delete messages, mute users)
- Profanity filtering
- Rate limiting
- Chat export
- Typing indicators
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

import redis
from better_profanity import profanity

from backend.config import settings
from backend.models.schemas import (
    SessionChatMessage,
    SessionMute,
    SessionRaisedHand,
    ReactionType,
    UserRole
)
from backend.services.zerodb_service import ZeroDBClient, ZeroDBError


# Configure logging
logger = logging.getLogger(__name__)

# Initialize profanity filter
profanity.load_censor_words()


class SessionChatError(Exception):
    """Base exception for session chat operations"""
    pass


class RateLimitError(SessionChatError):
    """Exception raised when rate limit is exceeded"""
    pass


class MutedUserError(SessionChatError):
    """Exception raised when muted user tries to send message"""
    pass


class SessionChatService:
    """
    Service for managing training session chat and interactions

    Provides methods for:
    - Sending and retrieving messages
    - Managing reactions
    - Handling raise hand feature
    - Chat moderation (mute/delete)
    - Profanity filtering
    - Rate limiting
    - Chat export
    """

    def __init__(self, db_client: Optional[ZeroDBClient] = None):
        """
        Initialize SessionChatService

        Args:
            db_client: ZeroDB client instance (creates new if not provided)
        """
        self.db = db_client or ZeroDBClient()
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        # Rate limiting configuration
        self.message_rate_limit = 5  # messages
        self.message_rate_window = 10  # seconds
        self.reaction_rate_limit = 10  # reactions
        self.reaction_rate_window = 60  # seconds

        # Profanity filter configuration
        self.profanity_strikes_threshold = 3  # auto-mute after 3 strikes

    def _check_rate_limit(
        self,
        user_id: UUID,
        action_type: str = "message",
        is_instructor: bool = False
    ) -> bool:
        """
        Check if user has exceeded rate limit

        Args:
            user_id: User ID to check
            action_type: Type of action ('message' or 'reaction')
            is_instructor: Whether user is instructor (bypass rate limit)

        Returns:
            True if within rate limit, False if exceeded

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        # Instructors bypass rate limits
        if is_instructor:
            return True

        # Determine rate limit parameters
        if action_type == "message":
            limit = self.message_rate_limit
            window = self.message_rate_window
        else:  # reaction
            limit = self.reaction_rate_limit
            window = self.reaction_rate_window

        # Redis key for rate limiting
        redis_key = f"rate_limit:{action_type}:{user_id}"

        try:
            # Get current count
            current_count = self.redis_client.get(redis_key)

            if current_count is None:
                # First action in window
                self.redis_client.setex(redis_key, window, 1)
                return True
            else:
                current_count = int(current_count)
                if current_count >= limit:
                    raise RateLimitError(
                        f"Rate limit exceeded: {limit} {action_type}s per {window} seconds"
                    )
                else:
                    # Increment counter
                    self.redis_client.incr(redis_key)
                    return True

        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Allow action if Redis is down (fail open)
            return True

    def _check_if_muted(self, session_id: UUID, user_id: UUID) -> Optional[SessionMute]:
        """
        Check if user is currently muted in session

        Args:
            session_id: Training session ID
            user_id: User ID to check

        Returns:
            SessionMute object if user is muted, None otherwise
        """
        try:
            # Query active mutes for this user in this session
            query = {
                "session_id": str(session_id),
                "user_id": str(user_id),
                "is_active": True
            }

            mutes = self.db.find("session_mutes", query, limit=1)

            if not mutes:
                return None

            mute = SessionMute(**mutes[0])

            # Check if mute has expired
            if mute.muted_until:
                if datetime.utcnow() > mute.muted_until:
                    # Mute has expired, deactivate it
                    self.unmute_user(session_id, user_id)
                    return None

            return mute

        except ZeroDBError as e:
            logger.error(f"Error checking mute status: {e}")
            return None

    def _filter_profanity(self, message: str, user_id: UUID, session_id: UUID) -> str:
        """
        Filter profanity from message and track violations

        Args:
            message: Message text to filter
            user_id: User ID
            session_id: Session ID

        Returns:
            Filtered message text
        """
        if profanity.contains_profanity(message):
            # Increment strike counter
            redis_key = f"profanity_strikes:{session_id}:{user_id}"
            strikes = self.redis_client.incr(redis_key)
            self.redis_client.expire(redis_key, 3600)  # Expire after 1 hour

            # Log violation
            logger.warning(
                f"Profanity detected for user {user_id} in session {session_id}. "
                f"Strike {strikes}/{self.profanity_strikes_threshold}"
            )

            # Auto-mute after threshold
            if strikes >= self.profanity_strikes_threshold:
                logger.warning(f"Auto-muting user {user_id} after {strikes} profanity strikes")
                # Mute for 15 minutes
                self.mute_user(
                    session_id=session_id,
                    user_id=user_id,
                    muted_by=user_id,  # System mute
                    duration_minutes=15,
                    reason="Automatic mute: repeated profanity violations"
                )

            # Censor the message
            return profanity.censor(message)

        return message

    def send_message(
        self,
        session_id: UUID,
        user_id: UUID,
        user_name: str,
        message: str,
        is_private: bool = False,
        recipient_id: Optional[UUID] = None,
        recipient_name: Optional[str] = None,
        is_instructor: bool = False
    ) -> SessionChatMessage:
        """
        Send a chat message in a training session

        Args:
            session_id: Training session ID
            user_id: Sender user ID
            user_name: Sender display name
            message: Message text
            is_private: Whether this is a private message
            recipient_id: Recipient user ID (for private messages)
            recipient_name: Recipient display name
            is_instructor: Whether sender is instructor

        Returns:
            Created SessionChatMessage object

        Raises:
            RateLimitError: If rate limit is exceeded
            MutedUserError: If user is muted
            SessionChatError: If message sending fails
        """
        try:
            # Check if user is muted
            mute = self._check_if_muted(session_id, user_id)
            if mute:
                raise MutedUserError(
                    f"User is muted until {mute.muted_until or 'permanently'}. "
                    f"Reason: {mute.reason or 'No reason provided'}"
                )

            # Check rate limit
            self._check_rate_limit(user_id, "message", is_instructor)

            # Filter profanity
            filtered_message = self._filter_profanity(message, user_id, session_id)

            # Create message object
            chat_message = SessionChatMessage(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                message=filtered_message,
                is_private=is_private,
                recipient_id=recipient_id,
                recipient_name=recipient_name,
                reactions={},
                timestamp=datetime.utcnow()
            )

            # Store in database
            message_data = chat_message.model_dump(mode='json')
            result = self.db.insert_one("session_chat_messages", message_data)

            logger.info(
                f"Message sent in session {session_id} by user {user_id}. "
                f"Private: {is_private}"
            )

            return chat_message

        except (RateLimitError, MutedUserError):
            raise
        except ZeroDBError as e:
            logger.error(f"Error sending message: {e}")
            raise SessionChatError(f"Failed to send message: {e}")

    def get_messages(
        self,
        session_id: UUID,
        user_id: UUID,
        is_instructor: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionChatMessage]:
        """
        Get chat messages for a session

        Args:
            session_id: Training session ID
            user_id: Current user ID (for filtering private messages)
            is_instructor: Whether user is instructor (sees all messages)
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of SessionChatMessage objects
        """
        try:
            # Build query
            query: Dict[str, Any] = {
                "session_id": str(session_id),
                "is_deleted": False
            }

            # Filter private messages
            if not is_instructor:
                # Non-instructors see:
                # 1. All public messages
                # 2. Private messages where they are sender or recipient
                query["$or"] = [
                    {"is_private": False},
                    {"is_private": True, "user_id": str(user_id)},
                    {"is_private": True, "recipient_id": str(user_id)}
                ]

            # Query database
            messages_data = self.db.find(
                "session_chat_messages",
                query,
                limit=limit,
                skip=offset,
                sort={"timestamp": 1}  # Oldest first
            )

            messages = [SessionChatMessage(**msg) for msg in messages_data]

            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")

            return messages

        except ZeroDBError as e:
            logger.error(f"Error retrieving messages: {e}")
            raise SessionChatError(f"Failed to retrieve messages: {e}")

    def delete_message(
        self,
        message_id: UUID,
        deleted_by: UUID,
        is_instructor: bool = False
    ) -> bool:
        """
        Delete a chat message (soft delete)

        Args:
            message_id: Message ID to delete
            deleted_by: User ID performing deletion
            is_instructor: Whether user is instructor (only instructors can delete)

        Returns:
            True if successful

        Raises:
            PermissionError: If non-instructor tries to delete
            SessionChatError: If deletion fails
        """
        if not is_instructor:
            raise PermissionError("Only instructors can delete messages")

        try:
            # Update message
            update_data = {
                "is_deleted": True,
                "deleted_at": datetime.utcnow().isoformat(),
                "deleted_by": str(deleted_by)
            }

            self.db.update_one("session_chat_messages", str(message_id), update_data)

            logger.info(f"Message {message_id} deleted by user {deleted_by}")

            return True

        except ZeroDBError as e:
            logger.error(f"Error deleting message: {e}")
            raise SessionChatError(f"Failed to delete message: {e}")

    def mute_user(
        self,
        session_id: UUID,
        user_id: UUID,
        muted_by: UUID,
        duration_minutes: Optional[int] = None,
        reason: Optional[str] = None
    ) -> SessionMute:
        """
        Mute a user in a session

        Args:
            session_id: Training session ID
            user_id: User ID to mute
            muted_by: User ID performing mute (instructor)
            duration_minutes: Mute duration (None for permanent)
            reason: Reason for muting

        Returns:
            Created SessionMute object

        Raises:
            SessionChatError: If mute fails
        """
        try:
            # Calculate mute expiration
            muted_until = None
            if duration_minutes:
                muted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

            # Create mute record
            mute = SessionMute(
                session_id=session_id,
                user_id=user_id,
                muted_by=muted_by,
                muted_until=muted_until,
                reason=reason,
                is_active=True
            )

            # Store in database
            mute_data = mute.model_dump(mode='json')
            self.db.insert_one("session_mutes", mute_data)

            logger.info(
                f"User {user_id} muted in session {session_id} by {muted_by}. "
                f"Duration: {duration_minutes or 'permanent'} minutes"
            )

            return mute

        except ZeroDBError as e:
            logger.error(f"Error muting user: {e}")
            raise SessionChatError(f"Failed to mute user: {e}")

    def unmute_user(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Unmute a user in a session

        Args:
            session_id: Training session ID
            user_id: User ID to unmute

        Returns:
            True if successful

        Raises:
            SessionChatError: If unmute fails
        """
        try:
            # Find active mutes for this user
            query = {
                "session_id": str(session_id),
                "user_id": str(user_id),
                "is_active": True
            }

            mutes = self.db.find("session_mutes", query)

            # Deactivate all active mutes
            for mute_data in mutes:
                update_data = {
                    "is_active": False,
                    "unmuted_at": datetime.utcnow().isoformat()
                }
                self.db.update_one("session_mutes", mute_data["id"], update_data)

            logger.info(f"User {user_id} unmuted in session {session_id}")

            return True

        except ZeroDBError as e:
            logger.error(f"Error unmuting user: {e}")
            raise SessionChatError(f"Failed to unmute user: {e}")

    def add_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        reaction: str,
        is_instructor: bool = False
    ) -> bool:
        """
        Add emoji reaction to a message

        Args:
            message_id: Message ID
            user_id: User ID adding reaction
            reaction: Emoji reaction (must be valid ReactionType)
            is_instructor: Whether user is instructor

        Returns:
            True if successful

        Raises:
            ValueError: If invalid reaction type
            RateLimitError: If rate limit exceeded
            SessionChatError: If adding reaction fails
        """
        # Validate reaction type
        valid_reactions = [r.value for r in ReactionType]
        if reaction not in valid_reactions:
            raise ValueError(f"Invalid reaction. Must be one of: {valid_reactions}")

        try:
            # Check rate limit
            self._check_rate_limit(user_id, "reaction", is_instructor)

            # Get current message
            message_data = self.db.find_by_id("session_chat_messages", str(message_id))
            if not message_data:
                raise SessionChatError("Message not found")

            message = SessionChatMessage(**message_data)

            # Update reactions
            reactions = message.reactions or {}
            reactions[reaction] = reactions.get(reaction, 0) + 1

            # Update in database
            update_data = {"reactions": reactions}
            self.db.update_one("session_chat_messages", str(message_id), update_data)

            logger.info(f"Reaction {reaction} added to message {message_id} by user {user_id}")

            return True

        except RateLimitError:
            raise
        except ZeroDBError as e:
            logger.error(f"Error adding reaction: {e}")
            raise SessionChatError(f"Failed to add reaction: {e}")

    def raise_hand(
        self,
        session_id: UUID,
        user_id: UUID,
        user_name: str
    ) -> SessionRaisedHand:
        """
        Raise hand in a session

        Args:
            session_id: Training session ID
            user_id: User ID raising hand
            user_name: User display name

        Returns:
            Created SessionRaisedHand object

        Raises:
            SessionChatError: If raise hand fails
        """
        try:
            # Check if hand is already raised
            query = {
                "session_id": str(session_id),
                "user_id": str(user_id),
                "is_active": True
            }

            existing = self.db.find("session_raised_hands", query, limit=1)

            if existing:
                # Hand already raised
                return SessionRaisedHand(**existing[0])

            # Create raised hand record
            raised_hand = SessionRaisedHand(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name,
                is_active=True
            )

            # Store in database
            hand_data = raised_hand.model_dump(mode='json')
            self.db.insert_one("session_raised_hands", hand_data)

            logger.info(f"User {user_id} raised hand in session {session_id}")

            return raised_hand

        except ZeroDBError as e:
            logger.error(f"Error raising hand: {e}")
            raise SessionChatError(f"Failed to raise hand: {e}")

    def lower_hand(
        self,
        session_id: UUID,
        user_id: UUID,
        acknowledged_by: Optional[UUID] = None
    ) -> bool:
        """
        Lower raised hand in a session

        Args:
            session_id: Training session ID
            user_id: User ID lowering hand
            acknowledged_by: Instructor ID who acknowledged (optional)

        Returns:
            True if successful

        Raises:
            SessionChatError: If lower hand fails
        """
        try:
            # Find active raised hands for this user
            query = {
                "session_id": str(session_id),
                "user_id": str(user_id),
                "is_active": True
            }

            hands = self.db.find("session_raised_hands", query)

            # Deactivate all active raised hands
            for hand_data in hands:
                update_data = {
                    "is_active": False,
                    "lowered_at": datetime.utcnow().isoformat()
                }
                if acknowledged_by:
                    update_data["acknowledged_by"] = str(acknowledged_by)

                self.db.update_one("session_raised_hands", hand_data["id"], update_data)

            logger.info(f"User {user_id} lowered hand in session {session_id}")

            return True

        except ZeroDBError as e:
            logger.error(f"Error lowering hand: {e}")
            raise SessionChatError(f"Failed to lower hand: {e}")

    def get_raised_hands(
        self,
        session_id: UUID
    ) -> List[SessionRaisedHand]:
        """
        Get all active raised hands in a session

        Args:
            session_id: Training session ID

        Returns:
            List of SessionRaisedHand objects
        """
        try:
            query = {
                "session_id": str(session_id),
                "is_active": True
            }

            hands_data = self.db.find(
                "session_raised_hands",
                query,
                sort={"raised_at": 1}  # Oldest first
            )

            hands = [SessionRaisedHand(**hand) for hand in hands_data]

            return hands

        except ZeroDBError as e:
            logger.error(f"Error retrieving raised hands: {e}")
            raise SessionChatError(f"Failed to retrieve raised hands: {e}")

    def set_typing(
        self,
        session_id: UUID,
        user_id: UUID,
        user_name: str,
        is_typing: bool
    ) -> bool:
        """
        Set typing indicator for a user

        Args:
            session_id: Training session ID
            user_id: User ID
            user_name: User display name
            is_typing: Whether user is typing

        Returns:
            True if successful
        """
        try:
            redis_key = f"typing:{session_id}:{user_id}"

            if is_typing:
                # Set typing indicator with 5 second expiration
                typing_data = json.dumps({
                    "user_id": str(user_id),
                    "user_name": user_name,
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.redis_client.setex(redis_key, 5, typing_data)
            else:
                # Remove typing indicator
                self.redis_client.delete(redis_key)

            return True

        except redis.RedisError as e:
            logger.error(f"Error setting typing indicator: {e}")
            # Non-critical error, return True
            return True

    def get_typing_users(
        self,
        session_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all users currently typing in a session

        Args:
            session_id: Training session ID

        Returns:
            List of typing user info dicts
        """
        try:
            pattern = f"typing:{session_id}:*"
            keys = self.redis_client.keys(pattern)

            typing_users = []
            for key in keys:
                typing_data = self.redis_client.get(key)
                if typing_data:
                    typing_users.append(json.loads(typing_data))

            return typing_users

        except redis.RedisError as e:
            logger.error(f"Error retrieving typing users: {e}")
            return []

    def export_chat(
        self,
        session_id: UUID,
        format: str = "json",
        include_private: bool = False
    ) -> str:
        """
        Export chat messages to JSON or CSV

        Args:
            session_id: Training session ID
            format: Export format ('json' or 'csv')
            include_private: Whether to include private messages

        Returns:
            Exported data as string

        Raises:
            ValueError: If invalid format
            SessionChatError: If export fails
        """
        if format not in ["json", "csv", "txt"]:
            raise ValueError("Format must be 'json', 'csv', or 'txt'")

        try:
            # Build query
            query: Dict[str, Any] = {
                "session_id": str(session_id),
                "is_deleted": False
            }

            if not include_private:
                query["is_private"] = False

            # Get all messages
            messages_data = self.db.find(
                "session_chat_messages",
                query,
                sort={"timestamp": 1}
            )

            if format == "json":
                return json.dumps(messages_data, indent=2, default=str)

            elif format == "csv":
                output = io.StringIO()
                if messages_data:
                    fieldnames = ["timestamp", "user_name", "message", "is_private", "reactions"]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()

                    for msg in messages_data:
                        writer.writerow({
                            "timestamp": msg.get("timestamp", ""),
                            "user_name": msg.get("user_name", ""),
                            "message": msg.get("message", ""),
                            "is_private": msg.get("is_private", False),
                            "reactions": json.dumps(msg.get("reactions", {}))
                        })

                return output.getvalue()

            else:  # txt
                lines = []
                for msg in messages_data:
                    timestamp = msg.get("timestamp", "")
                    user_name = msg.get("user_name", "")
                    message = msg.get("message", "")
                    is_private = msg.get("is_private", False)
                    reactions = msg.get("reactions", {})

                    line = f"[{timestamp}] {user_name}: {message}"
                    if is_private:
                        line += " (Private)"
                    if reactions:
                        reaction_str = " ".join([f"{emoji}x{count}" for emoji, count in reactions.items()])
                        line += f" | Reactions: {reaction_str}"
                    lines.append(line)

                return "\n".join(lines)

        except ZeroDBError as e:
            logger.error(f"Error exporting chat: {e}")
            raise SessionChatError(f"Failed to export chat: {e}")
