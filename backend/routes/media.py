"""
Media Routes for WWMAA Backend

Provides RESTful API endpoints for media asset management:
- POST /api/media/upload - Upload video or file (admin/instructor only)
- GET /api/media - List media assets (filtered by access level)
- GET /api/media/{id} - Get media asset details
- PUT /api/media/{id} - Update media metadata (admin/instructor)
- DELETE /api/media/{id} - Delete media asset (admin only)
- GET /api/media/{id}/access-url - Get signed URL for playback
- POST /api/media/{id}/captions - Upload captions (admin/instructor)
- POST /api/media/upload-chunked/initiate - Initiate chunked upload
- POST /api/media/upload-chunked/chunk - Upload chunk
- POST /api/media/upload-chunked/finalize - Finalize chunked upload
"""

import logging
import tempfile
import os
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Query,
    UploadFile,
    File,
    Form,
    Body
)
from pydantic import BaseModel, Field

from backend.services.media_service import get_media_service, MediaService
from backend.services.upload_service import UploadService
from backend.services.cloudflare_stream_service import CloudflareStreamError
from backend.services.zerodb_service import ZeroDBError
from backend.middleware.auth_middleware import get_current_user
from backend.models.schemas import User, UserRole, MediaType, SubscriptionTier

# Import enums from temporary extension
import sys
sys.path.insert(0, '/Users/aideveloper/Desktop/wwmaa/backend/models')
from schemas_media_extension import MediaAssetStatus, MediaAccessLevel

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/media", tags=["media"])


# ============================================================================
# Request/Response Models
# ============================================================================

class MediaUploadRequest(BaseModel):
    """Request model for media upload"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    media_type: MediaType
    access_level: MediaAccessLevel = MediaAccessLevel.MEMBERS_ONLY
    required_tier: Optional[SubscriptionTier] = None
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)


class MediaUpdateRequest(BaseModel):
    """Request model for media update"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    access_level: Optional[MediaAccessLevel] = None
    required_tier: Optional[SubscriptionTier] = None
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None


class ChunkedUploadInitRequest(BaseModel):
    """Request model for initiating chunked upload"""
    file_name: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    media_type: MediaType
    access_level: MediaAccessLevel = MediaAccessLevel.MEMBERS_ONLY
    required_tier: Optional[SubscriptionTier] = None


class ChunkedUploadChunkRequest(BaseModel):
    """Request model for uploading chunk"""
    upload_id: str
    chunk_index: int = Field(..., ge=0)


class MediaListResponse(BaseModel):
    """Response model for media list"""
    total: int
    items: List[dict]
    limit: int
    offset: int


# ============================================================================
# Helper Functions
# ============================================================================

def check_media_permissions(user: User, required_roles: List[UserRole]):
    """Check if user has required role for media operations"""
    if user.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}"
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    media_type: str = Form(...),
    access_level: str = Form("members_only"),
    required_tier: Optional[str] = Form(None),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Upload video or file (admin/instructor only)

    **Required Roles:** admin, instructor

    **Parameters:**
    - file: File to upload
    - title: Media title
    - description: Optional description
    - media_type: Type (video/image/document)
    - access_level: Access level (public/members_only/tier_specific)
    - required_tier: Required tier if tier_specific
    - entity_type: Related entity type (training_session/event)
    - entity_id: Related entity ID
    - tags: Comma-separated tags

    **Response:**
    - 201: Media uploaded successfully
    - 403: Insufficient permissions
    - 400: Validation error
    - 500: Server error
    """
    # Check permissions
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    try:
        # Parse enums
        media_type_enum = MediaType(media_type)
        access_level_enum = MediaAccessLevel(access_level)
        required_tier_enum = SubscriptionTier(required_tier) if required_tier else None

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Create media asset
            asset = await media_service.create_media_asset(
                file_path=temp_file_path,
                media_type=media_type_enum,
                title=title,
                created_by=current_user.id,
                description=description,
                access_level=access_level_enum,
                required_tier=required_tier_enum,
                entity_type=entity_type,
                entity_id=UUID(entity_id) if entity_id else None,
                metadata={"tags": tag_list}
            )

            logger.info(f"Media uploaded successfully: {asset['id']} by user {current_user.id}")

            return {
                "message": "Media uploaded successfully",
                "asset": asset
            }

        finally:
            # Cleanup temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CloudflareStreamError as e:
        logger.error(f"Cloudflare Stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )
    except ZeroDBError as e:
        logger.error(f"ZeroDB error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store media metadata: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error uploading media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload media"
        )


@router.get("", response_model=MediaListResponse)
async def list_media(
    media_type: Optional[str] = Query(None, description="Filter by media type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    List media assets filtered by access level

    **Parameters:**
    - media_type: Filter by type (video/image/document)
    - status: Filter by status (uploading/processing/ready/failed)
    - entity_type: Filter by entity type
    - entity_id: Filter by entity ID
    - limit: Maximum results (1-100)
    - offset: Pagination offset

    **Response:**
    - 200: List of media assets
    - 500: Server error
    """
    try:
        # Get user subscription tier from subscriptions collection
        # For now, assume basic tier for members
        user_tier = SubscriptionTier.BASIC if current_user.role == UserRole.MEMBER else None

        # Parse filters
        media_type_enum = MediaType(media_type) if media_type else None
        status_enum = MediaAssetStatus(status) if status else None
        entity_id_uuid = UUID(entity_id) if entity_id else None

        # List assets
        assets = await media_service.list_media_assets(
            user_id=current_user.id,
            user_role=current_user.role,
            user_tier=user_tier,
            media_type=media_type_enum,
            status=status_enum,
            entity_type=entity_type,
            entity_id=entity_id_uuid,
            limit=limit,
            offset=offset
        )

        return {
            "total": len(assets),  # Note: This is not the total count, just returned count
            "items": assets,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list media assets"
        )


@router.get("/{asset_id}")
async def get_media(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Get media asset details

    **Parameters:**
    - asset_id: Media asset ID

    **Response:**
    - 200: Media asset details
    - 403: Insufficient permissions
    - 404: Asset not found
    """
    try:
        # Get user tier (simplified)
        user_tier = SubscriptionTier.BASIC if current_user.role == UserRole.MEMBER else None

        asset = await media_service.get_media_asset(
            asset_id=asset_id,
            user_id=current_user.id,
            user_role=current_user.role,
            user_tier=user_tier
        )

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media asset not found"
            )

        return asset

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get media asset"
        )


@router.put("/{asset_id}")
async def update_media(
    asset_id: UUID,
    updates: MediaUpdateRequest,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Update media metadata (admin/instructor only)

    **Required Roles:** admin, instructor

    **Parameters:**
    - asset_id: Media asset ID
    - updates: Fields to update

    **Response:**
    - 200: Media updated successfully
    - 403: Insufficient permissions
    - 404: Asset not found
    """
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    try:
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}

        # Convert enums to values
        if "access_level" in update_dict:
            update_dict["access_level"] = update_dict["access_level"].value
        if "required_tier" in update_dict:
            update_dict["required_tier"] = update_dict["required_tier"].value

        asset = await media_service.update_media_asset(
            asset_id=asset_id,
            updates=update_dict
        )

        logger.info(f"Media updated: {asset_id} by user {current_user.id}")

        return {
            "message": "Media updated successfully",
            "asset": asset
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update media asset"
        )


@router.delete("/{asset_id}")
async def delete_media(
    asset_id: UUID,
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Delete media asset (admin only)

    **Required Roles:** admin

    **Parameters:**
    - asset_id: Media asset ID

    **Response:**
    - 200: Media deleted successfully
    - 403: Insufficient permissions
    - 404: Asset not found
    """
    check_media_permissions(current_user, [UserRole.ADMIN])

    try:
        await media_service.delete_media_asset(asset_id=asset_id)

        logger.info(f"Media deleted: {asset_id} by user {current_user.id}")

        return {
            "message": "Media deleted successfully",
            "asset_id": str(asset_id)
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media asset"
        )


@router.get("/{asset_id}/access-url")
async def get_access_url(
    asset_id: UUID,
    expiry_seconds: int = Query(86400, ge=300, le=604800, description="URL expiry in seconds (5min - 7days)"),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Get signed URL for media playback

    **Parameters:**
    - asset_id: Media asset ID
    - expiry_seconds: URL expiry (default 24 hours, max 7 days)

    **Response:**
    - 200: Signed URL
    - 403: Insufficient permissions
    - 404: Asset not found
    """
    try:
        # Get user tier (simplified)
        user_tier = SubscriptionTier.BASIC if current_user.role == UserRole.MEMBER else SubscriptionTier.PREMIUM

        access_url = await media_service.generate_access_url(
            asset_id=asset_id,
            user_id=current_user.id,
            user_role=current_user.role,
            user_tier=user_tier,
            expiry_seconds=expiry_seconds
        )

        return {
            "asset_id": str(asset_id),
            "access_url": access_url,
            "expires_in": expiry_seconds
        }

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating access URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access URL"
        )


@router.post("/{asset_id}/captions")
async def upload_captions(
    asset_id: UUID,
    caption_file: UploadFile = File(...),
    language: str = Form("en"),
    label: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Upload captions for video (admin/instructor only)

    **Required Roles:** admin, instructor

    **Parameters:**
    - asset_id: Media asset ID
    - caption_file: VTT caption file
    - language: Language code (e.g., 'en', 'es')
    - label: Display label (e.g., 'English')

    **Response:**
    - 200: Captions uploaded successfully
    - 403: Insufficient permissions
    - 404: Asset not found
    - 400: Invalid file format
    """
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    # Validate file extension
    if not caption_file.filename.endswith('.vtt'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caption file must be in WebVTT format (.vtt)"
        )

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.vtt') as temp_file:
            content = await caption_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            await media_service.upload_captions(
                asset_id=asset_id,
                caption_file=temp_file_path,
                language=language,
                label=label
            )

            logger.info(f"Captions uploaded for {asset_id}, language: {language}")

            return {
                "message": "Captions uploaded successfully",
                "asset_id": str(asset_id),
                "language": language
            }

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading captions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload captions"
        )


# ============================================================================
# Chunked Upload Endpoints
# ============================================================================

@router.post("/upload-chunked/initiate")
async def initiate_chunked_upload(
    request: ChunkedUploadInitRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Initiate chunked upload for large files (admin/instructor only)

    **Required Roles:** admin, instructor

    **Parameters:**
    - file_name: Original filename
    - file_size: Total file size in bytes
    - title: Media title
    - description: Optional description
    - media_type: Media type
    - access_level: Access level
    - required_tier: Required tier if tier_specific

    **Response:**
    - 200: Upload session created
    - 403: Insufficient permissions
    - 400: File size exceeds limit
    """
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    try:
        upload_service = UploadService()

        session = upload_service.initiate_upload(
            file_name=request.file_name,
            file_size=request.file_size,
            user_id=str(current_user.id),
            metadata={
                "title": request.title,
                "description": request.description,
                "media_type": request.media_type.value,
                "access_level": request.access_level.value,
                "required_tier": request.required_tier.value if request.required_tier else None
            }
        )

        logger.info(f"Chunked upload initiated: {session['upload_id']}")

        return session

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error initiating chunked upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate upload"
        )


@router.post("/upload-chunked/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file chunk

    **Required Roles:** admin, instructor

    **Parameters:**
    - upload_id: Upload session ID
    - chunk_index: Chunk index (0-based)
    - chunk: Chunk data

    **Response:**
    - 200: Chunk uploaded successfully
    - 403: Insufficient permissions
    - 400: Invalid chunk
    """
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    try:
        upload_service = UploadService()

        chunk_data = await chunk.read()

        progress = upload_service.upload_chunk(
            upload_id=upload_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data
        )

        return progress

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading chunk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload chunk"
        )


@router.post("/upload-chunked/finalize")
async def finalize_chunked_upload(
    upload_id: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service)
):
    """
    Finalize chunked upload and process media

    **Required Roles:** admin, instructor

    **Parameters:**
    - upload_id: Upload session ID

    **Response:**
    - 200: Upload finalized, media processing started
    - 403: Insufficient permissions
    - 400: Upload incomplete
    """
    check_media_permissions(current_user, [UserRole.ADMIN, UserRole.INSTRUCTOR])

    try:
        upload_service = UploadService()

        # Finalize upload
        result = upload_service.finalize_upload(upload_id)

        # Create media asset from uploaded file
        metadata = result.get("metadata", {})

        asset = await media_service.create_media_asset(
            file_path=result["temp_file"],
            media_type=MediaType(metadata.get("media_type", "video")),
            title=metadata.get("title", "Untitled"),
            created_by=current_user.id,
            description=metadata.get("description"),
            access_level=MediaAccessLevel(metadata.get("access_level", "members_only")),
            required_tier=SubscriptionTier(metadata["required_tier"]) if metadata.get("required_tier") else None
        )

        # Cleanup temp file
        upload_service.cleanup_temp_file(upload_id)

        logger.info(f"Chunked upload finalized: {upload_id}, asset: {asset['id']}")

        return {
            "message": "Upload finalized successfully",
            "upload_id": upload_id,
            "asset": asset
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finalizing upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize upload"
        )


@router.get("/upload-chunked/{upload_id}/progress")
async def get_upload_progress(
    upload_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get upload progress

    **Parameters:**
    - upload_id: Upload session ID

    **Response:**
    - 200: Upload progress
    - 404: Upload session not found
    """
    try:
        upload_service = UploadService()

        progress = upload_service.get_upload_progress(upload_id)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )

        return progress

    except Exception as e:
        logger.error(f"Error getting upload progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get upload progress"
        )
