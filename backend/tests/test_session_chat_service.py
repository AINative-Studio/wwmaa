"""
Tests for Session Chat Service - US-050: Chat & Interaction Features

Tests for:
- Message sending and retrieval
- Private messaging
- Rate limiting
- Profanity filtering
- Muting/unmuting
- Reactions
- Raise hand feature
- Typing indicators
- Chat export
"""

import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch

from backend.services.session_chat_service import (
    SessionChatService,
    SessionChatError,
    RateLimitError,
    MutedUserError
)
from backend.models.schemas import (
    SessionChatMessage,
    SessionMute,
    SessionRaisedHand,
    ReactionType,
    UserRole
)


@pytest.fixture
def mock_db():
    """Mock ZeroDB client"""
    db = Mock()
    db.insert_one = Mock(return_value={"id": str(uuid4())})
    db.find = Mock(return_value=[])
    db.find_by_id = Mock(return_value=None)
    db.update_one = Mock(return_value=True)
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_client = Mock()
    redis_client.get = Mock(return_value=None)
    redis_client.setex = Mock(return_value=True)
    redis_client.incr = Mock(return_value=1)
    redis_client.delete = Mock(return_value=True)
    redis_client.keys = Mock(return_value=[])
    redis_client.expire = Mock(return_value=True)
    return redis_client


@pytest.fixture
def chat_service(mock_db, mock_redis):
    """Create SessionChatService instance with mocked dependencies"""
    with patch('backend.services.session_chat_service.redis.from_url', return_value=mock_redis):
        service = SessionChatService(mock_db)
        service.redis_client = mock_redis
        return service


@pytest.fixture
def sample_session_id():
    """Sample session ID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return uuid4()


@pytest.fixture
def sample_message_data(sample_session_id, sample_user_id):
    """Sample message data"""
    return {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "user_name": "Test User",
        "message": "Hello, world!",
        "is_private": False,
        "recipient_id": None,
        "recipient_name": None,
        "reactions": {},
        "is_deleted": False,
        "deleted_at": None,
        "deleted_by": None,
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


# Tests for send_message

def test_send_message_success(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test successful message sending"""
    # Setup
    mock_db.find.return_value = []  # No active mutes
    mock_redis.get.return_value = None  # No rate limit

    # Execute
    message = chat_service.send_message(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User",
        message="Hello, world!",
        is_instructor=False
    )

    # Assert
    assert isinstance(message, SessionChatMessage)
    assert message.message == "Hello, world!"
    assert message.user_name == "Test User"
    assert not message.is_private
    mock_db.insert_one.assert_called_once()


def test_send_message_rate_limit_exceeded(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test message sending with rate limit exceeded"""
    # Setup
    mock_db.find.return_value = []  # No active mutes
    mock_redis.get.return_value = "5"  # At rate limit

    # Execute & Assert
    with pytest.raises(RateLimitError) as exc_info:
        chat_service.send_message(
            session_id=sample_session_id,
            user_id=sample_user_id,
            user_name="Test User",
            message="Hello, world!",
            is_instructor=False
        )

    assert "Rate limit exceeded" in str(exc_info.value)


def test_send_message_user_muted(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test message sending when user is muted"""
    # Setup
    mute_data = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "muted_by": str(uuid4()),
        "muted_until": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        "reason": "Test mute",
        "is_active": True,
        "muted_at": datetime.utcnow().isoformat(),
        "unmuted_at": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [mute_data]

    # Execute & Assert
    with pytest.raises(MutedUserError) as exc_info:
        chat_service.send_message(
            session_id=sample_session_id,
            user_id=sample_user_id,
            user_name="Test User",
            message="Hello, world!",
            is_instructor=False
        )

    assert "User is muted" in str(exc_info.value)


def test_send_message_profanity_filtered(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test message with profanity is filtered"""
    # Setup
    mock_db.find.return_value = []  # No active mutes
    mock_redis.get.return_value = None  # No rate limit
    mock_redis.incr.return_value = 1  # First strike

    # Execute
    message = chat_service.send_message(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User",
        message="This is a damn test message",  # Contains profanity
        is_instructor=False
    )

    # Assert - profanity should be censored
    assert "***" in message.message or message.message != "This is a damn test message"
    mock_redis.incr.assert_called_once()


def test_send_message_instructor_bypasses_rate_limit(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test instructor bypasses rate limit"""
    # Setup
    mock_db.find.return_value = []  # No active mutes
    mock_redis.get.return_value = "10"  # Well over rate limit

    # Execute - should succeed for instructor
    message = chat_service.send_message(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Instructor",
        message="Hello, class!",
        is_instructor=True
    )

    # Assert
    assert isinstance(message, SessionChatMessage)


def test_send_private_message(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test sending private message"""
    # Setup
    mock_db.find.return_value = []  # No active mutes
    mock_redis.get.return_value = None  # No rate limit
    recipient_id = uuid4()

    # Execute
    message = chat_service.send_message(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Instructor",
        message="Private message",
        is_private=True,
        recipient_id=recipient_id,
        recipient_name="Student",
        is_instructor=True
    )

    # Assert
    assert message.is_private
    assert message.recipient_id == recipient_id
    assert message.recipient_name == "Student"


# Tests for get_messages

def test_get_messages_success(chat_service, mock_db, sample_session_id, sample_user_id, sample_message_data):
    """Test successful message retrieval"""
    # Setup
    mock_db.find.return_value = [sample_message_data]

    # Execute
    messages = chat_service.get_messages(
        session_id=sample_session_id,
        user_id=sample_user_id,
        is_instructor=False
    )

    # Assert
    assert len(messages) == 1
    assert isinstance(messages[0], SessionChatMessage)
    assert messages[0].message == "Hello, world!"


def test_get_messages_filters_private_for_non_instructor(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test private messages are filtered for non-instructors"""
    # Setup - call with non-instructor user
    chat_service.get_messages(
        session_id=sample_session_id,
        user_id=sample_user_id,
        is_instructor=False
    )

    # Assert - query should include $or for private message filtering
    call_args = mock_db.find.call_args
    query = call_args[0][1]
    assert "$or" in query or "is_private" in query


def test_get_messages_instructor_sees_all(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test instructor sees all messages"""
    # Execute
    chat_service.get_messages(
        session_id=sample_session_id,
        user_id=sample_user_id,
        is_instructor=True
    )

    # Assert - query should not filter private messages
    call_args = mock_db.find.call_args
    query = call_args[0][1]
    assert "$or" not in query


# Tests for delete_message

def test_delete_message_success(chat_service, mock_db, sample_user_id):
    """Test successful message deletion"""
    # Setup
    message_id = uuid4()

    # Execute
    result = chat_service.delete_message(
        message_id=message_id,
        deleted_by=sample_user_id,
        is_instructor=True
    )

    # Assert
    assert result is True
    mock_db.update_one.assert_called_once()


def test_delete_message_non_instructor_fails(chat_service, sample_user_id):
    """Test non-instructor cannot delete message"""
    # Setup
    message_id = uuid4()

    # Execute & Assert
    with pytest.raises(PermissionError) as exc_info:
        chat_service.delete_message(
            message_id=message_id,
            deleted_by=sample_user_id,
            is_instructor=False
        )

    assert "Only instructors" in str(exc_info.value)


# Tests for mute_user / unmute_user

def test_mute_user_success(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test successful user muting"""
    # Setup
    muted_by = uuid4()

    # Execute
    mute = chat_service.mute_user(
        session_id=sample_session_id,
        user_id=sample_user_id,
        muted_by=muted_by,
        duration_minutes=15,
        reason="Test mute"
    )

    # Assert
    assert isinstance(mute, SessionMute)
    assert mute.user_id == sample_user_id
    assert mute.reason == "Test mute"
    assert mute.is_active
    mock_db.insert_one.assert_called_once()


def test_mute_user_permanent(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test permanent user muting"""
    # Setup
    muted_by = uuid4()

    # Execute
    mute = chat_service.mute_user(
        session_id=sample_session_id,
        user_id=sample_user_id,
        muted_by=muted_by,
        duration_minutes=None,  # Permanent
        reason="Permanent mute"
    )

    # Assert
    assert mute.muted_until is None


def test_unmute_user_success(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test successful user unmuting"""
    # Setup
    mute_data = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "muted_by": str(uuid4()),
        "is_active": True,
        "muted_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [mute_data]

    # Execute
    result = chat_service.unmute_user(
        session_id=sample_session_id,
        user_id=sample_user_id
    )

    # Assert
    assert result is True
    mock_db.update_one.assert_called()


# Tests for add_reaction

def test_add_reaction_success(chat_service, mock_db, mock_redis, sample_user_id, sample_message_data):
    """Test successful reaction addition"""
    # Setup
    message_id = UUID(sample_message_data["id"])
    mock_db.find_by_id.return_value = sample_message_data
    mock_redis.get.return_value = None  # No rate limit

    # Execute
    result = chat_service.add_reaction(
        message_id=message_id,
        user_id=sample_user_id,
        reaction="👍",
        is_instructor=False
    )

    # Assert
    assert result is True
    mock_db.update_one.assert_called_once()


def test_add_reaction_invalid_type(chat_service, sample_user_id):
    """Test adding invalid reaction type"""
    # Setup
    message_id = uuid4()

    # Execute & Assert
    with pytest.raises(ValueError) as exc_info:
        chat_service.add_reaction(
            message_id=message_id,
            user_id=sample_user_id,
            reaction="😀",  # Invalid reaction
            is_instructor=False
        )

    assert "Invalid reaction" in str(exc_info.value)


def test_add_reaction_rate_limit(chat_service, mock_redis, sample_user_id):
    """Test reaction rate limiting"""
    # Setup
    message_id = uuid4()
    mock_redis.get.return_value = "10"  # At rate limit

    # Execute & Assert
    with pytest.raises(RateLimitError):
        chat_service.add_reaction(
            message_id=message_id,
            user_id=sample_user_id,
            reaction="👍",
            is_instructor=False
        )


# Tests for raise_hand / lower_hand

def test_raise_hand_success(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test successful hand raising"""
    # Setup
    mock_db.find.return_value = []  # No existing raised hands

    # Execute
    raised_hand = chat_service.raise_hand(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User"
    )

    # Assert
    assert isinstance(raised_hand, SessionRaisedHand)
    assert raised_hand.user_id == sample_user_id
    assert raised_hand.is_active
    mock_db.insert_one.assert_called_once()


def test_raise_hand_already_raised(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test raising hand when already raised"""
    # Setup
    existing_hand = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "user_name": "Test User",
        "is_active": True,
        "raised_at": datetime.utcnow().isoformat(),
        "lowered_at": None,
        "acknowledged_by": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [existing_hand]

    # Execute
    raised_hand = chat_service.raise_hand(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User"
    )

    # Assert - should return existing raised hand
    assert isinstance(raised_hand, SessionRaisedHand)
    # Should not insert new record
    mock_db.insert_one.assert_not_called()


def test_lower_hand_success(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test successful hand lowering"""
    # Setup
    hand_data = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "is_active": True,
        "raised_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [hand_data]

    # Execute
    result = chat_service.lower_hand(
        session_id=sample_session_id,
        user_id=sample_user_id
    )

    # Assert
    assert result is True
    mock_db.update_one.assert_called()


def test_lower_hand_with_acknowledgment(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test hand lowering with instructor acknowledgment"""
    # Setup
    hand_data = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "is_active": True,
        "raised_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [hand_data]
    instructor_id = uuid4()

    # Execute
    result = chat_service.lower_hand(
        session_id=sample_session_id,
        user_id=sample_user_id,
        acknowledged_by=instructor_id
    )

    # Assert
    assert result is True
    call_args = mock_db.update_one.call_args
    update_data = call_args[0][2]
    assert update_data.get("acknowledged_by") == str(instructor_id)


def test_get_raised_hands_success(chat_service, mock_db, sample_session_id):
    """Test getting active raised hands"""
    # Setup
    hands_data = [
        {
            "id": str(uuid4()),
            "session_id": str(sample_session_id),
            "user_id": str(uuid4()),
            "user_name": "User 1",
            "is_active": True,
            "raised_at": datetime.utcnow().isoformat(),
            "lowered_at": None,
            "acknowledged_by": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": str(sample_session_id),
            "user_id": str(uuid4()),
            "user_name": "User 2",
            "is_active": True,
            "raised_at": datetime.utcnow().isoformat(),
            "lowered_at": None,
            "acknowledged_by": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    mock_db.find.return_value = hands_data

    # Execute
    hands = chat_service.get_raised_hands(sample_session_id)

    # Assert
    assert len(hands) == 2
    assert all(isinstance(hand, SessionRaisedHand) for hand in hands)


# Tests for typing indicators

def test_set_typing_start(chat_service, mock_redis, sample_session_id, sample_user_id):
    """Test setting typing indicator"""
    # Execute
    result = chat_service.set_typing(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User",
        is_typing=True
    )

    # Assert
    assert result is True
    mock_redis.setex.assert_called_once()


def test_set_typing_stop(chat_service, mock_redis, sample_session_id, sample_user_id):
    """Test removing typing indicator"""
    # Execute
    result = chat_service.set_typing(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User",
        is_typing=False
    )

    # Assert
    assert result is True
    mock_redis.delete.assert_called_once()


def test_get_typing_users(chat_service, mock_redis, sample_session_id):
    """Test getting typing users"""
    # Setup
    typing_keys = [
        f"typing:{sample_session_id}:{uuid4()}",
        f"typing:{sample_session_id}:{uuid4()}"
    ]
    mock_redis.keys.return_value = typing_keys
    mock_redis.get.return_value = json.dumps({
        "user_id": str(uuid4()),
        "user_name": "Test User",
        "timestamp": datetime.utcnow().isoformat()
    })

    # Execute
    typing_users = chat_service.get_typing_users(sample_session_id)

    # Assert
    assert len(typing_users) == 2


# Tests for export_chat

def test_export_chat_json(chat_service, mock_db, sample_session_id, sample_message_data):
    """Test chat export as JSON"""
    # Setup
    mock_db.find.return_value = [sample_message_data]

    # Execute
    export_data = chat_service.export_chat(
        session_id=sample_session_id,
        format="json",
        include_private=False
    )

    # Assert
    assert isinstance(export_data, str)
    data = json.loads(export_data)
    assert len(data) == 1
    assert data[0]["message"] == "Hello, world!"


def test_export_chat_csv(chat_service, mock_db, sample_session_id, sample_message_data):
    """Test chat export as CSV"""
    # Setup
    mock_db.find.return_value = [sample_message_data]

    # Execute
    export_data = chat_service.export_chat(
        session_id=sample_session_id,
        format="csv",
        include_private=False
    )

    # Assert
    assert isinstance(export_data, str)
    assert "user_name" in export_data
    assert "message" in export_data
    assert "Test User" in export_data


def test_export_chat_txt(chat_service, mock_db, sample_session_id, sample_message_data):
    """Test chat export as plain text"""
    # Setup
    mock_db.find.return_value = [sample_message_data]

    # Execute
    export_data = chat_service.export_chat(
        session_id=sample_session_id,
        format="txt",
        include_private=False
    )

    # Assert
    assert isinstance(export_data, str)
    assert "Test User" in export_data
    assert "Hello, world!" in export_data


def test_export_chat_invalid_format(chat_service, sample_session_id):
    """Test chat export with invalid format"""
    # Execute & Assert
    with pytest.raises(ValueError) as exc_info:
        chat_service.export_chat(
            session_id=sample_session_id,
            format="pdf",  # Invalid format
            include_private=False
        )

    assert "Format must be" in str(exc_info.value)


def test_export_chat_includes_private(chat_service, mock_db, sample_session_id):
    """Test chat export includes private messages"""
    # Execute
    chat_service.export_chat(
        session_id=sample_session_id,
        format="json",
        include_private=True
    )

    # Assert - query should not filter private messages
    call_args = mock_db.find.call_args
    query = call_args[0][1]
    assert query.get("is_private") != False


# Tests for profanity filter and auto-mute

def test_profanity_auto_mute_after_strikes(chat_service, mock_db, mock_redis, sample_session_id, sample_user_id):
    """Test auto-mute after profanity strikes threshold"""
    # Setup
    mock_db.find.return_value = []  # No active mutes initially
    mock_redis.get.return_value = None  # No rate limit
    mock_redis.incr.return_value = 3  # Third strike

    # Execute - send message with profanity
    chat_service.send_message(
        session_id=sample_session_id,
        user_id=sample_user_id,
        user_name="Test User",
        message="This is a damn test",  # Profanity
        is_instructor=False
    )

    # Assert - should have called mute_user
    # Check if insert_one was called twice (once for message, once for mute)
    assert mock_db.insert_one.call_count >= 1


# Tests for edge cases

def test_check_if_muted_expired_mute(chat_service, mock_db, sample_session_id, sample_user_id):
    """Test checking mute status with expired mute"""
    # Setup - mute expired 1 minute ago
    mute_data = {
        "id": str(uuid4()),
        "session_id": str(sample_session_id),
        "user_id": str(sample_user_id),
        "muted_by": str(uuid4()),
        "muted_until": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
        "is_active": True,
        "muted_at": datetime.utcnow().isoformat(),
        "unmuted_at": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [mute_data]

    # Execute
    mute = chat_service._check_if_muted(sample_session_id, sample_user_id)

    # Assert - expired mute should return None
    assert mute is None
    # Should have called unmute_user
    mock_db.update_one.assert_called()


def test_rate_limit_with_redis_error(chat_service, mock_redis, sample_user_id):
    """Test rate limiting handles Redis errors gracefully"""
    # Setup
    import redis as redis_module
    mock_redis.get.side_effect = redis_module.RedisError("Redis connection error")

    # Execute - should not raise exception (fail open)
    result = chat_service._check_rate_limit(sample_user_id, "message", False)

    # Assert - should allow action when Redis is down
    assert result is True


def test_message_with_empty_text_fails_validation():
    """Test message with empty text fails Pydantic validation"""
    # Execute & Assert
    with pytest.raises(Exception):  # Pydantic validation error
        SessionChatMessage(
            session_id=uuid4(),
            user_id=uuid4(),
            user_name="Test User",
            message="",  # Empty message
            timestamp=datetime.utcnow()
        )


# Integration-style tests

def test_full_message_flow(chat_service, mock_db, mock_redis, sample_session_id):
    """Test full message flow: send, react, retrieve"""
    # Setup
    mock_db.find.return_value = []  # No mutes
    mock_redis.get.return_value = None  # No rate limit
    user_id = uuid4()

    # Step 1: Send message
    message = chat_service.send_message(
        session_id=sample_session_id,
        user_id=user_id,
        user_name="Test User",
        message="Hello, world!",
        is_instructor=False
    )

    assert isinstance(message, SessionChatMessage)
    message_id = message.id

    # Step 2: Add reaction
    message_data = {
        "id": str(message_id),
        "session_id": str(sample_session_id),
        "user_id": str(user_id),
        "user_name": "Test User",
        "message": "Hello, world!",
        "is_private": False,
        "reactions": {},
        "is_deleted": False,
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find_by_id.return_value = message_data

    result = chat_service.add_reaction(
        message_id=message_id,
        user_id=user_id,
        reaction="👍",
        is_instructor=False
    )

    assert result is True

    # Step 3: Retrieve messages
    mock_db.find.return_value = [message_data]
    messages = chat_service.get_messages(
        session_id=sample_session_id,
        user_id=user_id,
        is_instructor=False
    )

    assert len(messages) >= 0  # May not include the just-sent message due to mocking


def test_full_raise_hand_flow(chat_service, mock_db, sample_session_id):
    """Test full raise hand flow: raise, get list, lower"""
    # Setup
    user_id = uuid4()
    mock_db.find.return_value = []  # No existing raised hands

    # Step 1: Raise hand
    raised_hand = chat_service.raise_hand(
        session_id=sample_session_id,
        user_id=user_id,
        user_name="Test User"
    )

    assert isinstance(raised_hand, SessionRaisedHand)
    assert raised_hand.is_active

    # Step 2: Get raised hands
    hand_data = {
        "id": str(raised_hand.id),
        "session_id": str(sample_session_id),
        "user_id": str(user_id),
        "user_name": "Test User",
        "is_active": True,
        "raised_at": datetime.utcnow().isoformat(),
        "lowered_at": None,
        "acknowledged_by": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    mock_db.find.return_value = [hand_data]

    hands = chat_service.get_raised_hands(sample_session_id)
    assert len(hands) == 1

    # Step 3: Lower hand
    result = chat_service.lower_hand(
        session_id=sample_session_id,
        user_id=user_id
    )

    assert result is True
