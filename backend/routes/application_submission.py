"""
Application Submission Routes for WWMAA Backend (US-015)

Provides membership application submission and management endpoints.
Implements secure file upload, validation, email notifications, and role-based access control.

Key Features:
- Public application submission (no auth required)
- File upload to ZeroDB Object Storage (PDF, JPG, PNG certificates)
- Email confirmations to applicants and board notifications
- Duplicate application detection
- Draft application management (authenticated users)
- Board member/admin application listing and viewing

Endpoints:
- POST /api/applications - Submit new application (public)
- GET /api/applications/:id - Get application by ID (owner/board/admin)
- GET /api/applications - List applications (board/admin only)
- PATCH /api/applications/:id - Update draft application (owner only)
- DELETE /api/applications/:id - Delete draft application (owner only)
"""

import logging
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4, UUID
import os
import tempfile

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBValidationError,
    ZeroDBError,
    ZeroDBNotFoundError
)
from backend.services.email_service import get_email_service, EmailSendError
from backend.config import get_settings
from backend.middleware.auth_middleware import get_optional_user, CurrentUser, RoleChecker
from backend.middleware.permissions import (
    can_view_application,
    can_edit_application,
    require_permission
)
from backend.models.schemas import ApplicationStatus

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/application-submissions", tags=["application-submissions"])

# Settings
settings = get_settings()

# File upload constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_FILE_TYPES = {
    'application/pdf': ['.pdf'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png']
}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ApplicationSubmitRequest(BaseModel):
    """Application submission request (no auth required)"""
    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (ISO format)")

    # Address
    address_line1: Optional[str] = Field(None, max_length=200, description="Street address")
    address_line2: Optional[str] = Field(None, max_length=200, description="Apt/Suite")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP code")
    country: str = Field(default="USA", max_length=100, description="Country")

    # Martial Arts Background (REQUIRED)
    disciplines: List[str] = Field(..., min_items=1, description="Martial arts disciplines")
    experience_years: int = Field(..., ge=0, le=100, description="Years of experience")
    current_rank: Optional[str] = Field(None, max_length=50, description="Current rank/belt")
    school_affiliation: Optional[str] = Field(None, max_length=200, description="School affiliation")
    instructor_name: Optional[str] = Field(None, max_length=200, description="Instructor name")

    # Application Details (REQUIRED)
    motivation: str = Field(..., min_length=10, max_length=2000, description="Why joining WWMAA")
    goals: Optional[str] = Field(None, max_length=2000, description="Training goals")
    referral_source: Optional[str] = Field(None, max_length=200, description="How they heard about WWMAA")

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

    @field_validator('disciplines')
    @classmethod
    def validate_disciplines(cls, v):
        """Ensure at least one discipline"""
        if not v or len(v) == 0:
            raise ValueError("At least one martial arts discipline is required")
        return v


class ApplicationUpdateRequest(BaseModel):
    """Application update request (for draft applications)"""
    # Personal Information (all optional for updates)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[str] = Field(None, description="Date of birth (ISO format)")

    # Address
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)

    # Martial Arts Background
    disciplines: Optional[List[str]] = Field(None, description="Martial arts disciplines")
    experience_years: Optional[int] = Field(None, ge=0, le=100)
    current_rank: Optional[str] = Field(None, max_length=50)
    school_affiliation: Optional[str] = Field(None, max_length=200)
    instructor_name: Optional[str] = Field(None, max_length=200)

    # Application Details
    motivation: Optional[str] = Field(None, max_length=2000)
    goals: Optional[str] = Field(None, max_length=2000)
    referral_source: Optional[str] = Field(None, max_length=200)


class ApplicationResponse(BaseModel):
    """Application response"""
    id: str
    user_id: Optional[str] = None
    status: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str
    disciplines: List[str]
    experience_years: Optional[int] = None
    current_rank: Optional[str] = None
    school_affiliation: Optional[str] = None
    instructor_name: Optional[str] = None
    motivation: Optional[str] = None
    goals: Optional[str] = None
    referral_source: Optional[str] = None
    certificate_files: List[Dict[str, str]] = Field(default_factory=list, description="Uploaded certificate files")
    submitted_at: Optional[str] = None
    created_at: str
    updated_at: str


class ApplicationListResponse(BaseModel):
    """Application list response"""
    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int


class ApplicationSubmitResponse(BaseModel):
    """Application submission response"""
    message: str
    application_id: str
    status: str
    confirmation_sent: bool


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_file_upload(file: UploadFile) -> None:
    """
    Validate uploaded file type and size

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If file validation fails
    """
    # Check file type
    content_type = file.content_type
    if content_type not in ALLOWED_FILE_TYPES:
        allowed = ", ".join(ALLOWED_FILE_TYPES.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {allowed}"
        )

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FILE_TYPES[content_type]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension {file_ext} does not match content type {content_type}"
        )


async def upload_certificate_file(file: UploadFile, application_id: str) -> Dict[str, str]:
    """
    Upload certificate file to ZeroDB Object Storage

    Args:
        file: Uploaded file
        application_id: Application ID for organizing files

    Returns:
        Dictionary with file metadata (id, filename, url, size)

    Raises:
        HTTPException: If upload fails
    """
    db_client = get_zerodb_client()

    try:
        # Validate file
        validate_file_upload(file)

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Check file size
        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {max_mb}MB"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Generate unique filename
            file_id = str(uuid4())
            file_ext = os.path.splitext(file.filename)[1]
            object_name = f"applications/{application_id}/{file_id}{file_ext}"

            # Upload to ZeroDB Object Storage
            logger.info(f"Uploading certificate file: {object_name}")
            upload_result = db_client.upload_object(
                file_path=tmp_path,
                object_name=object_name,
                metadata={
                    "application_id": application_id,
                    "original_filename": file.filename,
                    "content_type": file.content_type,
                    "uploaded_at": datetime.utcnow().isoformat()
                },
                content_type=file.content_type
            )

            logger.info(f"Certificate file uploaded successfully: {object_name}")

            return {
                "id": file_id,
                "filename": file.filename,
                "object_name": object_name,
                "url": upload_result.get("url", ""),
                "size": file_size,
                "content_type": file.content_type
            }

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload certificate file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


async def send_application_confirmation_email(email: str, name: str, application_id: str) -> None:
    """
    Send confirmation email to applicant

    Args:
        email: Applicant email
        name: Applicant name
        application_id: Application ID
    """
    email_service = get_email_service()

    subject = "WWMAA Membership Application Received"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #8B0000; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
            .info-box {{ background-color: #e8f4f8; border-left: 4px solid #0066cc; padding: 15px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Application Received</h1>
        </div>
        <div class="content">
            <h2>Hello, {name}!</h2>
            <p>Thank you for submitting your membership application to the Women's Martial Arts Association of America.</p>

            <div class="info-box">
                <strong>Application ID:</strong> {application_id}<br>
                <strong>Status:</strong> Submitted - Pending Review
            </div>

            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Our Board members will review your application</li>
                <li>Review typically takes 3-5 business days</li>
                <li>You will receive an email notification once a decision is made</li>
                <li>If approved, you'll receive instructions for membership activation</li>
            </ul>

            <p>If you have any questions about your application, please don't hesitate to contact us.</p>

            <p>We appreciate your interest in joining WWMAA!</p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Application Received

    Hello, {name}!

    Thank you for submitting your membership application to the Women's Martial Arts Association of America.

    Application ID: {application_id}
    Status: Submitted - Pending Review

    What happens next?
    - Our Board members will review your application
    - Review typically takes 3-5 business days
    - You will receive an email notification once a decision is made
    - If approved, you'll receive instructions for membership activation

    If you have any questions about your application, please don't hesitate to contact us.

    We appreciate your interest in joining WWMAA!

    ---
    Women's Martial Arts Association of America
    """

    try:
        email_service._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="application-confirmation"
        )
        logger.info(f"Application confirmation email sent to {email}")
    except EmailSendError as e:
        logger.error(f"Failed to send application confirmation email: {e}")
        # Don't fail the request if email fails


async def send_board_notification_email(application_id: str, applicant_name: str, applicant_email: str) -> None:
    """
    Send notification email to board members about new application

    Args:
        application_id: Application ID
        applicant_name: Applicant name
        applicant_email: Applicant email
    """
    db_client = get_zerodb_client()
    email_service = get_email_service()

    try:
        # Get all board members and admins
        board_users = db_client.query_documents(
            collection="users",
            filters={"role": {"$in": ["board_member", "admin"]}},
            limit=50
        )

        board_emails = []
        for user in board_users.get("documents", []):
            user_data = user.get("data", {})
            if user_data.get("is_active") and user_data.get("is_verified"):
                board_emails.append(user_data.get("email"))

        if not board_emails:
            logger.warning("No board members found to notify about new application")
            return

        subject = "New Membership Application - Action Required"

        # Send email to each board member
        for board_email in board_emails:
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #8B0000; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center; }}
                    .info-box {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                    .button {{ display: inline-block; background-color: #8B0000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>New Membership Application</h1>
                </div>
                <div class="content">
                    <h2>Action Required</h2>
                    <p>A new membership application has been submitted and requires Board review.</p>

                    <div class="info-box">
                        <strong>Applicant:</strong> {applicant_name}<br>
                        <strong>Email:</strong> {applicant_email}<br>
                        <strong>Application ID:</strong> {application_id}<br>
                        <strong>Submitted:</strong> {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}
                    </div>

                    <p>Please log in to the WWMAA admin portal to review and process this application.</p>

                    <div style="text-align: center;">
                        <a href="{settings.PYTHON_BACKEND_URL.replace(':8000', ':3000')}/admin/applications/{application_id}" class="button">Review Application</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Women's Martial Arts Association of America - Board Portal</p>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            New Membership Application - Action Required

            A new membership application has been submitted and requires Board review.

            Applicant: {applicant_name}
            Email: {applicant_email}
            Application ID: {application_id}
            Submitted: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}

            Please log in to the WWMAA admin portal to review and process this application.

            ---
            Women's Martial Arts Association of America - Board Portal
            """

            try:
                email_service._send_email(
                    to_email=board_email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    tag="board-notification"
                )
            except EmailSendError as e:
                logger.error(f"Failed to send board notification to {board_email}: {e}")

        logger.info(f"Board notification emails sent to {len(board_emails)} members")

    except Exception as e:
        logger.error(f"Failed to send board notifications: {e}")
        # Don't fail the request if email fails


# ============================================================================
# APPLICATION ENDPOINTS
# ============================================================================

@router.post(
    "",
    response_model=ApplicationSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit membership application",
    description="Submit a new membership application (no authentication required)"
)
async def submit_application(
    # Form data
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: EmailStr = Form(...),
    phone: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    address_line1: Optional[str] = Form(None),
    address_line2: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    zip_code: Optional[str] = Form(None),
    country: str = Form("USA"),
    disciplines: str = Form(..., description="Comma-separated list of disciplines"),
    experience_years: int = Form(...),
    current_rank: Optional[str] = Form(None),
    school_affiliation: Optional[str] = Form(None),
    instructor_name: Optional[str] = Form(None),
    motivation: str = Form(...),
    goals: Optional[str] = Form(None),
    referral_source: Optional[str] = Form(None),
    # File uploads (optional)
    certificate_files: Optional[List[UploadFile]] = File(None)
) -> ApplicationSubmitResponse:
    """
    Submit a new membership application

    This endpoint (US-015):
    1. Validates all required fields (personal info + martial arts background)
    2. Checks for duplicate applications by email
    3. Uploads certificate files to ZeroDB Object Storage (if provided)
    4. Creates application document in 'applications' collection with status 'submitted'
    5. Sends confirmation email to applicant
    6. Sends notification email to board members
    7. Returns application ID and confirmation details

    No authentication required - public endpoint.

    Args:
        Form data with personal info, martial arts background, and optional files

    Returns:
        ApplicationSubmitResponse with application ID and confirmation

    Raises:
        HTTPException 400: Duplicate application or validation error
        HTTPException 500: Server error
    """
    db_client = get_zerodb_client()

    try:
        # Parse disciplines
        disciplines_list = [d.strip() for d in disciplines.split(",") if d.strip()]
        if not disciplines_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one martial arts discipline is required"
            )

        # Validate motivation length
        if not motivation or len(motivation.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Motivation must be at least 10 characters"
            )

        # Check for duplicate application (submitted in last 30 days)
        email_lower = email.lower()
        logger.info(f"Checking for duplicate application for email: {email_lower}")

        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()

        existing_apps = db_client.query_documents(
            collection="applications",
            filters={
                "email": email_lower,
                "status": {"$in": ["submitted", "under_review", "approved"]},
                "submitted_at": {"$gte": cutoff_date}
            },
            limit=1
        )

        if existing_apps.get("documents") and len(existing_apps["documents"]) > 0:
            logger.warning(f"Duplicate application attempt for email: {email_lower}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An application with this email address already exists and is being processed. Please contact us if you need to update your application."
            )

        # Create application ID
        application_id = str(uuid4())

        # Upload certificate files if provided
        uploaded_files = []
        if certificate_files:
            logger.info(f"Processing {len(certificate_files)} certificate files")
            for cert_file in certificate_files:
                if cert_file.filename:  # Skip empty file uploads
                    file_metadata = await upload_certificate_file(cert_file, application_id)
                    uploaded_files.append(file_metadata)

        # Create application document
        application_data = {
            "user_id": None,  # Not authenticated, will be linked after account creation
            "status": "submitted",
            "first_name": first_name,
            "last_name": last_name,
            "email": email_lower,
            "phone": phone,
            "date_of_birth": date_of_birth,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
            "disciplines": disciplines_list,
            "experience_years": experience_years,
            "current_rank": current_rank,
            "school_affiliation": school_affiliation,
            "instructor_name": instructor_name,
            "motivation": motivation,
            "goals": goals,
            "referral_source": referral_source,
            "certificate_files": uploaded_files,
            "submitted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Creating application in ZeroDB: {application_id}")
        db_client.create_document(
            collection="applications",
            data=application_data,
            document_id=application_id
        )

        logger.info(f"Application created successfully: {application_id}")

        # Send confirmation email to applicant
        applicant_name = f"{first_name} {last_name}"
        await send_application_confirmation_email(email_lower, applicant_name, application_id)

        # Send notification email to board members
        await send_board_notification_email(application_id, applicant_name, email_lower)

        return ApplicationSubmitResponse(
            message="Application submitted successfully. You will receive a confirmation email shortly.",
            application_id=application_id,
            status="submitted",
            confirmation_sent=True
        )

    except HTTPException:
        raise
    except ZeroDBValidationError as e:
        logger.error(f"Validation error during application submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid application data: {str(e)}"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error during application submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit application. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error during application submission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application by ID",
    description="Get a specific application (owner, board members, or admins only)"
)
async def get_application(
    application_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
) -> ApplicationResponse:
    """
    Get application by ID

    Authorization rules:
    - Application owner can view their own application
    - Board members can view all applications
    - Admins can view all applications
    - Public users cannot view applications

    Args:
        application_id: Application UUID
        current_user: Optional authenticated user

    Returns:
        ApplicationResponse with application details

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: Not authorized to view this application
        HTTPException 404: Application not found
    """
    db_client = get_zerodb_client()

    try:
        # Fetch application
        logger.info(f"Fetching application: {application_id}")
        application = db_client.get_document(
            collection="applications",
            document_id=application_id
        )

        application_data = application.get("data", {})

        # Check authorization
        if current_user:
            # Convert application data to Application object for permission check
            from backend.models.schemas import Application
            app_obj = Application(**application_data)

            if not can_view_application(current_user, app_obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this application"
                )
        else:
            # Public users cannot view applications
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view applications"
            )

        # Return application data
        return ApplicationResponse(
            id=application.get("id"),
            user_id=application_data.get("user_id"),
            status=application_data.get("status"),
            first_name=application_data.get("first_name"),
            last_name=application_data.get("last_name"),
            email=application_data.get("email"),
            phone=application_data.get("phone"),
            date_of_birth=application_data.get("date_of_birth"),
            address_line1=application_data.get("address_line1"),
            address_line2=application_data.get("address_line2"),
            city=application_data.get("city"),
            state=application_data.get("state"),
            zip_code=application_data.get("zip_code"),
            country=application_data.get("country", "USA"),
            disciplines=application_data.get("disciplines", []),
            experience_years=application_data.get("experience_years"),
            current_rank=application_data.get("current_rank"),
            school_affiliation=application_data.get("school_affiliation"),
            instructor_name=application_data.get("instructor_name"),
            motivation=application_data.get("motivation"),
            goals=application_data.get("goals"),
            referral_source=application_data.get("referral_source"),
            certificate_files=application_data.get("certificate_files", []),
            submitted_at=application_data.get("submitted_at"),
            created_at=application_data.get("created_at"),
            updated_at=application_data.get("updated_at")
        )

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application not found: {application_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch application"
        )


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List all applications",
    description="List all applications (board members and admins only)"
)
async def list_applications(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(RoleChecker(allowed_roles=["admin", "board_member"]))
) -> ApplicationListResponse:
    """
    List all applications with pagination

    Only accessible to board members and admins.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status_filter: Optional status filter (submitted, under_review, approved, rejected)
        current_user: Authenticated user (board member or admin)

    Returns:
        ApplicationListResponse with paginated applications
    """
    db_client = get_zerodb_client()

    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter

        # Calculate offset
        offset = (page - 1) * page_size

        # Query applications
        logger.info(f"Querying applications (page={page}, size={page_size}, status={status_filter})")
        result = db_client.query_documents(
            collection="applications",
            filters=filters,
            limit=page_size,
            offset=offset,
            sort={"submitted_at": "desc"}
        )

        applications = []
        for app_doc in result.get("documents", []):
            app_data = app_doc.get("data", {})
            applications.append(ApplicationResponse(
                id=app_doc.get("id"),
                user_id=app_data.get("user_id"),
                status=app_data.get("status"),
                first_name=app_data.get("first_name"),
                last_name=app_data.get("last_name"),
                email=app_data.get("email"),
                phone=app_data.get("phone"),
                date_of_birth=app_data.get("date_of_birth"),
                address_line1=app_data.get("address_line1"),
                address_line2=app_data.get("address_line2"),
                city=app_data.get("city"),
                state=app_data.get("state"),
                zip_code=app_data.get("zip_code"),
                country=app_data.get("country", "USA"),
                disciplines=app_data.get("disciplines", []),
                experience_years=app_data.get("experience_years"),
                current_rank=app_data.get("current_rank"),
                school_affiliation=app_data.get("school_affiliation"),
                instructor_name=app_data.get("instructor_name"),
                motivation=app_data.get("motivation"),
                goals=app_data.get("goals"),
                referral_source=app_data.get("referral_source"),
                certificate_files=app_data.get("certificate_files", []),
                submitted_at=app_data.get("submitted_at"),
                created_at=app_data.get("created_at"),
                updated_at=app_data.get("updated_at")
            ))

        # Get total count
        total = result.get("total", len(applications))

        return ApplicationListResponse(
            applications=applications,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing applications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications"
        )


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    summary="Update draft application",
    description="Update a draft application (applicant only)"
)
async def update_application(
    application_id: str,
    update_data: ApplicationUpdateRequest,
    current_user: dict = Depends(CurrentUser())
) -> ApplicationResponse:
    """
    Update a draft application

    Only the application owner can update their own draft application.
    Applications with status 'submitted', 'under_review', 'approved', or 'rejected' cannot be updated.

    Args:
        application_id: Application UUID
        update_data: Fields to update
        current_user: Authenticated user

    Returns:
        ApplicationResponse with updated application

    Raises:
        HTTPException 403: Not authorized or application not in draft status
        HTTPException 404: Application not found
    """
    db_client = get_zerodb_client()

    try:
        # Fetch application
        application = db_client.get_document(
            collection="applications",
            document_id=application_id
        )

        application_data = application.get("data", {})

        # Check if application is in draft status
        if application_data.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only draft applications can be updated. This application has been submitted."
            )

        # Check authorization (only owner can update)
        app_user_id = application_data.get("user_id")
        if app_user_id and str(app_user_id) != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own applications"
            )

        # Build update dict (only include non-None fields)
        update_fields = update_data.model_dump(exclude_none=True)
        update_fields["updated_at"] = datetime.utcnow().isoformat()

        # Update application
        logger.info(f"Updating application {application_id}")
        updated_app = db_client.update_document(
            collection="applications",
            document_id=application_id,
            data=update_fields,
            merge=True
        )

        updated_data = updated_app.get("data", {})

        return ApplicationResponse(
            id=updated_app.get("id"),
            user_id=updated_data.get("user_id"),
            status=updated_data.get("status"),
            first_name=updated_data.get("first_name"),
            last_name=updated_data.get("last_name"),
            email=updated_data.get("email"),
            phone=updated_data.get("phone"),
            date_of_birth=updated_data.get("date_of_birth"),
            address_line1=updated_data.get("address_line1"),
            address_line2=updated_data.get("address_line2"),
            city=updated_data.get("city"),
            state=updated_data.get("state"),
            zip_code=updated_data.get("zip_code"),
            country=updated_data.get("country", "USA"),
            disciplines=updated_data.get("disciplines", []),
            experience_years=updated_data.get("experience_years"),
            current_rank=updated_data.get("current_rank"),
            school_affiliation=updated_data.get("school_affiliation"),
            instructor_name=updated_data.get("instructor_name"),
            motivation=updated_data.get("motivation"),
            goals=updated_data.get("goals"),
            referral_source=updated_data.get("referral_source"),
            certificate_files=updated_data.get("certificate_files", []),
            submitted_at=updated_data.get("submitted_at"),
            created_at=updated_data.get("created_at"),
            updated_at=updated_data.get("updated_at")
        )

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application not found: {application_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete draft application",
    description="Delete a draft application (applicant only)"
)
async def delete_application(
    application_id: str,
    current_user: dict = Depends(CurrentUser())
):
    """
    Delete a draft application

    Only the application owner can delete their own draft application.
    Applications with status 'submitted', 'under_review', 'approved', or 'rejected' cannot be deleted.

    Args:
        application_id: Application UUID
        current_user: Authenticated user

    Raises:
        HTTPException 403: Not authorized or application not in draft status
        HTTPException 404: Application not found
    """
    db_client = get_zerodb_client()

    try:
        # Fetch application
        application = db_client.get_document(
            collection="applications",
            document_id=application_id
        )

        application_data = application.get("data", {})

        # Check if application is in draft status
        if application_data.get("status") != "draft":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only draft applications can be deleted. This application has been submitted."
            )

        # Check authorization (only owner can delete)
        app_user_id = application_data.get("user_id")
        if app_user_id and str(app_user_id) != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own applications"
            )

        # Delete certificate files from storage
        certificate_files = application_data.get("certificate_files", [])
        for cert_file in certificate_files:
            try:
                object_name = cert_file.get("object_name")
                if object_name:
                    db_client.delete_object(object_name)
                    logger.info(f"Deleted certificate file: {object_name}")
            except Exception as e:
                logger.error(f"Failed to delete certificate file: {e}")
                # Continue anyway

        # Delete application
        logger.info(f"Deleting application {application_id}")
        db_client.delete_document(
            collection="applications",
            document_id=application_id
        )

        logger.info(f"Application deleted successfully: {application_id}")

    except ZeroDBNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application not found: {application_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application"
        )
