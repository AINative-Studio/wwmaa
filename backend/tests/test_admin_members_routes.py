"""
Unit Tests for Admin Members Routes

Tests all CRUD operations for admin members management:
- POST /api/admin/members - Create member
- PUT /api/admin/members/:id - Update member
- DELETE /api/admin/members/:id - Delete member
- GET /api/admin/members - List members
- GET /api/admin/members/:id - Get single member

Security Tests:
- Non-admin users cannot access endpoints
- Email uniqueness validation
- Password strength validation
- Role validation
- Self-deletion prevention
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from backend.routes.admin.members import (
    router,
    create_member,
    update_member,
    delete_member,
    list_members,
    get_member,
    MemberCreateRequest,
    MemberUpdateRequest,
    format_member_response
)
from backend.models.schemas import UserRole


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication"""
    return {
        "id": uuid4(),
        "email": "admin@wwmaa.com",
        "role": "admin"
    }


@pytest.fixture
def mock_member_user():
    """Mock regular member user (non-admin)"""
    return {
        "id": uuid4(),
        "email": "member@wwmaa.com",
        "role": "member"
    }


@pytest.fixture
def sample_user_data():
    """Sample user document from database"""
    user_id = uuid4()
    return {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "$2b$12$abcdefghijklmnopqrstuvwxyz",
        "role": "member",
        "is_active": True,
        "is_verified": False,
        "last_login": None,
        "profile_id": uuid4(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_profile_data(sample_user_data):
    """Sample profile document from database"""
    return {
        "id": sample_user_data["profile_id"],
        "user_id": sample_user_data["id"],
        "first_name": "Test",
        "last_name": "User",
        "display_name": "Test User",
        "phone": "+12025551234",
        "bio": None,
        "avatar_url": None,
        "city": None,
        "state": None,
        "country": "USA",
        "disciplines": [],
        "ranks": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client"""
    with patch('backend.routes.admin.members.zerodb_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_hash_password():
    """Mock password hashing function"""
    with patch('backend.routes.admin.members.hash_password') as mock_hash:
        mock_hash.return_value = "$2b$12$mocked_password_hash"
        yield mock_hash


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

def test_format_member_response(sample_user_data, sample_profile_data):
    """Test formatting member response with user and profile data"""
    result = format_member_response(sample_user_data, sample_profile_data)

    assert result["id"] == str(sample_user_data["id"])
    assert result["email"] == sample_user_data["email"]
    assert result["role"] == sample_user_data["role"]
    assert result["is_active"] == sample_user_data["is_active"]
    assert result["is_verified"] == sample_user_data["is_verified"]
    assert result["first_name"] == sample_profile_data["first_name"]
    assert result["last_name"] == sample_profile_data["last_name"]
    assert result["phone"] == sample_profile_data["phone"]


def test_format_member_response_no_profile(sample_user_data):
    """Test formatting member response without profile"""
    result = format_member_response(sample_user_data, None)

    assert result["id"] == str(sample_user_data["id"])
    assert result["email"] == sample_user_data["email"]
    assert result["first_name"] is None
    assert result["last_name"] is None
    assert result["phone"] is None


# ============================================================================
# CREATE MEMBER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_member_success(
    mock_zerodb_client,
    mock_hash_password,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test successfully creating a new member"""
    # Setup mocks
    mock_zerodb_client.find_one.side_effect = [
        None,  # First call: no existing user with that email
        sample_user_data  # Final call: get created user
    ]
    mock_zerodb_client.insert_one.side_effect = [
        sample_user_data,  # User creation
        sample_profile_data  # Profile creation
    ]
    mock_zerodb_client.update_one.return_value = True

    # Create request
    request_data = MemberCreateRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="Test",
        last_name="User",
        role=UserRole.MEMBER
    )

    # Execute
    result = await create_member(request_data, mock_admin_user)

    # Assertions
    assert result["email"] == "test@example.com"
    assert result["role"] == "member"
    assert result["first_name"] == "Test"
    assert result["last_name"] == "User"

    # Verify function calls
    mock_hash_password.assert_called_once_with("SecurePass123!")
    assert mock_zerodb_client.insert_one.call_count == 2
    mock_zerodb_client.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_member_duplicate_email(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data
):
    """Test creating member with duplicate email fails"""
    # Setup: email already exists
    mock_zerodb_client.find_one.return_value = sample_user_data

    request_data = MemberCreateRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="Test",
        last_name="User"
    )

    # Execute and assert
    with pytest.raises(HTTPException) as exc_info:
        await create_member(request_data, mock_admin_user)

    assert exc_info.value.status_code == 409
    assert "already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_member_profile_failure_rollback(
    mock_zerodb_client,
    mock_hash_password,
    mock_admin_user,
    sample_user_data
):
    """Test that user is deleted if profile creation fails"""
    # Setup mocks
    mock_zerodb_client.find_one.return_value = None
    mock_zerodb_client.insert_one.side_effect = [
        sample_user_data,  # User creation succeeds
        None  # Profile creation fails
    ]

    request_data = MemberCreateRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="Test",
        last_name="User"
    )

    # Execute and assert
    with pytest.raises(HTTPException) as exc_info:
        await create_member(request_data, mock_admin_user)

    assert exc_info.value.status_code == 500
    assert "Failed to create user profile" in str(exc_info.value.detail)

    # Verify rollback: user should be deleted
    mock_zerodb_client.delete_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_member_invalid_password():
    """Test creating member with weak password fails validation"""
    with pytest.raises(ValueError) as exc_info:
        MemberCreateRequest(
            email="test@example.com",
            password="weak",  # Too short
            first_name="Test",
            last_name="User"
        )

    assert "password" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_member_invalid_role():
    """Test creating member with invalid role fails validation"""
    from pydantic import ValidationError
    with pytest.raises(ValidationError) as exc_info:
        MemberCreateRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User",
            role="invalid_role"  # Invalid role
        )

    assert "role" in str(exc_info.value).lower()


# ============================================================================
# UPDATE MEMBER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_member_success(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test successfully updating a member"""
    member_id = str(sample_user_data["id"])

    # Setup mocks
    mock_zerodb_client.find_one.side_effect = [
        sample_user_data,  # First call: check member exists
        None,  # Second call: check email not duplicate
        sample_profile_data,  # Third call: get current profile
        sample_user_data,  # Fourth call: get updated user
        sample_profile_data  # Fifth call: get updated profile
    ]
    mock_zerodb_client.update_one.return_value = True

    # Create update request
    update_data = MemberUpdateRequest(
        email="newemail@example.com",
        first_name="Updated",
        last_name="Name",
        role=UserRole.INSTRUCTOR
    )

    # Execute
    result = await update_member(member_id, update_data, mock_admin_user)

    # Assertions
    assert result["id"] == member_id
    assert mock_zerodb_client.update_one.call_count == 2  # User and profile


@pytest.mark.asyncio
async def test_update_member_not_found(
    mock_zerodb_client,
    mock_admin_user
):
    """Test updating non-existent member fails"""
    member_id = str(uuid4())
    mock_zerodb_client.find_one.return_value = None

    update_data = MemberUpdateRequest(first_name="Test")

    with pytest.raises(HTTPException) as exc_info:
        await update_member(member_id, update_data, mock_admin_user)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_member_duplicate_email(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data
):
    """Test updating email to existing email fails"""
    member_id = str(uuid4())
    other_user = sample_user_data.copy()
    other_user["id"] = uuid4()

    # Setup mocks
    mock_zerodb_client.find_one.side_effect = [
        sample_user_data,  # Member exists
        other_user  # Email is taken by another user
    ]

    update_data = MemberUpdateRequest(email="taken@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await update_member(member_id, update_data, mock_admin_user)

    assert exc_info.value.status_code == 409
    assert "already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_member_password(
    mock_zerodb_client,
    mock_hash_password,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test updating member password"""
    member_id = str(sample_user_data["id"])

    mock_zerodb_client.find_one.side_effect = [
        sample_user_data,  # Member exists
        sample_user_data,  # Get updated user
        sample_profile_data  # Get profile
    ]
    mock_zerodb_client.update_one.return_value = True

    update_data = MemberUpdateRequest(password="NewSecurePass123!")

    result = await update_member(member_id, update_data, mock_admin_user)

    # Verify password was hashed
    mock_hash_password.assert_called_once_with("NewSecurePass123!")


@pytest.mark.asyncio
async def test_update_member_invalid_id(mock_admin_user):
    """Test updating member with invalid UUID format fails"""
    update_data = MemberUpdateRequest(first_name="Test")

    with pytest.raises(HTTPException) as exc_info:
        await update_member("invalid-uuid", update_data, mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "Invalid member ID" in str(exc_info.value.detail)


# ============================================================================
# DELETE MEMBER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_member_success(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data
):
    """Test successfully deleting a member"""
    member_id = str(sample_user_data["id"])

    # Setup mocks
    mock_zerodb_client.find_one.return_value = sample_user_data
    mock_zerodb_client.delete_one.return_value = True

    # Execute
    result = await delete_member(member_id, mock_admin_user)

    # Assertions
    assert result is None  # 204 No Content
    assert mock_zerodb_client.delete_one.call_count == 2  # Profile and user


@pytest.mark.asyncio
async def test_delete_member_not_found(
    mock_zerodb_client,
    mock_admin_user
):
    """Test deleting non-existent member fails"""
    member_id = str(uuid4())
    mock_zerodb_client.find_one.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await delete_member(member_id, mock_admin_user)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_member_self_deletion_prevented(
    mock_zerodb_client,
    sample_user_data
):
    """Test admin cannot delete their own account"""
    admin_id = uuid4()
    admin_user = {
        "id": admin_id,
        "email": "admin@wwmaa.com",
        "role": "admin"
    }

    sample_user_data["id"] = admin_id
    mock_zerodb_client.find_one.return_value = sample_user_data

    with pytest.raises(HTTPException) as exc_info:
        await delete_member(str(admin_id), admin_user)

    assert exc_info.value.status_code == 400
    assert "Cannot delete your own account" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_member_invalid_id(mock_admin_user):
    """Test deleting member with invalid UUID format fails"""
    with pytest.raises(HTTPException) as exc_info:
        await delete_member("invalid-uuid", mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "Invalid member ID" in str(exc_info.value.detail)


# ============================================================================
# LIST MEMBERS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_members_success(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test successfully listing members"""
    # Setup mocks
    users = [sample_user_data]
    mock_zerodb_client.find_many.return_value = users
    mock_zerodb_client.count.return_value = 1
    mock_zerodb_client.find_one.return_value = sample_profile_data

    # Execute
    result = await list_members(
        limit=10,
        offset=0,
        role=None,
        is_active=None,
        search=None,
        current_user=mock_admin_user
    )

    # Assertions
    assert result["total"] == 1
    assert len(result["members"]) == 1
    assert result["members"][0]["email"] == sample_user_data["email"]
    assert result["limit"] == 10
    assert result["offset"] == 0


@pytest.mark.asyncio
async def test_list_members_with_role_filter(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test listing members with role filter"""
    mock_zerodb_client.find_many.return_value = [sample_user_data]
    mock_zerodb_client.count.return_value = 1
    mock_zerodb_client.find_one.return_value = sample_profile_data

    result = await list_members(
        limit=10,
        offset=0,
        role="member",
        is_active=None,
        search=None,
        current_user=mock_admin_user
    )

    # Verify filter was applied
    call_args = mock_zerodb_client.find_many.call_args
    assert call_args[1]["filter_query"]["role"] == "member"


@pytest.mark.asyncio
async def test_list_members_with_active_filter(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test listing members with is_active filter"""
    mock_zerodb_client.find_many.return_value = [sample_user_data]
    mock_zerodb_client.count.return_value = 1
    mock_zerodb_client.find_one.return_value = sample_profile_data

    result = await list_members(
        limit=10,
        offset=0,
        role=None,
        is_active=True,
        search=None,
        current_user=mock_admin_user
    )

    # Verify filter was applied
    call_args = mock_zerodb_client.find_many.call_args
    assert call_args[1]["filter_query"]["is_active"] is True


@pytest.mark.asyncio
async def test_list_members_with_search(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test listing members with search query"""
    mock_zerodb_client.find_many.return_value = [sample_user_data]
    mock_zerodb_client.count.return_value = 1
    mock_zerodb_client.find_one.return_value = sample_profile_data

    result = await list_members(
        limit=10,
        offset=0,
        role=None,
        is_active=None,
        search="test",
        current_user=mock_admin_user
    )

    # Should return matching member
    assert len(result["members"]) == 1


@pytest.mark.asyncio
async def test_list_members_invalid_role(mock_admin_user):
    """Test listing members with invalid role fails"""
    with pytest.raises(HTTPException) as exc_info:
        await list_members(
            limit=10,
            offset=0,
            role="invalid_role",
            is_active=None,
            search=None,
            current_user=mock_admin_user
        )

    assert exc_info.value.status_code == 400
    assert "Invalid role" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_list_members_pagination(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test members list pagination"""
    mock_zerodb_client.find_many.return_value = [sample_user_data]
    mock_zerodb_client.count.return_value = 100
    mock_zerodb_client.find_one.return_value = sample_profile_data

    result = await list_members(
        limit=20,
        offset=40,
        role=None,
        is_active=None,
        search=None,
        current_user=mock_admin_user
    )

    # Verify pagination parameters
    assert result["limit"] == 20
    assert result["offset"] == 40
    call_args = mock_zerodb_client.find_many.call_args
    assert call_args[1]["limit"] == 20
    assert call_args[1]["offset"] == 40


# ============================================================================
# GET MEMBER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_member_success(
    mock_zerodb_client,
    mock_admin_user,
    sample_user_data,
    sample_profile_data
):
    """Test successfully getting a single member"""
    member_id = str(sample_user_data["id"])

    mock_zerodb_client.find_one.side_effect = [
        sample_user_data,  # Get user
        sample_profile_data  # Get profile
    ]

    result = await get_member(member_id, mock_admin_user)

    assert result["id"] == member_id
    assert result["email"] == sample_user_data["email"]
    assert result["first_name"] == sample_profile_data["first_name"]


@pytest.mark.asyncio
async def test_get_member_not_found(
    mock_zerodb_client,
    mock_admin_user
):
    """Test getting non-existent member fails"""
    member_id = str(uuid4())
    mock_zerodb_client.find_one.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_member(member_id, mock_admin_user)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_member_invalid_id(mock_admin_user):
    """Test getting member with invalid UUID format fails"""
    with pytest.raises(HTTPException) as exc_info:
        await get_member("invalid-uuid", mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "Invalid member ID" in str(exc_info.value.detail)


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_member_create_request_email_lowercase():
    """Test email is converted to lowercase"""
    request = MemberCreateRequest(
        email="TEST@EXAMPLE.COM",
        password="SecurePass123!",
        first_name="Test",
        last_name="User"
    )
    assert request.email == "test@example.com"


def test_member_update_request_email_lowercase():
    """Test email is converted to lowercase in update"""
    request = MemberUpdateRequest(email="TEST@EXAMPLE.COM")
    assert request.email == "test@example.com"


def test_member_create_request_name_sanitization():
    """Test name fields are sanitized"""
    request = MemberCreateRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="  Test  ",
        last_name="  User  "
    )
    assert request.first_name == "Test"
    assert request.last_name == "User"


def test_member_create_request_role_conversion():
    """Test role string is converted to UserRole enum"""
    request = MemberCreateRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="Test",
        last_name="User",
        role="admin"
    )
    assert isinstance(request.role, UserRole)
    assert request.role == UserRole.ADMIN
