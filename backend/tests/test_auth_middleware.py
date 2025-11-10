"""
Comprehensive Unit Tests for Authorization Middleware

This test suite validates the authorization middleware implementation with 80%+ coverage.

Test Coverage:
- JWT token creation and validation
- Token expiration handling
- Role-based access control
- Resource-level permissions
- FastAPI dependency injection
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from backend.middleware.auth_middleware import (
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_token_from_header,
    get_current_user,
    get_optional_user,
    CurrentUser,
    RoleChecker,
    require_auth,
    require_role,
    require_admin,
    require_board_member,
    require_instructor,
    require_member,
    has_role_level,
    check_role_permission,
)
from backend.middleware.permissions import (
    is_resource_owner,
    is_profile_owner,
    can_approve_application,
    can_edit_application,
    can_view_application,
    can_view_event,
    can_edit_event,
    can_delete_event,
    can_view_member_data,
    can_edit_profile,
    can_view_training_session,
    can_edit_training_session,
    can_view_media_asset,
    can_edit_media_asset,
    require_permission,
    require_ownership,
    filter_by_visibility,
)
from backend.models.schemas import (
    UserRole,
    Application,
    Event,
    Profile,
    EventVisibility,
    ApplicationStatus,
    TrainingSession,
    MediaAsset,
    MediaType,
)
from backend.config import get_settings

settings = get_settings()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_user_id():
    """Generate a mock user ID"""
    return uuid4()


@pytest.fixture
def mock_user(mock_user_id):
    """Generate a mock user dictionary"""
    return {
        "id": mock_user_id,
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def admin_user(mock_user_id):
    """Generate an admin user"""
    return {
        "id": mock_user_id,
        "email": "admin@example.com",
        "role": "admin"
    }


@pytest.fixture
def board_member_user():
    """Generate a board member user"""
    return {
        "id": uuid4(),
        "email": "board@example.com",
        "role": "board_member"
    }


@pytest.fixture
def instructor_user():
    """Generate an instructor user"""
    return {
        "id": uuid4(),
        "email": "instructor@example.com",
        "role": "instructor"
    }


@pytest.fixture
def public_user():
    """Generate a public user"""
    return {
        "id": uuid4(),
        "email": "public@example.com",
        "role": "public"
    }


@pytest.fixture
def valid_access_token(mock_user_id):
    """Generate a valid access token"""
    return create_access_token(
        user_id=mock_user_id,
        email="test@example.com",
        role=UserRole.MEMBER
    )


@pytest.fixture
def valid_refresh_token(mock_user_id):
    """Generate a valid refresh token"""
    return create_refresh_token(user_id=mock_user_id)


@pytest.fixture
def expired_token(mock_user_id):
    """Generate an expired token"""
    expire = datetime.utcnow() - timedelta(minutes=30)
    to_encode = {
        "sub": str(mock_user_id),
        "email": "test@example.com",
        "role": "member",
        "exp": expire,
        "iat": datetime.utcnow() - timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def mock_application(mock_user_id):
    """Generate a mock application"""
    return Application(
        user_id=mock_user_id,
        status=ApplicationStatus.SUBMITTED,
        first_name="John",
        last_name="Doe",
        email="john@example.com"
    )


@pytest.fixture
def mock_event(mock_user_id):
    """Generate a mock event"""
    return Event(
        title="Test Event",
        event_type="training",
        visibility=EventVisibility.PUBLIC,
        start_datetime=datetime.utcnow() + timedelta(days=1),
        end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
        organizer_id=mock_user_id,
        is_published=True
    )


@pytest.fixture
def mock_profile(mock_user_id):
    """Generate a mock profile"""
    return Profile(
        user_id=mock_user_id,
        first_name="John",
        last_name="Doe",
        public_profile=False
    )


# ============================================================================
# TOKEN CREATION AND VALIDATION TESTS
# ============================================================================

class TestTokenCreation:
    """Test JWT token creation functionality"""

    def test_create_access_token_success(self, mock_user_id):
        """Test successful access token creation"""
        token = create_access_token(
            user_id=mock_user_id,
            email="test@example.com",
            role=UserRole.MEMBER
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == str(mock_user_id)
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "member"
        assert payload["type"] == "access"

    def test_create_access_token_with_custom_expiry(self, mock_user_id):
        """Test access token with custom expiration"""
        custom_expiry = timedelta(minutes=60)
        token = create_access_token(
            user_id=mock_user_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            expires_delta=custom_expiry
        )

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])

        # Check that expiration is approximately 60 minutes from issued time
        time_diff = (exp_time - iat_time).total_seconds()
        assert 3500 < time_diff < 3700  # Allow some tolerance

    def test_create_refresh_token_success(self, mock_user_id):
        """Test successful refresh token creation"""
        token = create_refresh_token(user_id=mock_user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == str(mock_user_id)
        assert payload["type"] == "refresh"

    def test_create_token_with_string_role(self, mock_user_id):
        """Test token creation with string role instead of enum"""
        token = create_access_token(
            user_id=mock_user_id,
            email="test@example.com",
            role="instructor"
        )

        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["role"] == "instructor"


class TestTokenDecoding:
    """Test JWT token decoding and validation"""

    def test_decode_valid_token(self, valid_access_token):
        """Test decoding a valid token"""
        payload = decode_token(valid_access_token)

        assert "sub" in payload
        assert "email" in payload
        assert "role" in payload
        assert "exp" in payload

    def test_decode_expired_token(self, expired_token):
        """Test that expired tokens raise HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    def test_decode_invalid_token(self):
        """Test that invalid tokens raise HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decode_malformed_token(self):
        """Test that malformed tokens raise HTTPException"""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not-a-jwt-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenExtraction:
    """Test token extraction from headers"""

    def test_extract_valid_bearer_token(self):
        """Test extracting token from valid Bearer header"""
        header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        token = extract_token_from_header(header)

        assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    def test_extract_invalid_scheme(self):
        """Test that non-Bearer schemes raise exception"""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("Basic abc123")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "scheme" in exc_info.value.detail.lower()

    def test_extract_malformed_header(self):
        """Test that malformed headers raise exception"""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("InvalidHeader")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# USER EXTRACTION TESTS
# ============================================================================

class TestGetCurrentUser:
    """Test current user extraction from token"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, valid_access_token, mock_user_id):
        """Test successful user extraction"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_access_token
        )

        user = await get_current_user(credentials)

        assert user["id"] == mock_user_id
        assert user["email"] == "test@example.com"
        assert user["role"] == "member"

    @pytest.mark.asyncio
    async def test_get_current_user_with_refresh_token(self, valid_refresh_token):
        """Test that refresh tokens are rejected"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_refresh_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "token type" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, expired_token):
        """Test that expired tokens raise exception"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=expired_token
        )

        with pytest.raises(HTTPException):
            await get_current_user(credentials)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_payload(self, mock_user_id):
        """Test token with missing required fields"""
        # Create token with missing email
        to_encode = {
            "sub": str(mock_user_id),
            "role": "member",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "type": "access"
        }
        token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetOptionalUser:
    """Test optional user extraction"""

    @pytest.mark.asyncio
    async def test_get_optional_user_with_valid_token(self, valid_access_token, mock_user_id):
        """Test extracting user with valid token"""
        mock_request = Mock()
        mock_request.headers.get.return_value = f"Bearer {valid_access_token}"

        user = await get_optional_user(mock_request)

        assert user is not None
        assert user["id"] == mock_user_id
        assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_optional_user_without_token(self):
        """Test that missing token returns None"""
        mock_request = Mock()
        mock_request.headers.get.return_value = None

        user = await get_optional_user(mock_request)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_optional_user_with_invalid_token(self):
        """Test that invalid token returns None"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Bearer invalid.token"

        user = await get_optional_user(mock_request)

        assert user is None


# ============================================================================
# FASTAPI DEPENDENCY TESTS
# ============================================================================

class TestCurrentUserDependency:
    """Test CurrentUser FastAPI dependency"""

    @pytest.mark.asyncio
    async def test_current_user_dependency(self, valid_access_token, mock_user_id):
        """Test CurrentUser dependency injection"""
        dependency = CurrentUser()
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_access_token
        )

        user = await dependency(credentials)

        assert user["id"] == mock_user_id
        assert user["email"] == "test@example.com"


class TestRoleCheckerDependency:
    """Test RoleChecker FastAPI dependency"""

    @pytest.mark.asyncio
    async def test_role_checker_admin_success(self, mock_user_id):
        """Test RoleChecker allows admin access"""
        admin_token = create_access_token(
            user_id=mock_user_id,
            email="admin@example.com",
            role=UserRole.ADMIN
        )

        checker = RoleChecker(allowed_roles=["admin"])
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=admin_token
        )

        user = await checker(credentials)

        assert user["role"] == "admin"

    @pytest.mark.asyncio
    async def test_role_checker_multiple_roles(self, mock_user_id):
        """Test RoleChecker with multiple allowed roles"""
        board_token = create_access_token(
            user_id=mock_user_id,
            email="board@example.com",
            role=UserRole.BOARD_MEMBER
        )

        checker = RoleChecker(allowed_roles=["admin", "board_member"])
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=board_token
        )

        user = await checker(credentials)

        assert user["role"] == "board_member"

    @pytest.mark.asyncio
    async def test_role_checker_denied(self, valid_access_token):
        """Test RoleChecker denies insufficient role"""
        checker = RoleChecker(allowed_roles=["admin"])
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=valid_access_token
        )

        with pytest.raises(HTTPException) as exc_info:
            await checker(credentials)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# ROLE HIERARCHY TESTS
# ============================================================================

class TestRoleHierarchy:
    """Test role hierarchy and permission checks"""

    def test_has_role_level_equal(self):
        """Test role level check with equal roles"""
        assert has_role_level(UserRole.MEMBER, UserRole.MEMBER) is True

    def test_has_role_level_higher(self):
        """Test role level check with higher role"""
        assert has_role_level(UserRole.ADMIN, UserRole.MEMBER) is True
        assert has_role_level(UserRole.BOARD_MEMBER, UserRole.INSTRUCTOR) is True

    def test_has_role_level_lower(self):
        """Test role level check with lower role"""
        assert has_role_level(UserRole.MEMBER, UserRole.ADMIN) is False
        assert has_role_level(UserRole.PUBLIC, UserRole.MEMBER) is False

    def test_has_role_level_string_input(self):
        """Test role level with string inputs"""
        assert has_role_level("admin", "member") is True
        assert has_role_level("member", "admin") is False

    def test_check_role_permission_allowed(self):
        """Test role permission check for allowed role"""
        assert check_role_permission(
            UserRole.ADMIN,
            [UserRole.ADMIN, UserRole.BOARD_MEMBER]
        ) is True

    def test_check_role_permission_denied(self):
        """Test role permission check for denied role"""
        assert check_role_permission(
            UserRole.MEMBER,
            [UserRole.ADMIN, UserRole.BOARD_MEMBER]
        ) is False

    def test_check_role_permission_string_input(self):
        """Test role permission with string inputs"""
        assert check_role_permission(
            "board_member",
            ["admin", "board_member"]
        ) is True


# ============================================================================
# APPLICATION PERMISSION TESTS
# ============================================================================

class TestApplicationPermissions:
    """Test application-related permissions"""

    def test_can_approve_application_admin(self, admin_user, mock_application):
        """Test admin can approve applications"""
        assert can_approve_application(admin_user, mock_application) is True

    def test_can_approve_application_board_member(self, board_member_user, mock_application):
        """Test board member can approve applications"""
        assert can_approve_application(board_member_user, mock_application) is True

    def test_can_approve_application_member_denied(self, mock_user, mock_application):
        """Test regular member cannot approve applications"""
        assert can_approve_application(mock_user, mock_application) is False

    def test_can_edit_application_owner(self, mock_user, mock_application):
        """Test owner can edit their own application"""
        assert can_edit_application(mock_user, mock_application) is True

    def test_can_edit_application_admin(self, admin_user):
        """Test admin can edit any application"""
        app = Application(
            user_id=uuid4(),
            status=ApplicationStatus.APPROVED,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        assert can_edit_application(admin_user, app) is True

    def test_can_edit_application_board_member_under_review(self, board_member_user):
        """Test board member can edit applications under review"""
        app = Application(
            user_id=uuid4(),
            status=ApplicationStatus.UNDER_REVIEW,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        assert can_edit_application(board_member_user, app) is True

    def test_can_edit_application_owner_approved_denied(self, mock_user):
        """Test owner cannot edit approved application"""
        app = Application(
            user_id=mock_user["id"],
            status=ApplicationStatus.APPROVED,
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        assert can_edit_application(mock_user, app) is False

    def test_can_view_application_owner(self, mock_user, mock_application):
        """Test owner can view their own application"""
        assert can_view_application(mock_user, mock_application) is True

    def test_can_view_application_admin(self, admin_user):
        """Test admin can view any application"""
        app = Application(
            user_id=uuid4(),
            status=ApplicationStatus.SUBMITTED,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        assert can_view_application(admin_user, app) is True

    def test_can_view_application_denied(self, mock_user):
        """Test user cannot view others' applications"""
        app = Application(
            user_id=uuid4(),
            status=ApplicationStatus.SUBMITTED,
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com"
        )
        assert can_view_application(mock_user, app) is False


# ============================================================================
# EVENT PERMISSION TESTS
# ============================================================================

class TestEventPermissions:
    """Test event-related permissions"""

    def test_can_view_public_event(self, mock_event):
        """Test anyone can view public event"""
        assert can_view_event(mock_event, None) is True

    def test_can_view_members_only_event_as_member(self, mock_user):
        """Test member can view members-only event"""
        event = Event(
            title="Members Event",
            event_type="training",
            visibility=EventVisibility.MEMBERS_ONLY,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            is_published=True
        )
        assert can_view_event(event, mock_user) is True

    def test_can_view_members_only_event_as_public_denied(self, public_user):
        """Test public user cannot view members-only event"""
        event = Event(
            title="Members Event",
            event_type="training",
            visibility=EventVisibility.MEMBERS_ONLY,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            is_published=True
        )
        assert can_view_event(event, public_user) is False

    def test_can_view_invite_only_event_as_instructor(self, instructor_user):
        """Test instructor can view invite-only event"""
        event = Event(
            title="Invite Only",
            event_type="training",
            visibility=EventVisibility.INVITE_ONLY,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            is_published=True
        )
        assert can_view_event(event, instructor_user) is True

    def test_can_view_unpublished_event_as_organizer(self, mock_user_id, mock_user):
        """Test organizer can view unpublished event"""
        event = Event(
            title="Unpublished Event",
            event_type="training",
            visibility=EventVisibility.PUBLIC,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=mock_user_id,
            is_published=False
        )
        assert can_view_event(event, mock_user) is True

    def test_can_edit_event_owner(self, mock_user, mock_event):
        """Test owner can edit their own event"""
        assert can_edit_event(mock_user, mock_event) is True

    def test_can_edit_event_admin(self, admin_user):
        """Test admin can edit any event"""
        event = Event(
            title="Test Event",
            event_type="training",
            visibility=EventVisibility.PUBLIC,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            is_published=True
        )
        assert can_edit_event(admin_user, event) is True

    def test_can_edit_event_instructor_assigned(self, instructor_user):
        """Test assigned instructor can edit event"""
        event = Event(
            title="Test Event",
            event_type="training",
            visibility=EventVisibility.PUBLIC,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            instructors=[instructor_user["id"]],
            is_published=True
        )
        assert can_edit_event(instructor_user, event) is True

    def test_can_delete_event_owner(self, mock_user, mock_event):
        """Test owner can delete their own event"""
        assert can_delete_event(mock_user, mock_event) is True

    def test_can_delete_event_board_member(self, board_member_user):
        """Test board member can delete any event"""
        event = Event(
            title="Test Event",
            event_type="training",
            visibility=EventVisibility.PUBLIC,
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
            organizer_id=uuid4(),
            is_published=True
        )
        assert can_delete_event(board_member_user, event) is True


# ============================================================================
# PROFILE PERMISSION TESTS
# ============================================================================

class TestProfilePermissions:
    """Test profile-related permissions"""

    def test_can_view_member_data_own_profile(self, mock_user, mock_user_id):
        """Test user can view their own profile"""
        assert can_view_member_data(mock_user, mock_user_id, False) is True

    def test_can_view_member_data_public_profile(self, mock_user):
        """Test anyone can view public profile"""
        other_user_id = uuid4()
        assert can_view_member_data(mock_user, other_user_id, True) is True

    def test_can_view_member_data_private_denied(self, mock_user):
        """Test user cannot view others' private profiles"""
        other_user_id = uuid4()
        assert can_view_member_data(mock_user, other_user_id, False) is False

    def test_can_view_member_data_admin(self, admin_user):
        """Test admin can view any profile"""
        other_user_id = uuid4()
        assert can_view_member_data(admin_user, other_user_id, False) is True

    def test_can_edit_profile_owner(self, mock_user, mock_profile):
        """Test owner can edit their own profile"""
        assert can_edit_profile(mock_user, mock_profile) is True

    def test_can_edit_profile_admin(self, admin_user):
        """Test admin can edit any profile"""
        profile = Profile(
            user_id=uuid4(),
            first_name="Jane",
            last_name="Doe"
        )
        assert can_edit_profile(admin_user, profile) is True

    def test_can_edit_profile_denied(self, mock_user):
        """Test user cannot edit others' profiles"""
        profile = Profile(
            user_id=uuid4(),
            first_name="Jane",
            last_name="Doe"
        )
        assert can_edit_profile(mock_user, profile) is False


# ============================================================================
# TRAINING SESSION PERMISSION TESTS
# ============================================================================

class TestTrainingSessionPermissions:
    """Test training session permissions"""

    def test_can_view_public_training_session(self):
        """Test anyone can view public training session"""
        session = TrainingSession(
            title="Public Session",
            instructor_id=uuid4(),
            session_date=datetime.utcnow(),
            duration_minutes=60,
            discipline="Karate",
            is_public=True,
            members_only=False
        )
        assert can_view_training_session(session, None) is True

    def test_can_view_members_only_session_as_member(self, mock_user):
        """Test member can view members-only session"""
        session = TrainingSession(
            title="Members Session",
            instructor_id=uuid4(),
            session_date=datetime.utcnow(),
            duration_minutes=60,
            discipline="Karate",
            is_public=False,
            members_only=True
        )
        assert can_view_training_session(session, mock_user) is True

    def test_can_view_members_only_session_denied(self, public_user):
        """Test public user cannot view members-only session"""
        session = TrainingSession(
            title="Members Session",
            instructor_id=uuid4(),
            session_date=datetime.utcnow(),
            duration_minutes=60,
            discipline="Karate",
            is_public=False,
            members_only=True
        )
        assert can_view_training_session(session, public_user) is False

    def test_can_edit_training_session_instructor(self, instructor_user):
        """Test instructor can edit their own session"""
        session = TrainingSession(
            title="Test Session",
            instructor_id=instructor_user["id"],
            session_date=datetime.utcnow(),
            duration_minutes=60,
            discipline="Karate",
            is_public=True
        )
        assert can_edit_training_session(instructor_user, session) is True

    def test_can_edit_training_session_assistant(self, instructor_user):
        """Test assistant instructor can edit session"""
        session = TrainingSession(
            title="Test Session",
            instructor_id=uuid4(),
            assistant_instructors=[instructor_user["id"]],
            session_date=datetime.utcnow(),
            duration_minutes=60,
            discipline="Karate",
            is_public=True
        )
        assert can_edit_training_session(instructor_user, session) is True


# ============================================================================
# MEDIA ASSET PERMISSION TESTS
# ============================================================================

class TestMediaAssetPermissions:
    """Test media asset permissions"""

    def test_can_view_public_media(self):
        """Test anyone can view public media"""
        media = MediaAsset(
            media_type=MediaType.IMAGE,
            filename="test.jpg",
            file_size_bytes=1024,
            mime_type="image/jpeg",
            uploaded_by=uuid4(),
            is_public=True
        )
        assert can_view_media_asset(media, None) is True

    def test_can_view_private_media_owner(self, mock_user):
        """Test uploader can view their own media"""
        media = MediaAsset(
            media_type=MediaType.IMAGE,
            filename="test.jpg",
            file_size_bytes=1024,
            mime_type="image/jpeg",
            uploaded_by=mock_user["id"],
            is_public=False
        )
        assert can_view_media_asset(media, mock_user) is True

    def test_can_view_private_media_with_role_access(self, mock_user):
        """Test user with role access can view media"""
        media = MediaAsset(
            media_type=MediaType.IMAGE,
            filename="test.jpg",
            file_size_bytes=1024,
            mime_type="image/jpeg",
            uploaded_by=uuid4(),
            is_public=False,
            access_roles=[UserRole.MEMBER]
        )
        assert can_view_media_asset(media, mock_user) is True

    def test_can_edit_media_owner(self, mock_user):
        """Test uploader can edit their own media"""
        media = MediaAsset(
            media_type=MediaType.IMAGE,
            filename="test.jpg",
            file_size_bytes=1024,
            mime_type="image/jpeg",
            uploaded_by=mock_user["id"],
            is_public=False
        )
        assert can_edit_media_asset(mock_user, media) is True


# ============================================================================
# PERMISSION ENFORCEMENT TESTS
# ============================================================================

class TestPermissionEnforcement:
    """Test permission enforcement helpers"""

    def test_require_permission_allowed(self):
        """Test require_permission passes when allowed"""
        # Should not raise exception
        require_permission(True, "Test error")

    def test_require_permission_denied(self):
        """Test require_permission raises exception when denied"""
        with pytest.raises(HTTPException) as exc_info:
            require_permission(False, "Custom error message")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Custom error message"

    def test_require_ownership_allowed(self, mock_user_id):
        """Test require_ownership passes when user owns resource"""
        # Should not raise exception
        require_ownership(mock_user_id, mock_user_id, "Test error")

    def test_require_ownership_denied(self, mock_user_id):
        """Test require_ownership raises exception when user doesn't own"""
        other_user_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            require_ownership(mock_user_id, other_user_id, "Not your resource")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Not your resource"


class TestFilterByVisibility:
    """Test visibility filtering helper"""

    def test_filter_by_visibility_public_events(self):
        """Test filtering public events"""
        events = [
            Event(
                title="Public 1",
                event_type="training",
                visibility=EventVisibility.PUBLIC,
                start_datetime=datetime.utcnow(),
                end_datetime=datetime.utcnow(),
                organizer_id=uuid4(),
                is_published=True
            ),
            Event(
                title="Members Only",
                event_type="training",
                visibility=EventVisibility.MEMBERS_ONLY,
                start_datetime=datetime.utcnow(),
                end_datetime=datetime.utcnow(),
                organizer_id=uuid4(),
                is_published=True
            ),
        ]

        filtered = filter_by_visibility(
            events,
            None,
            lambda event, user: can_view_event(event, user)
        )

        assert len(filtered) == 1
        assert filtered[0].title == "Public 1"


# ============================================================================
# OWNERSHIP CHECKS TESTS
# ============================================================================

class TestOwnershipChecks:
    """Test resource ownership checks"""

    def test_is_resource_owner_true(self, mock_user_id):
        """Test resource ownership check returns True for owner"""
        assert is_resource_owner(mock_user_id, mock_user_id) is True

    def test_is_resource_owner_false(self, mock_user_id):
        """Test resource ownership check returns False for non-owner"""
        other_user_id = uuid4()
        assert is_resource_owner(mock_user_id, other_user_id) is False

    def test_is_profile_owner_true(self, mock_user_id):
        """Test profile ownership check returns True for owner"""
        assert is_profile_owner(mock_user_id, mock_user_id) is True

    def test_is_profile_owner_false(self, mock_user_id):
        """Test profile ownership check returns False for non-owner"""
        other_user_id = uuid4()
        assert is_profile_owner(mock_user_id, other_user_id) is False
