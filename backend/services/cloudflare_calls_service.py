"""
Cloudflare Calls Service for WWMAA Backend

Provides integration with Cloudflare Calls API for live video sessions.
Supports room creation, session management, and recording control.

API Documentation: https://developers.cloudflare.com/calls/
"""

import logging
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class CloudflareCallsError(Exception):
    """Base exception for Cloudflare Calls errors"""
    pass


class CallsAPIError(CloudflareCallsError):
    """Exception raised when Cloudflare Calls API returns an error"""
    pass


class RecordingError(CloudflareCallsError):
    """Exception raised when recording operations fail"""
    pass


class CloudflareCallsService:
    """
    Service for interacting with Cloudflare Calls API

    Provides methods for:
    - Creating and managing live session rooms
    - Starting and stopping recordings
    - Managing session participants
    - Generating signed URLs for secure access
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        app_id: Optional[str] = None
    ):
        """
        Initialize Cloudflare Calls Service

        Args:
            account_id: Cloudflare account ID (defaults to settings.CLOUDFLARE_ACCOUNT_ID)
            api_token: Cloudflare API token (defaults to settings.CLOUDFLARE_API_TOKEN)
            app_id: Cloudflare Calls app ID (defaults to settings.CLOUDFLARE_CALLS_APP_ID)
        """
        self.account_id = account_id or settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = api_token or settings.CLOUDFLARE_API_TOKEN
        self.app_id = app_id or settings.CLOUDFLARE_CALLS_APP_ID

        if not self.account_id or not self.api_token:
            raise CloudflareCallsError("Cloudflare account ID and API token are required")

        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/calls"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"CloudflareCallsService initialized for account {self.account_id}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to Cloudflare Calls API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data (optional)
            params: Query parameters (optional)

        Returns:
            API response data

        Raises:
            CallsAPIError: If API request fails
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
                logger.error(f"Cloudflare Calls API error: {error_message}")
                raise CallsAPIError(f"Cloudflare Calls API error: {error_message}")

            logger.info(f"Cloudflare Calls API {method} {endpoint} succeeded")
            return response_data.get("result", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Cloudflare Calls API request failed: {e}")
            raise CallsAPIError(f"API request failed: {e}")

    def create_room(
        self,
        session_id: str,
        max_participants: Optional[int] = None,
        enable_recording: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new Cloudflare Calls room for a live session

        Args:
            session_id: Unique session identifier
            max_participants: Maximum number of participants (optional)
            enable_recording: Whether to enable recording for this room

        Returns:
            Room data including room_id and room_url

        Raises:
            CallsAPIError: If room creation fails
        """
        logger.info(f"Creating Cloudflare Calls room for session {session_id}")

        data = {
            "sessionId": session_id,
            "maxParticipants": max_participants,
            "features": {
                "recording": enable_recording,
                "screenSharing": True,
                "chat": True
            }
        }

        result = self._make_request("POST", "rooms", data=data)

        logger.info(f"Room created successfully: {result.get('roomId')}")
        return {
            "room_id": result.get("roomId"),
            "room_url": result.get("roomUrl"),
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat()
        }

    def start_recording(self, room_id: str) -> Dict[str, Any]:
        """
        Start recording for a Cloudflare Calls room

        Args:
            room_id: Cloudflare room ID

        Returns:
            Recording data including recording_id

        Raises:
            RecordingError: If recording start fails
        """
        logger.info(f"Starting recording for room {room_id}")

        try:
            result = self._make_request("POST", f"rooms/{room_id}/recordings")

            recording_id = result.get("recordingId")
            logger.info(f"Recording started successfully: {recording_id}")

            return {
                "recording_id": recording_id,
                "room_id": room_id,
                "status": "recording",
                "started_at": datetime.utcnow().isoformat()
            }

        except CallsAPIError as e:
            logger.error(f"Failed to start recording: {e}")
            raise RecordingError(f"Failed to start recording: {e}")

    def stop_recording(self, room_id: str, recording_id: str) -> Dict[str, Any]:
        """
        Stop recording for a Cloudflare Calls room

        Args:
            room_id: Cloudflare room ID
            recording_id: Recording ID

        Returns:
            Recording data with status and metadata

        Raises:
            RecordingError: If recording stop fails
        """
        logger.info(f"Stopping recording {recording_id} for room {room_id}")

        try:
            result = self._make_request(
                "POST",
                f"rooms/{room_id}/recordings/{recording_id}/stop"
            )

            logger.info(f"Recording stopped successfully: {recording_id}")

            return {
                "recording_id": recording_id,
                "room_id": room_id,
                "status": "processing",
                "ended_at": datetime.utcnow().isoformat(),
                "duration_seconds": result.get("duration")
            }

        except CallsAPIError as e:
            logger.error(f"Failed to stop recording: {e}")
            raise RecordingError(f"Failed to stop recording: {e}")

    def get_recording_status(self, room_id: str, recording_id: str) -> Dict[str, Any]:
        """
        Get recording status from Cloudflare Calls

        Args:
            room_id: Cloudflare room ID
            recording_id: Recording ID

        Returns:
            Recording status data

        Raises:
            CallsAPIError: If status retrieval fails
        """
        logger.info(f"Getting recording status for {recording_id}")

        result = self._make_request("GET", f"rooms/{room_id}/recordings/{recording_id}")

        return {
            "recording_id": recording_id,
            "status": result.get("status"),
            "duration_seconds": result.get("duration"),
            "file_size_bytes": result.get("fileSize"),
            "stream_id": result.get("streamId"),
            "stream_url": result.get("streamUrl")
        }

    def delete_room(self, room_id: str) -> bool:
        """
        Delete a Cloudflare Calls room

        Args:
            room_id: Cloudflare room ID

        Returns:
            True if deletion was successful

        Raises:
            CallsAPIError: If deletion fails
        """
        logger.info(f"Deleting room {room_id}")

        try:
            self._make_request("DELETE", f"rooms/{room_id}")
            logger.info(f"Room {room_id} deleted successfully")
            return True

        except CallsAPIError as e:
            logger.error(f"Failed to delete room: {e}")
            return False

    def get_room_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Get list of participants in a room

        Args:
            room_id: Cloudflare room ID

        Returns:
            List of participant data

        Raises:
            CallsAPIError: If retrieval fails
        """
        logger.info(f"Getting participants for room {room_id}")

        result = self._make_request("GET", f"rooms/{room_id}/participants")

        participants = result.get("participants", [])
        logger.info(f"Found {len(participants)} participants in room {room_id}")

        return participants

    def generate_room_token(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
        role: str = "participant",
        expiry_hours: int = 24
    ) -> str:
        """
        Generate a signed token for room access

        Args:
            room_id: Cloudflare room ID
            user_id: User identifier
            user_name: User display name
            role: User role (participant/moderator/presenter)
            expiry_hours: Token expiry in hours

        Returns:
            Signed JWT token for room access

        Raises:
            CallsAPIError: If token generation fails
        """
        logger.info(f"Generating room token for user {user_id} in room {room_id}")

        data = {
            "roomId": room_id,
            "userId": user_id,
            "userName": user_name,
            "role": role,
            "expiresAt": (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()
        }

        result = self._make_request("POST", "tokens", data=data)

        token = result.get("token")
        logger.info(f"Room token generated successfully for user {user_id}")

        return token


# Global service instance
_cloudflare_calls_service_instance: Optional[CloudflareCallsService] = None


def get_cloudflare_calls_service() -> CloudflareCallsService:
    """
    Get or create the global CloudflareCallsService instance

    Returns:
        CloudflareCallsService instance
    """
    global _cloudflare_calls_service_instance

    if _cloudflare_calls_service_instance is None:
        _cloudflare_calls_service_instance = CloudflareCallsService()

    return _cloudflare_calls_service_instance
