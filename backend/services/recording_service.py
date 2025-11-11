"""
Recording Service for WWMAA Backend

Orchestrates live session recording workflow using Cloudflare Calls and Stream.
Handles recording lifecycle, error handling, retries, and VOD processing.

US-046: Live Session Recording
"""

import logging
import json
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from backend.config import settings
from backend.services.cloudflare_calls_service import (
    get_cloudflare_calls_service,
    RecordingError as CallsRecordingError
)
from backend.services.cloudflare_stream_service import (
    get_cloudflare_stream_service,
    StreamAPIError
)
from backend.services.zerodb_service import get_zerodb_service
from backend.models.schemas import RecordingStatus

# Configure logging
logger = logging.getLogger(__name__)


class RecordingServiceError(Exception):
    """Base exception for recording service errors"""
    pass


class RecordingStartError(RecordingServiceError):
    """Exception raised when recording start fails"""
    pass


class RecordingStopError(RecordingServiceError):
    """Exception raised when recording stop fails"""
    pass


class RecordingService:
    """
    Service for managing live session recordings

    Provides methods for:
    - Starting and stopping recordings
    - Processing recording uploads
    - Generating signed VOD URLs
    - Handling recording failures and retries
    - Managing chat transcripts
    """

    def __init__(self):
        """Initialize Recording Service"""
        self.calls_service = get_cloudflare_calls_service()
        self.stream_service = get_cloudflare_stream_service()
        self.db_service = get_zerodb_service()

        self.max_retries = 3
        self.retry_delay_seconds = 5

        logger.info("RecordingService initialized")

    def initiate_recording(self, session_id: UUID) -> Dict[str, Any]:
        """
        Start recording for a live training session

        Args:
            session_id: Training session UUID

        Returns:
            Recording data with recording_id and status

        Raises:
            RecordingStartError: If recording start fails after retries
        """
        logger.info(f"Initiating recording for session {session_id}")

        # Get session data
        session_data = self.db_service.get_document("training_sessions", str(session_id))

        if not session_data:
            raise RecordingStartError(f"Session {session_id} not found")

        room_id = session_data.get("cloudflare_room_id")
        if not room_id:
            raise RecordingStartError(f"No Cloudflare room ID found for session {session_id}")

        # Check if recording is enabled
        if not session_data.get("recording_enabled", True):
            logger.warning(f"Recording is disabled for session {session_id}")
            return {
                "session_id": str(session_id),
                "recording_enabled": False,
                "message": "Recording is disabled for this session"
            }

        # Attempt to start recording with retries
        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                # Start recording via Cloudflare Calls API
                recording_result = self.calls_service.start_recording(room_id)

                recording_id = recording_result["recording_id"]

                # Update session in database
                update_data = {
                    "recording_id": recording_id,
                    "recording_status": RecordingStatus.RECORDING.value,
                    "recording_started_at": datetime.utcnow().isoformat(),
                    "recording_retry_count": retry_count,
                    "recording_error": None
                }

                self.db_service.update_document(
                    "training_sessions",
                    str(session_id),
                    update_data
                )

                logger.info(f"Recording started successfully for session {session_id}: {recording_id}")

                return {
                    "session_id": str(session_id),
                    "recording_id": recording_id,
                    "status": RecordingStatus.RECORDING.value,
                    "started_at": update_data["recording_started_at"]
                }

            except (CallsRecordingError, Exception) as e:
                last_error = str(e)
                retry_count += 1
                logger.error(
                    f"Failed to start recording for session {session_id} "
                    f"(attempt {retry_count}/{self.max_retries}): {e}"
                )

                if retry_count < self.max_retries:
                    import time
                    time.sleep(self.retry_delay_seconds)

        # All retries failed
        error_message = f"Failed to start recording after {self.max_retries} attempts: {last_error}"

        # Update session with failure status
        self.db_service.update_document(
            "training_sessions",
            str(session_id),
            {
                "recording_status": RecordingStatus.FAILED.value,
                "recording_error": error_message,
                "recording_retry_count": retry_count
            }
        )

        raise RecordingStartError(error_message)

    def finalize_recording(self, session_id: UUID) -> Dict[str, Any]:
        """
        Stop recording and begin processing for VOD

        Args:
            session_id: Training session UUID

        Returns:
            Recording finalization data

        Raises:
            RecordingStopError: If recording stop fails
        """
        logger.info(f"Finalizing recording for session {session_id}")

        # Get session data
        session_data = self.db_service.get_document("training_sessions", str(session_id))

        if not session_data:
            raise RecordingStopError(f"Session {session_id} not found")

        room_id = session_data.get("cloudflare_room_id")
        recording_id = session_data.get("recording_id")

        if not room_id or not recording_id:
            raise RecordingStopError(
                f"No active recording found for session {session_id}"
            )

        try:
            # Stop recording via Cloudflare Calls API
            stop_result = self.calls_service.stop_recording(room_id, recording_id)

            # Update session in database
            update_data = {
                "recording_status": RecordingStatus.PROCESSING.value,
                "recording_ended_at": datetime.utcnow().isoformat(),
                "video_duration_seconds": stop_result.get("duration_seconds")
            }

            self.db_service.update_document(
                "training_sessions",
                str(session_id),
                update_data
            )

            logger.info(f"Recording stopped successfully for session {session_id}")

            return {
                "session_id": str(session_id),
                "recording_id": recording_id,
                "status": RecordingStatus.PROCESSING.value,
                "ended_at": update_data["recording_ended_at"],
                "duration_seconds": update_data.get("video_duration_seconds")
            }

        except (CallsRecordingError, Exception) as e:
            error_message = f"Failed to stop recording: {str(e)}"
            logger.error(f"Error stopping recording for session {session_id}: {e}")

            # Update session with error
            self.db_service.update_document(
                "training_sessions",
                str(session_id),
                {
                    "recording_status": RecordingStatus.FAILED.value,
                    "recording_error": error_message
                }
            )

            raise RecordingStopError(error_message)

    def attach_recording(
        self,
        session_id: UUID,
        stream_id: str,
        stream_url: str,
        duration_seconds: Optional[int] = None,
        file_size_bytes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Attach processed recording VOD to training session

        Called by webhook handler when Cloudflare Stream upload completes

        Args:
            session_id: Training session UUID
            stream_id: Cloudflare Stream video ID
            stream_url: Playback URL for VOD
            duration_seconds: Video duration
            file_size_bytes: File size in bytes

        Returns:
            Updated session data
        """
        logger.info(f"Attaching recording VOD to session {session_id}")

        try:
            # Update session in database
            update_data = {
                "cloudflare_stream_id": stream_id,
                "vod_stream_url": stream_url,
                "recording_status": RecordingStatus.READY.value,
                "video_duration_seconds": duration_seconds,
                "recording_file_size_bytes": file_size_bytes,
                "recording_error": None
            }

            self.db_service.update_document(
                "training_sessions",
                str(session_id),
                update_data
            )

            logger.info(f"Recording VOD attached successfully to session {session_id}")

            return {
                "session_id": str(session_id),
                "stream_id": stream_id,
                "stream_url": stream_url,
                "status": RecordingStatus.READY.value
            }

        except Exception as e:
            error_message = f"Failed to attach recording: {str(e)}"
            logger.error(f"Error attaching recording to session {session_id}: {e}")
            raise RecordingServiceError(error_message)

    def get_recording_status(self, session_id: UUID) -> Dict[str, Any]:
        """
        Get current recording status for a session

        Args:
            session_id: Training session UUID

        Returns:
            Recording status data
        """
        logger.info(f"Getting recording status for session {session_id}")

        session_data = self.db_service.get_document("training_sessions", str(session_id))

        if not session_data:
            raise RecordingServiceError(f"Session {session_id} not found")

        return {
            "session_id": str(session_id),
            "recording_id": session_data.get("recording_id"),
            "recording_status": session_data.get("recording_status"),
            "recording_enabled": session_data.get("recording_enabled", True),
            "started_at": session_data.get("recording_started_at"),
            "ended_at": session_data.get("recording_ended_at"),
            "duration_seconds": session_data.get("video_duration_seconds"),
            "file_size_bytes": session_data.get("recording_file_size_bytes"),
            "stream_id": session_data.get("cloudflare_stream_id"),
            "stream_url": session_data.get("vod_stream_url"),
            "error": session_data.get("recording_error"),
            "retry_count": session_data.get("recording_retry_count", 0)
        }

    def generate_vod_signed_url(
        self,
        session_id: UUID,
        user_id: UUID,
        expiry_hours: int = 24
    ) -> str:
        """
        Generate signed URL for secure VOD playback

        Args:
            session_id: Training session UUID
            user_id: User requesting access
            expiry_hours: URL expiry in hours

        Returns:
            Signed playback URL

        Raises:
            RecordingServiceError: If URL generation fails
        """
        logger.info(f"Generating VOD signed URL for session {session_id}, user {user_id}")

        # Get session data
        session_data = self.db_service.get_document("training_sessions", str(session_id))

        if not session_data:
            raise RecordingServiceError(f"Session {session_id} not found")

        stream_id = session_data.get("cloudflare_stream_id")
        if not stream_id:
            raise RecordingServiceError(f"No VOD available for session {session_id}")

        # Check if recording is ready
        if session_data.get("recording_status") != RecordingStatus.READY.value:
            raise RecordingServiceError(
                f"Recording not ready (status: {session_data.get('recording_status')})"
            )

        # TODO: Verify user has access (members-only check)
        # This should check user's role/subscription status

        # Generate signed URL
        try:
            signed_url = self.stream_service.generate_signed_url(
                stream_id,
                expiry_hours=expiry_hours
            )

            logger.info(f"VOD signed URL generated for session {session_id}")

            return signed_url

        except StreamAPIError as e:
            error_message = f"Failed to generate signed URL: {str(e)}"
            logger.error(error_message)
            raise RecordingServiceError(error_message)

    def delete_recording(self, session_id: UUID) -> bool:
        """
        Delete recording from Cloudflare Stream (admin only)

        Args:
            session_id: Training session UUID

        Returns:
            True if deletion was successful

        Raises:
            RecordingServiceError: If deletion fails
        """
        logger.info(f"Deleting recording for session {session_id}")

        # Get session data
        session_data = self.db_service.get_document("training_sessions", str(session_id))

        if not session_data:
            raise RecordingServiceError(f"Session {session_id} not found")

        stream_id = session_data.get("cloudflare_stream_id")
        if not stream_id:
            logger.warning(f"No recording to delete for session {session_id}")
            return True

        try:
            # Delete from Cloudflare Stream
            success = self.stream_service.delete_video(stream_id)

            if success:
                # Update session in database
                self.db_service.update_document(
                    "training_sessions",
                    str(session_id),
                    {
                        "cloudflare_stream_id": None,
                        "vod_stream_url": None,
                        "recording_status": RecordingStatus.NOT_RECORDED.value
                    }
                )

                logger.info(f"Recording deleted successfully for session {session_id}")

            return success

        except Exception as e:
            error_message = f"Failed to delete recording: {str(e)}"
            logger.error(error_message)
            raise RecordingServiceError(error_message)

    def export_chat_to_storage(
        self,
        session_id: UUID,
        chat_messages: list
    ) -> str:
        """
        Export chat messages to JSON and upload to ZeroDB Object Storage

        Args:
            session_id: Training session UUID
            chat_messages: List of chat message dicts

        Returns:
            URL to chat transcript JSON file

        Raises:
            RecordingServiceError: If export fails
        """
        logger.info(f"Exporting chat transcript for session {session_id}")

        try:
            # Create chat transcript JSON
            chat_data = {
                "session_id": str(session_id),
                "message_count": len(chat_messages),
                "exported_at": datetime.utcnow().isoformat(),
                "messages": chat_messages
            }

            chat_json = json.dumps(chat_data, indent=2)

            # TODO: Upload to ZeroDB Object Storage
            # For now, just update the message count
            self.db_service.update_document(
                "training_sessions",
                str(session_id),
                {
                    "chat_message_count": len(chat_messages)
                }
            )

            logger.info(f"Chat transcript exported for session {session_id}")

            # Return placeholder URL
            # In production, this should be actual ZeroDB Object Storage URL
            chat_url = f"zerodb://chat-transcripts/{session_id}.json"

            return chat_url

        except Exception as e:
            error_message = f"Failed to export chat: {str(e)}"
            logger.error(error_message)
            raise RecordingServiceError(error_message)


# Global service instance
_recording_service_instance: Optional[RecordingService] = None


def get_recording_service() -> RecordingService:
    """
    Get or create the global RecordingService instance

    Returns:
        RecordingService instance
    """
    global _recording_service_instance

    if _recording_service_instance is None:
        _recording_service_instance = RecordingService()

    return _recording_service_instance
