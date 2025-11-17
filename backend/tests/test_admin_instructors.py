"""
Unit Tests for Admin Instructor Management Routes

Tests all instructor management endpoints including:
- Creating instructors
- Listing instructors with pagination and filters
- Getting instructor details
- Updating instructor profiles
- Getting performance metrics
- Assigning instructors to classes
- Removing instructors from classes

All tests use mocked ZeroDB client and authentication.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from backend.routes.admin.instructors import (
    router,
    list_instructors,
    create_instructor,
    get_instructor,
    update_instructor,
    get_instructor_performance,
    assign_instructor_to_class,
    remove_instructor_from_class,
    calculate_instructor_performance,
    format_instructor_response,
    CreateInstructorRequest,
    UpdateInstructorRequest,
    AssignInstructorRequest
)
from backend.models.schemas import User, UserRole


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication"""
    return User(
        id=uuid4(),
        email="admin@wwmaa.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_instructor_user():
    """Mock instructor user"""
    instructor_id = uuid4()
    return {
        "id": str(instructor_id),
        "email": "instructor@wwmaa.com",
        "password_hash": "hashed",
        "role": "instructor",
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_instructor_profile():
    """Mock instructor profile"""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+12025551234",
        "bio": "Experienced martial arts instructor",
        "city": "Los Angeles",
        "state": "CA",
        "disciplines": ["Karate", "Judo"],
        "instructor_certifications": ["Black Belt 3rd Dan", "Certified Instructor"],
        "schools_affiliated": ["WWMAA Dojo"],
        "member_since": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_db_client():
    """Mock ZeroDB client"""
    return MagicMock()


# ============================================================================
# TEST LIST INSTRUCTORS
# ============================================================================

@pytest.mark.asyncio
async def test_list_instructors_success(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test successfully listing instructors"""
    # Setup mock DB responses
    mock_db_client.find_documents.side_effect = [
        {"documents": [mock_instructor_user]},  # users query
        {"documents": [mock_instructor_profile]}  # profile query
    ]

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await list_instructors(
            page=1,
            page_size=20,
            is_active=None,
            discipline=None,
            current_user=mock_admin_user
        )

    assert result.total == 1
    assert len(result.instructors) == 1
    assert result.instructors[0].email == "instructor@wwmaa.com"
    assert result.instructors[0].first_name == "John"
    assert result.page == 1


@pytest.mark.asyncio
async def test_list_instructors_with_discipline_filter(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test listing instructors filtered by discipline"""
    mock_db_client.find_documents.side_effect = [
        {"documents": [mock_instructor_user]},
        {"documents": [mock_instructor_profile]}
    ]

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await list_instructors(
            page=1,
            page_size=20,
            is_active=None,
            discipline="Karate",
            current_user=mock_admin_user
        )

    assert result.total == 1
    assert "Karate" in result.instructors[0].disciplines


@pytest.mark.asyncio
async def test_list_instructors_pagination(mock_admin_user, mock_db_client):
    """Test instructor list pagination"""
    # Create 25 mock instructors
    users = []
    profiles = []
    for i in range(25):
        user_id = str(uuid4())
        users.append({
            "id": user_id,
            "email": f"instructor{i}@wwmaa.com",
            "role": "instructor",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        })
        profiles.append({
            "id": str(uuid4()),
            "user_id": user_id,
            "first_name": f"Instructor{i}",
            "last_name": "Test",
            "disciplines": ["Karate"],
            "instructor_certifications": [],
            "schools_affiliated": []
        })

    # Mock DB to return users once, then profiles for each user
    find_calls = [{"documents": users}]
    for profile in profiles:
        find_calls.append({"documents": [profile]})

    mock_db_client.find_documents.side_effect = find_calls

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        # Get page 1
        result_page1 = await list_instructors(
            page=1,
            page_size=20,
            is_active=None,
            discipline=None,
            current_user=mock_admin_user
        )

    assert result_page1.total == 25
    assert len(result_page1.instructors) == 20
    assert result_page1.page == 1


# ============================================================================
# TEST CREATE INSTRUCTOR
# ============================================================================

@pytest.mark.asyncio
async def test_create_instructor_success(mock_admin_user, mock_db_client):
    """Test successfully creating a new instructor"""
    new_instructor_id = uuid4()
    new_profile_id = uuid4()

    # Setup mock responses
    mock_db_client.find_documents.return_value = {"documents": []}  # Email not exists
    mock_db_client.insert_document.side_effect = [new_instructor_id, new_profile_id, uuid4()]
    mock_db_client.get_document.side_effect = [
        {
            "id": str(new_instructor_id),
            "email": "new.instructor@wwmaa.com",
            "role": "instructor",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": str(new_profile_id),
            "user_id": str(new_instructor_id),
            "first_name": "Jane",
            "last_name": "Smith",
            "disciplines": ["Taekwondo"],
            "instructor_certifications": ["Black Belt"],
            "schools_affiliated": []
        }
    ]

    request = CreateInstructorRequest(
        email="new.instructor@wwmaa.com",
        password="SecurePass123!",
        first_name="Jane",
        last_name="Smith",
        disciplines=["Taekwondo"],
        certifications=["Black Belt"]
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client), \
         patch('backend.routes.admin.instructors.hash_password', return_value="hashed_password"):
        result = await create_instructor(request, mock_admin_user)

    assert result.email == "new.instructor@wwmaa.com"
    assert result.first_name == "Jane"
    assert result.role == "instructor"
    assert mock_db_client.insert_document.call_count == 3  # user, profile, performance


@pytest.mark.asyncio
async def test_create_instructor_email_exists(mock_admin_user, mock_db_client):
    """Test creating instructor with existing email fails"""
    # Email already exists
    mock_db_client.find_documents.return_value = {
        "documents": [{"email": "existing@wwmaa.com"}]
    }

    request = CreateInstructorRequest(
        email="existing@wwmaa.com",
        password="SecurePass123!",
        first_name="Jane",
        last_name="Smith"
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        with pytest.raises(HTTPException) as exc_info:
            await create_instructor(request, mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail


# ============================================================================
# TEST GET INSTRUCTOR
# ============================================================================

@pytest.mark.asyncio
async def test_get_instructor_success(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test successfully getting instructor details"""
    instructor_id = mock_instructor_user["id"]

    mock_db_client.get_document.return_value = mock_instructor_user
    mock_db_client.find_documents.return_value = {"documents": [mock_instructor_profile]}

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await get_instructor(instructor_id, mock_admin_user)

    assert result.id == instructor_id
    assert result.email == "instructor@wwmaa.com"
    assert result.first_name == "John"


@pytest.mark.asyncio
async def test_get_instructor_not_found(mock_admin_user, mock_db_client):
    """Test getting non-existent instructor"""
    from backend.services.zerodb_service import ZeroDBNotFoundError

    mock_db_client.get_document.side_effect = ZeroDBNotFoundError("Not found")

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        with pytest.raises(HTTPException) as exc_info:
            await get_instructor(str(uuid4()), mock_admin_user)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_instructor_not_instructor_role(mock_admin_user, mock_db_client):
    """Test getting user who is not instructor fails"""
    user_id = str(uuid4())
    mock_db_client.get_document.return_value = {
        "id": user_id,
        "email": "member@wwmaa.com",
        "role": "member"  # Not instructor
    }

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        with pytest.raises(HTTPException) as exc_info:
            await get_instructor(user_id, mock_admin_user)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


# ============================================================================
# TEST UPDATE INSTRUCTOR
# ============================================================================

@pytest.mark.asyncio
async def test_update_instructor_success(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test successfully updating instructor profile"""
    instructor_id = mock_instructor_user["id"]
    profile_id = mock_instructor_profile["id"]

    mock_db_client.get_document.side_effect = [
        mock_instructor_user,  # Get user
        {**mock_instructor_user, "updated_at": datetime.utcnow().isoformat()},  # Updated user
        {**mock_instructor_profile, "first_name": "Updated", "updated_at": datetime.utcnow().isoformat()}  # Updated profile
    ]
    mock_db_client.find_documents.return_value = {"documents": [mock_instructor_profile]}

    request = UpdateInstructorRequest(
        first_name="Updated",
        bio="Updated bio"
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await update_instructor(instructor_id, request, mock_admin_user)

    assert result.first_name == "Updated"
    assert mock_db_client.update_document.call_count >= 1


@pytest.mark.asyncio
async def test_update_instructor_is_active(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test updating instructor active status"""
    instructor_id = mock_instructor_user["id"]

    mock_db_client.get_document.side_effect = [
        mock_instructor_user,
        {**mock_instructor_user, "is_active": False},
        mock_instructor_profile
    ]
    mock_db_client.find_documents.return_value = {"documents": [mock_instructor_profile]}

    request = UpdateInstructorRequest(is_active=False)

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await update_instructor(instructor_id, request, mock_admin_user)

    # Verify update_document was called with is_active
    calls = mock_db_client.update_document.call_args_list
    user_update_call = calls[0]
    assert user_update_call[1]['updates']['is_active'] == False


# ============================================================================
# TEST INSTRUCTOR PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_instructor_performance(mock_db_client):
    """Test calculating instructor performance metrics"""
    instructor_id = uuid4()

    # Mock training sessions
    sessions = [
        {
            "id": str(uuid4()),
            "instructor_id": str(instructor_id),
            "duration_minutes": 60,
            "session_date": datetime.utcnow().isoformat(),
            "discipline": "Karate",
            "max_participants": 20
        },
        {
            "id": str(uuid4()),
            "instructor_id": str(instructor_id),
            "duration_minutes": 90,
            "session_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "discipline": "Judo",
            "max_participants": 15
        }
    ]

    # Mock attendance - use same user_ids across sessions to test unique count
    user1_id = str(uuid4())
    user2_id = str(uuid4())
    user3_id = str(uuid4())

    session1_attendance = [
        {"id": str(uuid4()), "session_id": sessions[0]["id"], "user_id": user1_id},
        {"id": str(uuid4()), "session_id": sessions[0]["id"], "user_id": user2_id}
    ]
    session2_attendance = [
        {"id": str(uuid4()), "session_id": sessions[1]["id"], "user_id": user1_id},  # Same as session 1
        {"id": str(uuid4()), "session_id": sessions[1]["id"], "user_id": user2_id},  # Same as session 1
        {"id": str(uuid4()), "session_id": sessions[1]["id"], "user_id": user3_id}   # New student
    ]

    # Setup mock responses
    find_calls = [
        {"documents": sessions},  # Sessions
        {"documents": session1_attendance},  # Session 1 attendance
        {"documents": session2_attendance},  # Session 2 attendance
        {"documents": []},  # Chat messages
        {"documents": []},  # Resources
        {"documents": []}   # Existing performance record
    ]
    mock_db_client.find_documents.side_effect = find_calls

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await calculate_instructor_performance(instructor_id)

    assert result["total_classes_taught"] == 2
    assert result["total_teaching_hours"] == 2.5  # 1.0 + 1.5 hours
    assert result["total_students_taught"] == 3  # Unique students
    assert "Karate" in result["disciplines_taught"]
    assert "Judo" in result["disciplines_taught"]


@pytest.mark.asyncio
async def test_get_instructor_performance_success(mock_admin_user, mock_instructor_user, mock_instructor_profile, mock_db_client):
    """Test getting instructor performance metrics"""
    instructor_id = mock_instructor_user["id"]

    mock_db_client.get_document.return_value = mock_instructor_user

    # Mock find_documents for profile and performance calculation
    find_calls = [
        {"documents": [mock_instructor_profile]},  # Profile
        {"documents": []},  # Sessions for performance calc
        {"documents": []},  # Chat messages
        {"documents": []},  # Resources
        {"documents": []}   # Existing performance
    ]
    mock_db_client.find_documents.side_effect = find_calls

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await get_instructor_performance(instructor_id, mock_admin_user)

    assert result.instructor_id == instructor_id
    assert result.instructor_name == "John Doe"
    assert result.total_classes_taught == 0  # No sessions in mock


# ============================================================================
# TEST ASSIGN INSTRUCTOR TO CLASS
# ============================================================================

@pytest.mark.asyncio
async def test_assign_instructor_to_training_session(mock_admin_user, mock_instructor_user, mock_db_client):
    """Test assigning instructor to training session"""
    instructor_id = mock_instructor_user["id"]
    session_id = str(uuid4())

    # Mock instructor verification
    mock_db_client.get_document.side_effect = [
        mock_instructor_user,  # Verify instructor exists
        {  # Get training session
            "id": session_id,
            "instructor_id": None,
            "title": "Test Session"
        }
    ]

    request = AssignInstructorRequest(
        instructor_id=instructor_id,
        replace_existing=False
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await assign_instructor_to_class(session_id, request, mock_admin_user)

    assert result["message"] == "Instructor assigned to training session successfully"
    assert result["class_type"] == "training_session"
    assert result["instructor_id"] == instructor_id
    assert mock_db_client.update_document.called


@pytest.mark.asyncio
async def test_assign_instructor_to_event(mock_admin_user, mock_instructor_user, mock_db_client):
    """Test assigning instructor to event"""
    from backend.services.zerodb_service import ZeroDBNotFoundError

    instructor_id = mock_instructor_user["id"]
    event_id = str(uuid4())

    # Mock responses
    mock_db_client.get_document.side_effect = [
        mock_instructor_user,  # Verify instructor
        ZeroDBNotFoundError("Not found"),  # Not a training session
        {  # Get event
            "id": event_id,
            "title": "Test Event",
            "instructors": []
        }
    ]

    request = AssignInstructorRequest(instructor_id=instructor_id)

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await assign_instructor_to_class(event_id, request, mock_admin_user)

    assert result["class_type"] == "event"
    assert result["total_instructors"] == 1


@pytest.mark.asyncio
async def test_assign_instructor_replace_existing(mock_admin_user, mock_instructor_user, mock_db_client):
    """Test replacing existing instructor in training session"""
    instructor_id = mock_instructor_user["id"]
    session_id = str(uuid4())
    existing_instructor_id = str(uuid4())

    mock_db_client.get_document.side_effect = [
        mock_instructor_user,
        {
            "id": session_id,
            "instructor_id": existing_instructor_id,
            "title": "Test Session"
        }
    ]

    request = AssignInstructorRequest(
        instructor_id=instructor_id,
        replace_existing=True
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await assign_instructor_to_class(session_id, request, mock_admin_user)

    assert result["replaced"] == True


@pytest.mark.asyncio
async def test_assign_instructor_already_assigned_without_replace(mock_admin_user, mock_instructor_user, mock_db_client):
    """Test assigning when instructor already assigned fails without replace flag"""
    instructor_id = mock_instructor_user["id"]
    session_id = str(uuid4())
    existing_instructor_id = str(uuid4())

    mock_db_client.get_document.side_effect = [
        mock_instructor_user,
        {
            "id": session_id,
            "instructor_id": existing_instructor_id
        }
    ]

    request = AssignInstructorRequest(
        instructor_id=instructor_id,
        replace_existing=False
    )

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        with pytest.raises(HTTPException) as exc_info:
            await assign_instructor_to_class(session_id, request, mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "already has an instructor" in exc_info.value.detail


@pytest.mark.asyncio
async def test_assign_non_instructor_fails(mock_admin_user, mock_db_client):
    """Test assigning user who is not instructor fails"""
    user_id = str(uuid4())
    session_id = str(uuid4())

    mock_db_client.get_document.return_value = {
        "id": user_id,
        "role": "member"  # Not instructor
    }

    request = AssignInstructorRequest(instructor_id=user_id)

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        with pytest.raises(HTTPException) as exc_info:
            await assign_instructor_to_class(session_id, request, mock_admin_user)

    assert exc_info.value.status_code == 400
    assert "not an instructor" in exc_info.value.detail


# ============================================================================
# TEST REMOVE INSTRUCTOR FROM CLASS
# ============================================================================

@pytest.mark.asyncio
async def test_remove_instructor_from_training_session(mock_admin_user, mock_db_client):
    """Test removing instructor from training session"""
    instructor_id = str(uuid4())
    session_id = str(uuid4())

    mock_db_client.get_document.return_value = {
        "id": session_id,
        "instructor_id": instructor_id
    }

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await remove_instructor_from_class(session_id, instructor_id, mock_admin_user)

    assert result["class_type"] == "training_session"
    assert mock_db_client.update_document.called


@pytest.mark.asyncio
async def test_remove_instructor_from_event(mock_admin_user, mock_db_client):
    """Test removing instructor from event"""
    from backend.services.zerodb_service import ZeroDBNotFoundError

    instructor_id = str(uuid4())
    event_id = str(uuid4())

    mock_db_client.get_document.side_effect = [
        ZeroDBNotFoundError("Not found"),  # Not training session
        {
            "id": event_id,
            "instructors": [instructor_id, str(uuid4())]
        }
    ]

    with patch('backend.routes.admin.instructors.get_zerodb_client', return_value=mock_db_client):
        result = await remove_instructor_from_class(event_id, instructor_id, mock_admin_user)

    assert result["class_type"] == "event"


# ============================================================================
# TEST HELPER FUNCTIONS
# ============================================================================

def test_format_instructor_response(mock_instructor_user, mock_instructor_profile):
    """Test formatting instructor response"""
    result = format_instructor_response(mock_instructor_user, mock_instructor_profile)

    assert result.id == mock_instructor_user["id"]
    assert result.email == mock_instructor_user["email"]
    assert result.first_name == mock_instructor_profile["first_name"]
    assert result.last_name == mock_instructor_profile["last_name"]
    assert result.disciplines == mock_instructor_profile["disciplines"]
    assert result.certifications == mock_instructor_profile["instructor_certifications"]


# ============================================================================
# TEST AUTHORIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_non_admin_cannot_access_endpoints(mock_db_client):
    """Test that non-admin users cannot access instructor management"""
    from backend.routes.admin.instructors import require_admin

    non_admin_user = User(
        id=uuid4(),
        email="member@wwmaa.com",
        password_hash="hashed",
        role=UserRole.MEMBER,  # Not admin
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    with pytest.raises(HTTPException) as exc_info:
        require_admin(non_admin_user)

    assert exc_info.value.status_code == 403
    assert "Admin access required" in exc_info.value.detail


# ============================================================================
# TEST VALIDATION
# ============================================================================

def test_create_instructor_request_validation():
    """Test CreateInstructorRequest validation"""
    # Valid request
    valid_request = CreateInstructorRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="John",
        last_name="Doe"
    )
    assert valid_request.email == "test@example.com"

    # Email lowercase conversion
    request_uppercase = CreateInstructorRequest(
        email="TEST@EXAMPLE.COM",
        password="SecurePass123!",
        first_name="John",
        last_name="Doe"
    )
    assert request_uppercase.email == "test@example.com"


def test_update_instructor_request_validation():
    """Test UpdateInstructorRequest validation"""
    # All fields optional
    request = UpdateInstructorRequest()
    assert request.first_name is None

    # Partial update
    request = UpdateInstructorRequest(
        first_name="Updated",
        bio="New bio"
    )
    assert request.first_name == "Updated"
    assert request.last_name is None


def test_assign_instructor_request_validation():
    """Test AssignInstructorRequest validation"""
    request = AssignInstructorRequest(instructor_id=str(uuid4()))
    assert request.replace_existing == False

    request_replace = AssignInstructorRequest(
        instructor_id=str(uuid4()),
        replace_existing=True
    )
    assert request_replace.replace_existing == True
