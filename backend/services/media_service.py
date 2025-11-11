"""
Media Management Service

This service handles media asset management with access control,
integrating with Cloudflare Stream for videos and ZeroDB for metadata storage.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

from backend.services.zerodb_service import ZeroDBClient, ZeroDBError
from backend.services.cloudflare_stream_service import CloudflareStreamService, CloudflareStreamError
from backend.models.schemas import (
    MediaAsset,
    MediaType,
    UserRole,
    SubscriptionTier
)

# Import enums from temporary extension file
import sys
sys.path.insert(0, '/Users/aideveloper/Desktop/wwmaa/backend/models')
from schemas_media_extension import MediaAssetStatus, MediaAccessLevel

logger = logging.getLogger(__name__)


class MediaService:
    """
    Service for managing media assets with access control

    Features:
    - Upload videos to Cloudflare Stream
    - Store metadata in ZeroDB
    - Tier-based access control
    - Signed URL generation for member-only content
    - Caption/subtitle management
    """

    def __init__(
        self,
        zerodb_client: Optional[ZeroDBClient] = None,
        stream_service: Optional[CloudflareStreamService] = None
    ):
        """
        Initialize media service

        Args:
            zerodb_client: ZeroDB client instance
            stream_service: Cloudflare Stream service instance
        """
        self.db = zerodb_client or ZeroDBClient()
        self.stream = stream_service or CloudflareStreamService()
        self.collection = "media_assets"

    async def create_media_asset(
        self,
        file_path: str,
        media_type: MediaType,
        title: str,
        created_by: UUID,
        description: Optional[str] = None,
        access_level: MediaAccessLevel = MediaAccessLevel.MEMBERS_ONLY,
        required_tier: Optional[SubscriptionTier] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MediaAsset:
        """
        Create media asset by uploading file and storing metadata

        Args:
            file_path: Path to media file
            media_type: Type of media (video/image/document)
            title: Media title
            created_by: User ID of uploader
            description: Optional description
            access_level: Access control level
            required_tier: Required subscription tier if tier_specific
            entity_type: Related entity type (training_session/event)
            entity_id: Related entity ID
            metadata: Additional metadata

        Returns:
            Created MediaAsset

        Raises:
            ValueError: If validation fails
            CloudflareStreamError: If video upload fails
            ZeroDBError: If metadata storage fails

        Example:
            asset = await service.create_media_asset(
                file_path="/path/to/video.mp4",
                media_type=MediaType.VIDEO,
                title="Training Session 1",
                created_by=user_id,
                access_level=MediaAccessLevel.TIER_SPECIFIC,
                required_tier=SubscriptionTier.PREMIUM
            )
        """
        # Validate access level and tier
        if access_level == MediaAccessLevel.TIER_SPECIFIC and not required_tier:
            raise ValueError("required_tier must be specified when access_level is tier_specific")

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        file_size = file_path_obj.stat().st_size
        mime_type = self._get_mime_type(file_path_obj)

        # Create initial media asset record
        asset_data = {
            "id": uuid4(),
            "media_type": media_type.value,
            "title": title,
            "description": description,
            "filename": file_path_obj.name,
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "status": MediaAssetStatus.UPLOADING.value,
            "access_level": access_level.value,
            "required_tier": required_tier.value if required_tier else None,
            "created_by": str(created_by),
            "uploaded_by": str(created_by),
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "view_count": 0,
            "download_count": 0,
            "captions_available": False,
            "caption_languages": []
        }

        # Store initial record
        try:
            self.db.insert(self.collection, asset_data)
        except ZeroDBError as e:
            logger.error(f"Failed to create media asset record: {e}")
            raise

        # Upload to appropriate storage
        try:
            if media_type == MediaType.VIDEO:
                # Upload to Cloudflare Stream
                logger.info(f"Uploading video to Cloudflare Stream: {title}")

                stream_metadata = {
                    "name": title,
                    "requireSignedURLs": access_level != MediaAccessLevel.PUBLIC,
                    "meta": {
                        "asset_id": str(asset_data["id"]),
                        "title": title,
                        "created_by": str(created_by)
                    }
                }

                if file_size > 200 * 1024 * 1024:  # > 200MB
                    logger.warning(f"Large file {file_size / (1024**2):.2f}MB, recommend using chunked upload")

                video_result = self.stream.upload_video(
                    file_path=file_path,
                    metadata=stream_metadata
                )

                # Update asset with video details
                asset_data["storage_provider"] = "cloudflare_stream"
                asset_data["stream_video_id"] = video_result["uid"]
                asset_data["status"] = MediaAssetStatus.PROCESSING.value
                asset_data["url"] = video_result.get("playback", {}).get("hls")
                asset_data["thumbnail_url"] = video_result.get("thumbnail")
                asset_data["preview_url"] = video_result.get("preview")

            else:
                # Upload to ZeroDB Object Storage
                logger.info(f"Uploading file to ZeroDB Object Storage: {title}")

                with open(file_path, 'rb') as f:
                    object_key = f"media/{asset_data['id']}/{file_path_obj.name}"
                    upload_result = self.db.upload_object(
                        object_key=object_key,
                        file_data=f.read(),
                        content_type=mime_type
                    )

                asset_data["storage_provider"] = "zerodb"
                asset_data["object_storage_key"] = object_key
                asset_data["url"] = upload_result.get("url")
                asset_data["status"] = MediaAssetStatus.READY.value

            # Update record in ZeroDB
            self.db.update(
                self.collection,
                {"id": str(asset_data["id"])},
                asset_data
            )

            logger.info(f"Media asset created successfully: {asset_data['id']}")

            # Convert to Pydantic model (will need to add enums to schemas.py)
            # For now, return dict
            return asset_data

        except (CloudflareStreamError, ZeroDBError) as e:
            # Mark as failed
            asset_data["status"] = MediaAssetStatus.FAILED.value
            asset_data["processing_error"] = str(e)
            self.db.update(
                self.collection,
                {"id": str(asset_data["id"])},
                asset_data
            )
            logger.error(f"Failed to upload media: {e}")
            raise

    async def get_media_asset(
        self,
        asset_id: UUID,
        user_id: Optional[UUID] = None,
        user_role: Optional[UserRole] = None,
        user_tier: Optional[SubscriptionTier] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get media asset with access control check

        Args:
            asset_id: Media asset ID
            user_id: User requesting access
            user_role: User's role
            user_tier: User's subscription tier

        Returns:
            Media asset details or None if not found or no access

        Raises:
            PermissionError: If user doesn't have access
        """
        # Get asset from database
        results = self.db.find(
            self.collection,
            {"id": str(asset_id)}
        )

        if not results:
            return None

        asset = results[0]

        # Check access control
        if not self._check_access(asset, user_role, user_tier):
            raise PermissionError(f"User does not have access to media asset {asset_id}")

        return asset

    async def list_media_assets(
        self,
        user_id: Optional[UUID] = None,
        user_role: Optional[UserRole] = None,
        user_tier: Optional[SubscriptionTier] = None,
        media_type: Optional[MediaType] = None,
        status: Optional[MediaAssetStatus] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List media assets with access control filtering

        Args:
            user_id: User requesting list
            user_role: User's role
            user_tier: User's subscription tier
            media_type: Filter by media type
            status: Filter by status
            entity_type: Filter by related entity type
            entity_id: Filter by related entity ID
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of media assets user has access to
        """
        # Build query
        query = {}

        if media_type:
            query["media_type"] = media_type.value

        if status:
            query["status"] = status.value

        if entity_type:
            query["entity_type"] = entity_type

        if entity_id:
            query["entity_id"] = str(entity_id)

        # Get all matching assets
        results = self.db.find(self.collection, query)

        # Filter by access control
        accessible_assets = [
            asset for asset in results
            if self._check_access(asset, user_role, user_tier)
        ]

        # Apply pagination
        paginated = accessible_assets[offset:offset + limit]

        return paginated

    async def update_media_asset(
        self,
        asset_id: UUID,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update media asset metadata

        Args:
            asset_id: Media asset ID
            updates: Fields to update

        Returns:
            Updated asset

        Raises:
            ValueError: If asset not found
        """
        # Get existing asset
        results = self.db.find(
            self.collection,
            {"id": str(asset_id)}
        )

        if not results:
            raise ValueError(f"Media asset not found: {asset_id}")

        asset = results[0]

        # Update allowed fields
        allowed_fields = {
            "title", "description", "access_level", "required_tier",
            "alt_text", "caption", "tags", "metadata"
        }

        for key, value in updates.items():
            if key in allowed_fields:
                asset[key] = value

        asset["updated_at"] = datetime.utcnow().isoformat()

        # Update in database
        self.db.update(
            self.collection,
            {"id": str(asset_id)},
            asset
        )

        # If video and requireSignedURLs changed, update Cloudflare
        if asset.get("stream_video_id") and "access_level" in updates:
            require_signed = updates["access_level"] != MediaAccessLevel.PUBLIC.value
            try:
                self.stream.update_video(
                    asset["stream_video_id"],
                    {"requireSignedURLs": require_signed}
                )
            except CloudflareStreamError as e:
                logger.error(f"Failed to update video access settings: {e}")

        return asset

    async def delete_media_asset(
        self,
        asset_id: UUID
    ) -> bool:
        """
        Delete media asset from storage and database

        Args:
            asset_id: Media asset ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If asset not found
        """
        # Get asset
        results = self.db.find(
            self.collection,
            {"id": str(asset_id)}
        )

        if not results:
            raise ValueError(f"Media asset not found: {asset_id}")

        asset = results[0]

        # Delete from storage
        try:
            if asset.get("stream_video_id"):
                # Delete from Cloudflare Stream
                self.stream.delete_video(asset["stream_video_id"])
            elif asset.get("object_storage_key"):
                # Delete from ZeroDB Object Storage
                self.db.delete_object(asset["object_storage_key"])
        except Exception as e:
            logger.error(f"Failed to delete media from storage: {e}")
            # Continue with database deletion

        # Delete from database
        self.db.delete(
            self.collection,
            {"id": str(asset_id)}
        )

        logger.info(f"Media asset deleted: {asset_id}")
        return True

    async def generate_access_url(
        self,
        asset_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        user_tier: SubscriptionTier,
        expiry_seconds: int = 86400
    ) -> str:
        """
        Generate signed URL for media access

        Args:
            asset_id: Media asset ID
            user_id: User requesting access
            user_role: User's role
            user_tier: User's subscription tier
            expiry_seconds: URL expiry in seconds (default 24 hours)

        Returns:
            Signed URL for access

        Raises:
            PermissionError: If user doesn't have access
            ValueError: If asset not found or not a video
        """
        # Get asset and check access
        asset = await self.get_media_asset(asset_id, user_id, user_role, user_tier)

        if not asset:
            raise ValueError(f"Media asset not found: {asset_id}")

        # Only generate signed URLs for videos
        if asset["media_type"] != MediaType.VIDEO.value:
            return asset.get("url", "")

        if not asset.get("stream_video_id"):
            raise ValueError(f"Video ID not found for asset: {asset_id}")

        # Generate signed token
        token = self.stream.generate_signed_url(
            video_id=asset["stream_video_id"],
            expiry_seconds=expiry_seconds,
            user_id=user_id
        )

        # Build signed URL
        signed_url = f"https://customer-{self.stream.account_id}.cloudflarestream.com/{asset['stream_video_id']}/iframe?token={token}"

        # Increment view count
        asset["view_count"] = asset.get("view_count", 0) + 1
        self.db.update(
            self.collection,
            {"id": str(asset_id)},
            asset
        )

        return signed_url

    async def upload_captions(
        self,
        asset_id: UUID,
        caption_file: str,
        language: str = "en",
        label: Optional[str] = None
    ) -> bool:
        """
        Upload captions for video asset

        Args:
            asset_id: Media asset ID
            caption_file: Path to VTT caption file
            language: Language code (e.g., 'en', 'es')
            label: Display label (e.g., 'English')

        Returns:
            True if uploaded successfully

        Raises:
            ValueError: If asset not found or not a video
        """
        # Get asset
        results = self.db.find(
            self.collection,
            {"id": str(asset_id)}
        )

        if not results:
            raise ValueError(f"Media asset not found: {asset_id}")

        asset = results[0]

        if asset["media_type"] != MediaType.VIDEO.value:
            raise ValueError("Captions can only be uploaded for videos")

        if not asset.get("stream_video_id"):
            raise ValueError("Video ID not found")

        # Upload captions to Cloudflare Stream
        self.stream.upload_captions(
            video_id=asset["stream_video_id"],
            caption_file=caption_file,
            language=language,
            label=label
        )

        # Update asset record
        asset["captions_available"] = True
        if language not in asset.get("caption_languages", []):
            asset["caption_languages"] = asset.get("caption_languages", []) + [language]

        self.db.update(
            self.collection,
            {"id": str(asset_id)},
            asset
        )

        logger.info(f"Captions uploaded for asset {asset_id}, language: {language}")
        return True

    def _check_access(
        self,
        asset: Dict[str, Any],
        user_role: Optional[UserRole],
        user_tier: Optional[SubscriptionTier]
    ) -> bool:
        """
        Check if user has access to media asset

        Args:
            asset: Media asset data
            user_role: User's role
            user_tier: User's subscription tier

        Returns:
            True if user has access
        """
        access_level = asset.get("access_level", MediaAccessLevel.MEMBERS_ONLY.value)

        # Public access
        if access_level == MediaAccessLevel.PUBLIC.value:
            return True

        # Admin and board members have access to everything
        if user_role in [UserRole.ADMIN, UserRole.BOARD_MEMBER]:
            return True

        # Members-only access
        if access_level == MediaAccessLevel.MEMBERS_ONLY.value:
            return user_role in [UserRole.MEMBER, UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER, UserRole.ADMIN]

        # Tier-specific access
        if access_level == MediaAccessLevel.TIER_SPECIFIC.value:
            required_tier = asset.get("required_tier")
            if not required_tier or not user_tier:
                return False

            # Check tier hierarchy
            tier_hierarchy = {
                SubscriptionTier.FREE.value: 0,
                SubscriptionTier.BASIC.value: 1,
                SubscriptionTier.PREMIUM.value: 2,
                SubscriptionTier.LIFETIME.value: 3
            }

            user_tier_level = tier_hierarchy.get(user_tier.value, 0)
            required_tier_level = tier_hierarchy.get(required_tier, 0)

            return user_tier_level >= required_tier_level

        return False

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type from file extension"""
        import mimetypes

        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"


# Global service instance
_media_service_instance: Optional[MediaService] = None


def get_media_service() -> MediaService:
    """
    Get or create the global MediaService instance

    Returns:
        MediaService instance
    """
    global _media_service_instance

    if _media_service_instance is None:
        _media_service_instance = MediaService()

    return _media_service_instance
