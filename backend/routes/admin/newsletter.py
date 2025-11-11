"""
Admin Newsletter Configuration Endpoints

Provides admin-level API endpoints for managing BeeHiiv newsletter configuration,
subscriber management, and newsletter operations.

Routes:
- GET /api/admin/newsletter/config - Get configuration
- PUT /api/admin/newsletter/config - Update configuration
- POST /api/admin/newsletter/test - Send test email
- GET /api/admin/newsletter/lists - Get all lists
- GET /api/admin/newsletter/stats - Get subscriber stats
- GET /api/admin/newsletter/subscribers - List subscribers
- POST /api/admin/newsletter/sync - Trigger manual sync
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from services.beehiiv_service import BeeHiivService, BeeHiivAPIError
from database.zerodb import ZeroDBClient
from models.schemas import BeeHiivConfig, NewsletterSubscriber, UserRole
from auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/admin/newsletter", tags=["Admin Newsletter"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ConfigUpdateRequest(BaseModel):
    """Request model for updating BeeHiiv configuration"""
    api_key: Optional[str] = Field(None, description="BeeHiiv API key")
    publication_id: Optional[str] = Field(None, description="BeeHiiv publication ID")
    list_ids: Optional[Dict[str, str]] = Field(None, description="Email list IDs")
    custom_domain: Optional[str] = Field(None, description="Custom domain")
    from_email: Optional[EmailStr] = Field(None, description="From email address")
    from_name: Optional[str] = Field(None, description="From name")
    auto_sync_enabled: Optional[bool] = Field(None, description="Auto-sync enabled")
    welcome_email_enabled: Optional[bool] = Field(None, description="Welcome email enabled")
    sync_frequency_hours: Optional[int] = Field(None, ge=1, le=168, description="Sync frequency")


class TestEmailRequest(BaseModel):
    """Request model for sending test email"""
    recipient_email: EmailStr = Field(..., description="Test recipient email")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    content: str = Field(..., min_length=1, description="Email content (HTML)")


class SubscriberStatsResponse(BaseModel):
    """Response model for subscriber statistics"""
    total_subscribers: int
    active_subscribers: int
    unsubscribed_count: int
    bounced_count: int
    list_breakdown: Dict[str, int]
    growth_this_week: int
    growth_this_month: int


class SubscriberListResponse(BaseModel):
    """Response model for subscriber list"""
    subscribers: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_more: bool


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_db() -> ZeroDBClient:
    """Get database client"""
    db = ZeroDBClient()
    await db.connect()
    try:
        yield db
    finally:
        await db.disconnect()


async def get_beehiiv_service(db: ZeroDBClient = Depends(get_db)) -> BeeHiivService:
    """Get BeeHiiv service with configuration from database"""
    configs = await db.find("beehiiv_config", {})

    if not configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BeeHiiv not configured. Run setup script first."
        )

    config = configs[0]
    return BeeHiivService(
        api_key=config.get("api_key"),
        publication_id=config.get("publication_id")
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/config")
async def get_configuration(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Get BeeHiiv configuration

    Requires admin role.
    """
    configs = await db.find("beehiiv_config", {})

    if not configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BeeHiiv configuration not found. Run setup script."
        )

    config = configs[0]

    # Mask API key for security
    if "api_key" in config:
        config["api_key"] = f"{config['api_key'][:8]}...{config['api_key'][-4:]}"

    return {
        "success": True,
        "data": config
    }


@router.put("/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Update BeeHiiv configuration

    Requires admin role.
    """
    configs = await db.find("beehiiv_config", {})

    if not configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BeeHiiv configuration not found. Run setup script."
        )

    config_id = configs[0]["id"]

    # Build update dictionary with only provided fields
    updates = {}
    if request.api_key is not None:
        updates["api_key"] = request.api_key
    if request.publication_id is not None:
        updates["publication_id"] = request.publication_id
    if request.list_ids is not None:
        updates["list_ids"] = request.list_ids
    if request.custom_domain is not None:
        updates["custom_domain"] = request.custom_domain
    if request.from_email is not None:
        updates["from_email"] = request.from_email
    if request.from_name is not None:
        updates["from_name"] = request.from_name
    if request.auto_sync_enabled is not None:
        updates["auto_sync_enabled"] = request.auto_sync_enabled
    if request.welcome_email_enabled is not None:
        updates["welcome_email_enabled"] = request.welcome_email_enabled
    if request.sync_frequency_hours is not None:
        updates["sync_frequency_hours"] = request.sync_frequency_hours

    updates["updated_at"] = datetime.utcnow()

    # Update configuration
    await db.update_one(
        "beehiiv_config",
        {"id": config_id},
        updates
    )

    return {
        "success": True,
        "message": "Configuration updated successfully"
    }


@router.post("/test")
async def send_test_email(
    request: TestEmailRequest,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    service: BeeHiivService = Depends(get_beehiiv_service)
):
    """
    Send test email

    Requires admin role.
    """
    try:
        result = service.send_test_email(
            email=request.recipient_email,
            subject=request.subject,
            content=request.content
        )

        return {
            "success": True,
            "message": f"Test email sent to {request.recipient_email}",
            "data": result
        }
    except BeeHiivAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )


@router.get("/lists")
async def get_lists(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db)
):
    """
    Get all email lists

    Requires admin role.
    """
    configs = await db.find("beehiiv_config", {})

    if not configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BeeHiiv configuration not found"
        )

    list_ids = configs[0].get("list_ids", {})

    return {
        "success": True,
        "data": {
            "lists": list_ids,
            "count": len(list_ids)
        }
    }


@router.get("/stats", response_model=SubscriberStatsResponse)
async def get_subscriber_stats(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db),
    service: BeeHiivService = Depends(get_beehiiv_service)
):
    """
    Get subscriber statistics

    Requires admin role.
    """
    try:
        # Get stats from BeeHiiv
        beehiiv_stats = service.get_subscriber_stats()

        # Get stats from local database
        all_subscribers = await db.find("newsletter_subscribers", {})
        active = await db.find("newsletter_subscribers", {"status": "active"})
        unsubscribed = await db.find("newsletter_subscribers", {"status": "unsubscribed"})
        bounced = await db.find("newsletter_subscribers", {"status": "bounced"})

        # Calculate growth
        from datetime import timedelta
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        week_growth = await db.find(
            "newsletter_subscribers",
            {"subscribed_at": {"$gte": week_ago}}
        )
        month_growth = await db.find(
            "newsletter_subscribers",
            {"subscribed_at": {"$gte": month_ago}}
        )

        # Count by list
        list_breakdown = {}
        config = await db.find_one("beehiiv_config", {})
        if config and config.get("list_ids"):
            for list_name, list_id in config["list_ids"].items():
                count = await db.count(
                    "newsletter_subscribers",
                    {"list_ids": list_id}
                )
                list_breakdown[list_name] = count

        return SubscriberStatsResponse(
            total_subscribers=len(all_subscribers),
            active_subscribers=len(active),
            unsubscribed_count=len(unsubscribed),
            bounced_count=len(bounced),
            list_breakdown=list_breakdown,
            growth_this_week=len(week_growth),
            growth_this_month=len(month_growth)
        )

    except BeeHiivAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/subscribers", response_model=SubscriberListResponse)
async def list_subscribers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    list_id: Optional[str] = Query(None, description="Filter by list ID"),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db)
):
    """
    List newsletter subscribers with pagination

    Requires admin role.
    """
    # Build filter
    filter_query = {}
    if status:
        filter_query["status"] = status
    if list_id:
        filter_query["list_ids"] = list_id

    # Get total count
    total = await db.count("newsletter_subscribers", filter_query)

    # Get paginated results
    skip = (page - 1) * limit
    subscribers = await db.find(
        "newsletter_subscribers",
        filter_query,
        skip=skip,
        limit=limit,
        sort=[("created_at", -1)]
    )

    has_more = (skip + len(subscribers)) < total

    return SubscriberListResponse(
        subscribers=subscribers,
        total=total,
        page=page,
        limit=limit,
        has_more=has_more
    )


@router.post("/sync")
async def trigger_manual_sync(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db: ZeroDBClient = Depends(get_db),
    service: BeeHiivService = Depends(get_beehiiv_service)
):
    """
    Trigger manual subscriber sync

    Requires admin role.
    """
    try:
        # Import sync service
        from services.subscriber_sync_service import SubscriberSyncService

        sync_service = SubscriberSyncService(db, service)
        result = await sync_service.sync_from_beehiiv()

        return {
            "success": True,
            "message": "Sync completed successfully",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
