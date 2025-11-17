"""
Admin Instructor Management Routes

Provides comprehensive instructor management for admin dashboard including:
- Create/edit instructor profiles
- View instructor performance metrics
- Assign instructors to classes
- List and filter instructors

All endpoints require admin authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBError,
    ZeroDBNotFoundError
)
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole, Profile, InstructorPerformance
from backend.utils.validation import (
    validate_phone_number,
    detect_sql_injection,
    strip_html
)
from backend.utils.security import hash_password

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/admin/instructors",
    tags=["admin-instructors"]
)


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CreateInstructorRequest(BaseModel):
    """Request schema for creating a new instructor"""
    model_config = ConfigDict(use_enum_values=True)

    email: EmailStr = Field(..., description="Instructor email address")
    password: str = Field(..., min_length=8, max_length=128, description="Initial password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")

    # Optional profile fields
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=2000, description="Instructor bio")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")

    # Instructor-specific fields
    disciplines: List[str] = Field(default_factory=list, description="Martial arts disciplines")
    certifications: List[str] = Field(default_factory=list, description="Instructor certifications")
    schools_affiliated: List[str] = Field(default_factory=list, description="School affiliations")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format. Use E.164 format (e.g., +12025551234)")
        return v

    @field_validator('first_name', 'last_name', 'city', 'state')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields don't contain SQL injection"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return strip_html(v).strip()

    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v):
        """Sanitize bio field"""
        if v:
            from backend.utils.validation import sanitize_html
            return sanitize_html(v)
        return v


class UpdateInstructorRequest(BaseModel):
    """Request schema for updating instructor profile"""
    model_config = ConfigDict(use_enum_values=True)

    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    bio: Optional[str] = Field(None, max_length=2000, description="Instructor bio")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")

    # Instructor-specific fields
    disciplines: Optional[List[str]] = Field(None, description="Martial arts disciplines")
    certifications: Optional[List[str]] = Field(None, description="Instructor certifications")
    schools_affiliated: Optional[List[str]] = Field(None, description="School affiliations")

    # Status update
    is_active: Optional[bool] = Field(None, description="Instructor active status")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number"""
        if v and not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return v

    @field_validator('first_name', 'last_name', 'city', 'state')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate text fields"""
        if v and detect_sql_injection(v, strict=False):
            raise ValueError("Invalid characters detected")
        return strip_html(v).strip()

    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v):
        """Sanitize bio"""
        if v:
            from backend.utils.validation import sanitize_html
            return sanitize_html(v)
        return v


class AssignInstructorRequest(BaseModel):
    """Request schema for assigning instructor to a class"""
    model_config = ConfigDict(use_enum_values=True)

    instructor_id: str = Field(..., description="Instructor user ID (UUID)")
    replace_existing: bool = Field(default=False, description="Replace existing instructor if any")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class InstructorResponse(BaseModel):
    """Response schema for instructor details"""
    model_config = ConfigDict(use_enum_values=True)

    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    disciplines: List[str] = []
    certifications: List[str] = []
    schools_affiliated: List[str] = []
    is_active: bool
    role: str
    created_at: str
    member_since: Optional[str] = None


class InstructorListResponse(BaseModel):
    """Response schema for instructor list"""
    model_config = ConfigDict(use_enum_values=True)

    instructors: List[InstructorResponse]
    total: int
    page: int
    page_size: int


class PerformanceMetricsResponse(BaseModel):
    """Response schema for instructor performance metrics"""
    model_config = ConfigDict(use_enum_values=True)

    instructor_id: str
    instructor_name: str

    # Teaching metrics
    total_classes_taught: int
    total_students_taught: int
    total_teaching_hours: float
    average_attendance_rate: float

    # Quality metrics
    average_class_rating: float
    total_ratings_received: int
    class_completion_rate: float
    student_retention_rate: float

    # Engagement metrics
    total_chat_messages: int
    total_resources_shared: int

    # Feedback breakdown
    positive_feedback_count: int
    neutral_feedback_count: int
    negative_feedback_count: int

    # Specialties
    disciplines_taught: List[str]
    certifications: List[str]

    # Dates
    last_class_date: Optional[str] = None
    last_review_date: Optional[str] = None
    next_review_date: Optional[str] = None

    # Period
    period_start_date: str
    period_end_date: Optional[str] = None


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for instructor management

    Args:
        current_user: Currently authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_instructor_response(user: Dict[str, Any], profile: Dict[str, Any]) -> InstructorResponse:
    """
    Format instructor data for API response

    Args:
        user: User document from database
        profile: Profile document from database

    Returns:
        InstructorResponse object
    """
    return InstructorResponse(
        id=str(user.get("id")),
        email=user.get("email"),
        first_name=profile.get("first_name", ""),
        last_name=profile.get("last_name", ""),
        phone=profile.get("phone"),
        bio=profile.get("bio"),
        city=profile.get("city"),
        state=profile.get("state"),
        disciplines=profile.get("disciplines", []),
        certifications=profile.get("instructor_certifications", []),
        schools_affiliated=profile.get("schools_affiliated", []),
        is_active=user.get("is_active", True),
        role=user.get("role"),
        created_at=user.get("created_at"),
        member_since=profile.get("member_since")
    )


async def calculate_instructor_performance(instructor_id: UUID) -> Dict[str, Any]:
    """
    Calculate performance metrics for an instructor

    This function aggregates data from training sessions, attendance records,
    and feedback to generate comprehensive performance metrics.

    Args:
        instructor_id: UUID of the instructor

    Returns:
        Dictionary with performance metrics

    Raises:
        ZeroDBError: If database query fails
    """
    db = get_zerodb_client()

    try:
        # Get all training sessions taught by this instructor
        sessions_result = db.find_documents(
            collection="training_sessions",
            filters={"instructor_id": str(instructor_id)},
            limit=10000
        )
        sessions = sessions_result.get("documents", [])

        # Calculate basic metrics
        total_classes_taught = len(sessions)
        total_teaching_hours = sum(
            float(s.get("duration_minutes", 0)) / 60.0
            for s in sessions
        )

        # Get last class date
        last_class_date = None
        if sessions:
            dates = [
                datetime.fromisoformat(s.get("session_date", "1970-01-01T00:00:00").replace("Z", "+00:00"))
                for s in sessions
            ]
            last_class_date = max(dates).isoformat() if dates else None

        # Get attendance records for these sessions
        session_ids = [s.get("id") for s in sessions]
        unique_students = set()
        total_attendance = 0

        for session_id in session_ids:
            attendance_result = db.find_documents(
                collection="session_attendance",
                filters={"session_id": str(session_id)},
                limit=1000
            )
            attendees = attendance_result.get("documents", [])
            total_attendance += len(attendees)
            unique_students.update(a.get("user_id") for a in attendees)

        total_students_taught = len(unique_students)

        # Calculate average attendance rate
        # This is simplified - in production, you'd compare actual vs expected attendance
        total_capacity = sum(s.get("max_participants", 20) for s in sessions)
        average_attendance_rate = (total_attendance / total_capacity * 100) if total_capacity > 0 else 0.0

        # Get chat messages sent by instructor
        chat_messages_result = db.find_documents(
            collection="session_chat_messages",
            filters={"user_id": str(instructor_id)},
            limit=50000
        )
        total_chat_messages = len(chat_messages_result.get("documents", []))

        # Get resources shared by instructor
        resources_result = db.find_documents(
            collection="resources",
            filters={"created_by": str(instructor_id)},
            limit=10000
        )
        total_resources_shared = len(resources_result.get("documents", []))

        # Calculate disciplines taught
        disciplines_taught = list(set(s.get("discipline") for s in sessions if s.get("discipline")))

        # Get or create instructor performance record
        perf_result = db.find_documents(
            collection="instructor_performance",
            filters={"instructor_id": str(instructor_id)},
            limit=1
        )
        existing_perf = perf_result.get("documents", [])

        # For now, use simple metrics
        # In production, you'd track ratings, feedback, etc.
        performance_data = {
            "total_classes_taught": total_classes_taught,
            "total_students_taught": total_students_taught,
            "total_teaching_hours": round(total_teaching_hours, 2),
            "average_attendance_rate": round(average_attendance_rate, 2),
            "average_class_rating": 0.0,  # TODO: Implement rating system
            "total_ratings_received": 0,
            "class_completion_rate": 100.0,  # Simplified - assume all classes completed
            "student_retention_rate": 0.0,  # TODO: Calculate based on repeat attendees
            "total_chat_messages": total_chat_messages,
            "total_resources_shared": total_resources_shared,
            "positive_feedback_count": 0,  # TODO: Implement feedback system
            "neutral_feedback_count": 0,
            "negative_feedback_count": 0,
            "disciplines_taught": disciplines_taught,
            "certifications": [],  # Loaded from profile separately
            "last_class_date": last_class_date,
            "last_review_date": existing_perf[0].get("last_review_date") if existing_perf else None,
            "next_review_date": existing_perf[0].get("next_review_date") if existing_perf else None,
            "period_start_date": datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "period_end_date": None
        }

        return performance_data

    except ZeroDBError as e:
        logger.error(f"Database error calculating instructor performance: {e}")
        raise


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get(
    "",
    response_model=InstructorListResponse,
    summary="List All Instructors",
    description="Get a paginated list of all instructors with optional filtering"
)
async def list_instructors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    current_user: User = Depends(require_admin)
) -> InstructorListResponse:
    """
    List all instructors with pagination and filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        is_active: Filter by active status
        discipline: Filter by martial arts discipline
        current_user: Authenticated admin user

    Returns:
        InstructorListResponse with instructors list and pagination info

    Raises:
        HTTPException: 403 if not admin, 500 if database error
    """
    db = get_zerodb_client()

    try:
        # Build filters
        filters = {"role": "instructor"}
        if is_active is not None:
            filters["is_active"] = is_active

        # Get instructor users
        users_result = db.find_documents(
            collection="users",
            filters=filters,
            limit=10000  # Get all, paginate in memory
        )
        users = users_result.get("documents", [])

        # Get profiles for all instructors
        instructor_responses = []
        for user in users:
            profile_result = db.find_documents(
                collection="profiles",
                filters={"user_id": str(user.get("id"))},
                limit=1
            )
            profiles = profile_result.get("documents", [])
            profile = profiles[0] if profiles else {}

            # Apply discipline filter if specified
            if discipline and discipline not in profile.get("disciplines", []):
                continue

            instructor_responses.append(format_instructor_response(user, profile))

        # Pagination
        total = len(instructor_responses)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_instructors = instructor_responses[start_idx:end_idx]

        return InstructorListResponse(
            instructors=paginated_instructors,
            total=total,
            page=page,
            page_size=page_size
        )

    except ZeroDBError as e:
        logger.error(f"Database error listing instructors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve instructors"
        )


@router.post(
    "",
    response_model=InstructorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Instructor",
    description="Create a new instructor account with profile"
)
async def create_instructor(
    request: CreateInstructorRequest,
    current_user: User = Depends(require_admin)
) -> InstructorResponse:
    """
    Create a new instructor account.

    This endpoint:
    1. Creates a user account with instructor role
    2. Creates an associated profile with instructor details
    3. Initializes performance tracking record

    Args:
        request: Instructor creation request
        current_user: Authenticated admin user

    Returns:
        InstructorResponse with created instructor details

    Raises:
        HTTPException: 400 if email exists, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Check if email already exists
        existing_result = db.find_documents(
            collection="users",
            filters={"email": request.email},
            limit=1
        )
        if existing_result.get("documents"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        password_hash = hash_password(request.password)

        # Create user document
        user_data = {
            "email": request.email,
            "password_hash": password_hash,
            "role": UserRole.INSTRUCTOR.value,
            "is_active": True,
            "is_verified": True,  # Admin-created instructors are pre-verified
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        user_id = db.insert_document(collection="users", document=user_data)
        logger.info(f"Created instructor user: {user_id}")

        # Create profile document
        profile_data = {
            "user_id": str(user_id),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "bio": request.bio,
            "city": request.city,
            "state": request.state,
            "disciplines": request.disciplines,
            "instructor_certifications": request.certifications,
            "schools_affiliated": request.schools_affiliated,
            "member_since": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        profile_id = db.insert_document(collection="profiles", document=profile_data)
        logger.info(f"Created instructor profile: {profile_id}")

        # Update user with profile_id
        db.update_document(
            collection="users",
            document_id=user_id,
            updates={"profile_id": str(profile_id)}
        )

        # Initialize performance tracking
        performance_data = {
            "instructor_id": str(user_id),
            "total_classes_taught": 0,
            "total_students_taught": 0,
            "total_teaching_hours": 0.0,
            "average_attendance_rate": 0.0,
            "average_class_rating": 0.0,
            "total_ratings_received": 0,
            "class_completion_rate": 0.0,
            "student_retention_rate": 0.0,
            "total_chat_messages": 0,
            "total_resources_shared": 0,
            "positive_feedback_count": 0,
            "neutral_feedback_count": 0,
            "negative_feedback_count": 0,
            "disciplines_taught": request.disciplines,
            "certifications": request.certifications,
            "period_start_date": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        db.insert_document(collection="instructor_performance", document=performance_data)
        logger.info(f"Initialized performance tracking for instructor: {user_id}")

        # Get created user and profile for response
        user = db.get_document(collection="users", document_id=user_id)
        profile = db.get_document(collection="profiles", document_id=profile_id)

        return format_instructor_response(user, profile)

    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Database error creating instructor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create instructor"
        )


@router.get(
    "/{instructor_id}",
    response_model=InstructorResponse,
    summary="Get Instructor Details",
    description="Get detailed information about a specific instructor"
)
async def get_instructor(
    instructor_id: str,
    current_user: User = Depends(require_admin)
) -> InstructorResponse:
    """
    Get instructor details by ID.

    Args:
        instructor_id: UUID of the instructor
        current_user: Authenticated admin user

    Returns:
        InstructorResponse with instructor details

    Raises:
        HTTPException: 404 if not found, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Get user
        user = db.get_document(collection="users", document_id=UUID(instructor_id))

        # Verify role
        if user.get("role") != UserRole.INSTRUCTOR.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )

        # Get profile
        profile_result = db.find_documents(
            collection="profiles",
            filters={"user_id": instructor_id},
            limit=1
        )
        profiles = profile_result.get("documents", [])
        profile = profiles[0] if profiles else {}

        return format_instructor_response(user, profile)

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid instructor ID format"
        )
    except ZeroDBError as e:
        logger.error(f"Database error getting instructor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve instructor"
        )


@router.put(
    "/{instructor_id}",
    response_model=InstructorResponse,
    summary="Update Instructor Profile",
    description="Update instructor profile information"
)
async def update_instructor(
    instructor_id: str,
    request: UpdateInstructorRequest,
    current_user: User = Depends(require_admin)
) -> InstructorResponse:
    """
    Update instructor profile.

    Args:
        instructor_id: UUID of the instructor
        request: Update request with fields to change
        current_user: Authenticated admin user

    Returns:
        InstructorResponse with updated instructor details

    Raises:
        HTTPException: 404 if not found, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Get user to verify exists and is instructor
        user = db.get_document(collection="users", document_id=UUID(instructor_id))

        if user.get("role") != UserRole.INSTRUCTOR.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )

        # Update user if is_active changed
        if request.is_active is not None:
            db.update_document(
                collection="users",
                document_id=UUID(instructor_id),
                updates={
                    "is_active": request.is_active,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

        # Get profile
        profile_result = db.find_documents(
            collection="profiles",
            filters={"user_id": instructor_id},
            limit=1
        )
        profiles = profile_result.get("documents", [])

        if not profiles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor profile not found"
            )

        profile = profiles[0]
        profile_id = UUID(profile.get("id"))

        # Build profile updates
        profile_updates = {"updated_at": datetime.utcnow().isoformat()}

        if request.first_name is not None:
            profile_updates["first_name"] = request.first_name
        if request.last_name is not None:
            profile_updates["last_name"] = request.last_name
        if request.phone is not None:
            profile_updates["phone"] = request.phone
        if request.bio is not None:
            profile_updates["bio"] = request.bio
        if request.city is not None:
            profile_updates["city"] = request.city
        if request.state is not None:
            profile_updates["state"] = request.state
        if request.disciplines is not None:
            profile_updates["disciplines"] = request.disciplines
        if request.certifications is not None:
            profile_updates["instructor_certifications"] = request.certifications
        if request.schools_affiliated is not None:
            profile_updates["schools_affiliated"] = request.schools_affiliated

        # Update profile
        db.update_document(
            collection="profiles",
            document_id=profile_id,
            updates=profile_updates
        )

        logger.info(f"Updated instructor profile: {instructor_id}")

        # Get updated documents
        updated_user = db.get_document(collection="users", document_id=UUID(instructor_id))
        updated_profile = db.get_document(collection="profiles", document_id=profile_id)

        return format_instructor_response(updated_user, updated_profile)

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid instructor ID format"
        )
    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Database error updating instructor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update instructor"
        )


@router.get(
    "/{instructor_id}/performance",
    response_model=PerformanceMetricsResponse,
    summary="Get Instructor Performance Metrics",
    description="Get comprehensive performance analytics for an instructor"
)
async def get_instructor_performance(
    instructor_id: str,
    current_user: User = Depends(require_admin)
) -> PerformanceMetricsResponse:
    """
    Get instructor performance metrics.

    This endpoint calculates and returns:
    - Classes taught and student counts
    - Attendance and completion rates
    - Ratings and feedback statistics
    - Engagement metrics (chat, resources)
    - Specialties and certifications

    Args:
        instructor_id: UUID of the instructor
        current_user: Authenticated admin user

    Returns:
        PerformanceMetricsResponse with all metrics

    Raises:
        HTTPException: 404 if not found, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Verify instructor exists
        user = db.get_document(collection="users", document_id=UUID(instructor_id))

        if user.get("role") != UserRole.INSTRUCTOR.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )

        # Get profile for name and certifications
        profile_result = db.find_documents(
            collection="profiles",
            filters={"user_id": instructor_id},
            limit=1
        )
        profiles = profile_result.get("documents", [])
        profile = profiles[0] if profiles else {}

        # Calculate performance metrics
        performance_data = await calculate_instructor_performance(UUID(instructor_id))

        # Add certifications from profile
        performance_data["certifications"] = profile.get("instructor_certifications", [])

        # Build response
        instructor_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
        if not instructor_name:
            instructor_name = user.get("email")

        return PerformanceMetricsResponse(
            instructor_id=instructor_id,
            instructor_name=instructor_name,
            **performance_data
        )

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid instructor ID format"
        )
    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Database error getting instructor performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.post(
    "/classes/{class_id}/assign",
    summary="Assign Instructor to Class",
    description="Assign an instructor to a training session or event"
)
async def assign_instructor_to_class(
    class_id: str,
    request: AssignInstructorRequest,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Assign an instructor to a class (training session or event).

    This endpoint can assign instructors to:
    - Training sessions (updates instructor_id)
    - Events (adds to instructors list)

    Args:
        class_id: UUID of the training session or event
        request: Assignment request with instructor ID
        current_user: Authenticated admin user

    Returns:
        Success message with assignment details

    Raises:
        HTTPException: 400 if invalid, 404 if not found, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Verify instructor exists and has instructor role
        try:
            instructor = db.get_document(
                collection="users",
                document_id=UUID(request.instructor_id)
            )
        except ZeroDBNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instructor not found"
            )

        if instructor.get("role") != UserRole.INSTRUCTOR.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an instructor"
            )

        # Try to find as training session first
        try:
            session = db.get_document(
                collection="training_sessions",
                document_id=UUID(class_id)
            )

            # Check if session already has an instructor
            current_instructor_id = session.get("instructor_id")
            if current_instructor_id and not request.replace_existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Training session already has an instructor. Set replace_existing=true to replace."
                )

            # Update session with new instructor
            db.update_document(
                collection="training_sessions",
                document_id=UUID(class_id),
                updates={
                    "instructor_id": request.instructor_id,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Assigned instructor {request.instructor_id} to training session {class_id}")

            return {
                "message": "Instructor assigned to training session successfully",
                "class_type": "training_session",
                "class_id": class_id,
                "instructor_id": request.instructor_id,
                "replaced": current_instructor_id is not None
            }

        except ZeroDBNotFoundError:
            # Not a training session, try event
            pass

        # Try to find as event
        try:
            event = db.get_document(
                collection="events",
                document_id=UUID(class_id)
            )

            # Get current instructors list
            instructors = event.get("instructors", [])

            # Check if already assigned
            if request.instructor_id in instructors:
                return {
                    "message": "Instructor already assigned to this event",
                    "class_type": "event",
                    "class_id": class_id,
                    "instructor_id": request.instructor_id
                }

            # Add instructor to list
            instructors.append(request.instructor_id)

            db.update_document(
                collection="events",
                document_id=UUID(class_id),
                updates={
                    "instructors": instructors,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"Assigned instructor {request.instructor_id} to event {class_id}")

            return {
                "message": "Instructor assigned to event successfully",
                "class_type": "event",
                "class_id": class_id,
                "instructor_id": request.instructor_id,
                "total_instructors": len(instructors)
            }

        except ZeroDBNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found (not a training session or event)"
            )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Database error assigning instructor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign instructor"
        )


@router.delete(
    "/classes/{class_id}/instructors/{instructor_id}",
    summary="Remove Instructor from Class",
    description="Remove an instructor assignment from a training session or event"
)
async def remove_instructor_from_class(
    class_id: str,
    instructor_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Remove an instructor from a class.

    Args:
        class_id: UUID of the training session or event
        instructor_id: UUID of the instructor to remove
        current_user: Authenticated admin user

    Returns:
        Success message

    Raises:
        HTTPException: 400 if invalid, 404 if not found, 403 if not admin, 500 if error
    """
    db = get_zerodb_client()

    try:
        # Try training session first
        try:
            session = db.get_document(
                collection="training_sessions",
                document_id=UUID(class_id)
            )

            if session.get("instructor_id") != instructor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instructor is not assigned to this training session"
                )

            # Remove instructor (set to None or empty)
            db.update_document(
                collection="training_sessions",
                document_id=UUID(class_id),
                updates={
                    "instructor_id": None,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            return {
                "message": "Instructor removed from training session successfully",
                "class_type": "training_session"
            }

        except ZeroDBNotFoundError:
            pass

        # Try event
        try:
            event = db.get_document(
                collection="events",
                document_id=UUID(class_id)
            )

            instructors = event.get("instructors", [])

            if instructor_id not in instructors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instructor is not assigned to this event"
                )

            # Remove instructor from list
            instructors.remove(instructor_id)

            db.update_document(
                collection="events",
                document_id=UUID(class_id),
                updates={
                    "instructors": instructors,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )

            return {
                "message": "Instructor removed from event successfully",
                "class_type": "event"
            }

        except ZeroDBNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except HTTPException:
        raise
    except ZeroDBError as e:
        logger.error(f"Database error removing instructor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove instructor"
        )
