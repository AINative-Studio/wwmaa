"""
Cloudflare Stream Service for WWMAA Backend

Provides integration with Cloudflare Stream API for video on demand (VOD).
Supports video upload, signed URL generation, and video management.

API Documentation: https://developers.cloudflare.com/stream/
"""

import logging
import requests
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class CloudflareStreamError(Exception):
    """Base exception for Cloudflare Stream errors"""
    pass


class StreamAPIError(CloudflareStreamError):
    """Exception raised when Cloudflare Stream API returns an error"""
    pass


class CloudflareStreamService:
    """
    Service for interacting with Cloudflare Stream API

    Provides methods for:
    - Managing video uploads
    - Generating signed URLs for secure playback
    - Retrieving video metadata
    - Deleting videos
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """
        Initialize Cloudflare Stream Service

        Args:
            account_id: Cloudflare account ID (defaults to settings.CLOUDFLARE_ACCOUNT_ID)
            api_token: Cloudflare API token (defaults to settings.CLOUDFLARE_API_TOKEN)
        """
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = api_token or settings.CLOUDFLARE_API_TOKEN

        if not self.account_id or not self.api_token:
            raise CloudflareStreamError("Cloudflare account ID and API token are required")

        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/stream"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"CloudflareStreamService initialized for account {self.account_id}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to Cloudflare Stream API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data (optional)
            params: Query parameters (optional)

        Returns:
            API response data

        Raises:
            StreamAPIError: If API request fails
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )

            # Parse response
            response_data = response.json()

            # Check for errors
            if not response.ok or not response_data.get("success", False):
                errors = response_data.get("errors", [])
                error_message = errors[0].get("message", "Unknown error") if errors else "API request failed"
                logger.error(f"Cloudflare Stream API error: {error_message}")
                raise StreamAPIError(f"Cloudflare Stream API error: {error_message}")

            logger.info(f"Cloudflare Stream API {method} {endpoint} succeeded")
            return response_data.get("result", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Cloudflare Stream API request failed: {e}")
            raise StreamAPIError(f"API request failed: {e}")

    def get_video(self, video_id: str) -> Dict[str, Any]:
        """
        Get video metadata from Cloudflare Stream

        Args:
            video_id: Cloudflare Stream video ID

        Returns:
            Video metadata

        Raises:
            StreamAPIError: If retrieval fails
        """
        logger.info(f"Getting video metadata for {video_id}")

        result = self._make_request("GET", video_id)

        return {
            "video_id": result.get("uid"),
            "status": result.get("status", {}).get("state"),
            "duration_seconds": result.get("duration"),
            "file_size_bytes": result.get("size"),
            "thumbnail_url": result.get("thumbnail"),
            "playback_url": result.get("playback", {}).get("hls"),
            "dash_url": result.get("playback", {}).get("dash"),
            "created_at": result.get("created"),
            "modified_at": result.get("modified"),
            "ready_to_stream": result.get("readyToStream", False)
        }

    def create_video_from_url(
        self,
        url: str,
        metadata: Optional[Dict[str, str]] = None,
        require_signed_urls: bool = True
    ) -> Dict[str, Any]:
        """
        Create a video in Cloudflare Stream from a URL

        Args:
            url: URL of video to upload
            metadata: Optional metadata dict
            require_signed_urls: Whether to require signed URLs for playback

        Returns:
            Video creation response

        Raises:
            StreamAPIError: If creation fails
        """
        logger.info(f"Creating video from URL in Cloudflare Stream")

        data = {
            "url": url,
            "meta": metadata or {},
            "requireSignedURLs": require_signed_urls
        }

        result = self._make_request("POST", "", data=data)

        return {
            "video_id": result.get("uid"),
            "status": result.get("status", {}).get("state"),
            "playback_url": result.get("playback", {}).get("hls")
        }

    def update_video_metadata(
        self,
        video_id: str,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update video metadata

        Args:
            video_id: Cloudflare Stream video ID
            metadata: Metadata dict to update

        Returns:
            Updated video data

        Raises:
            StreamAPIError: If update fails
        """
        logger.info(f"Updating metadata for video {video_id}")

        data = {"meta": metadata}

        result = self._make_request("POST", video_id, data=data)

        return {
            "video_id": result.get("uid"),
            "metadata": result.get("meta", {})
        }

    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from Cloudflare Stream

        Args:
            video_id: Cloudflare Stream video ID

        Returns:
            True if deletion was successful

        Raises:
            StreamAPIError: If deletion fails
        """
        logger.info(f"Deleting video {video_id}")

        try:
            self._make_request("DELETE", video_id)
            logger.info(f"Video {video_id} deleted successfully")
            return True

        except StreamAPIError as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    def generate_signed_url(
        self,
        video_id: str,
        expiry_hours: int = 24,
        download_allowed: bool = False
    ) -> str:
        """
        Generate a signed URL for secure video playback

        Note: This is a simplified implementation. For production, you should:
        1. Store signing keys in Cloudflare Stream dashboard
        2. Use proper HMAC-SHA256 signing with your key
        3. Follow Cloudflare's exact signing specification

        Args:
            video_id: Cloudflare Stream video ID
            expiry_hours: URL expiry in hours
            download_allowed: Whether to allow video download

        Returns:
            Signed video playback URL

        Raises:
            StreamAPIError: If URL generation fails
        """
        logger.info(f"Generating signed URL for video {video_id}")

        # Calculate expiry timestamp
        expiry_timestamp = int((datetime.utcnow() + timedelta(hours=expiry_hours)).timestamp())

        # Base playback URL
        base_url = f"https://customer-{self.account_id}.cloudflarestream.com/{video_id}/manifest/video.m3u8"

        # Build query parameters for signed URL
        params = {
            "exp": expiry_timestamp,
            "download": "1" if download_allowed else "0"
        }

        # In production, sign these params with HMAC-SHA256
        # For now, returning the base URL with params
        # You need to configure signing keys in Cloudflare dashboard
        signed_url = f"{base_url}?{urlencode(params)}"

        logger.info(f"Signed URL generated for video {video_id}")

        return signed_url

    def generate_embed_code(
        self,
        video_id: str,
        autoplay: bool = False,
        muted: bool = False,
        controls: bool = True
    ) -> str:
        """
        Generate iframe embed code for video playback

        Args:
            video_id: Cloudflare Stream video ID
            autoplay: Whether to autoplay video
            muted: Whether to mute video by default
            controls: Whether to show player controls

        Returns:
            HTML iframe embed code
        """
        params = []
        if autoplay:
            params.append("autoplay=true")
        if muted:
            params.append("muted=true")
        if not controls:
            params.append("controls=false")

        query_string = "&".join(params)
        embed_url = f"https://customer-{self.account_id}.cloudflarestream.com/{video_id}/iframe"

        if query_string:
            embed_url = f"{embed_url}?{query_string}"

        iframe_code = f'''<iframe
    src="{embed_url}"
    style="border: none;"
    height="720"
    width="1280"
    allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;"
    allowfullscreen="true"
></iframe>'''

        return iframe_code

    def get_upload_url(
        self,
        max_duration_seconds: Optional[int] = None,
        require_signed_urls: bool = True
    ) -> Dict[str, Any]:
        """
        Get a direct upload URL for uploading videos

        Args:
            max_duration_seconds: Maximum video duration allowed
            require_signed_urls: Whether to require signed URLs for playback

        Returns:
            Upload URL and video ID

        Raises:
            StreamAPIError: If URL generation fails
        """
        logger.info("Generating direct upload URL")

        data = {
            "maxDurationSeconds": max_duration_seconds or 3600,
            "requireSignedURLs": require_signed_urls
        }

        result = self._make_request("POST", "direct_upload", data=data)

        return {
            "upload_url": result.get("uploadURL"),
            "video_id": result.get("uid")
        }

    def list_videos(
        self,
        limit: int = 100,
        status: Optional[str] = None
    ) -> list:
        """
        List videos in Cloudflare Stream account

        Args:
            limit: Maximum number of videos to return
            status: Filter by status (ready/error/inprogress)

        Returns:
            List of video metadata dicts

        Raises:
            StreamAPIError: If listing fails
        """
        logger.info(f"Listing videos (limit: {limit})")

        params = {"limit": limit}
        if status:
            params["status"] = status

        result = self._make_request("GET", "", params=params)

        videos = result if isinstance(result, list) else result.get("result", [])

        return [{
            "video_id": video.get("uid"),
            "status": video.get("status", {}).get("state"),
            "duration_seconds": video.get("duration"),
            "created_at": video.get("created")
        } for video in videos]


# Global service instance
_cloudflare_stream_service_instance: Optional[CloudflareStreamService] = None


def get_cloudflare_stream_service() -> CloudflareStreamService:
    """
    Get or create the global CloudflareStreamService instance

    Returns:
        CloudflareStreamService instance
    """
    global _cloudflare_stream_service_instance

    if _cloudflare_stream_service_instance is None:
        _cloudflare_stream_service_instance = CloudflareStreamService()

    return _cloudflare_stream_service_instance
