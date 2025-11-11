"""
Training Session Service for WWMAA Backend

Provides business logic for live training session management including:
- Session CRUD operations with Cloudflare Calls integration
- Session scheduling and lifecycle management
- Room creation and deletion
- Access control and capacity management
- Session status transitions (scheduled -> live -> ended)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from backend.services.zerodb_service import (
    get_zerodb_client,
    ZeroDBError,
    ZeroDBNotFoundError,
    ZeroDBValidationError
)
from backend.services.cloudflare_calls_service import (
    get_cloudflare_calls_service,
    CloudflareCallsError
)
from backend.models.schemas import UserRole

# Session status constants (since session_status is a string field in schema)
class SessionStatus:
    SCHEDULED = "scheduled"
    LIVE = "live"
    ENDED = "ended"
    CANCELED = "canceled"

# Configure logging
logger = logging.getLogger(__name__)


class TrainingSessionService:
    """
    Training Session Management Service

    Handles all business logic for live training session operations including:
    - Creating sessions with automatic Cloudflare room creation
    - Managing session lifecycle (scheduled/live/ended/canceled)
    - Access control and capacity management
    - Integration with events
    """

    def __init__(self):
        """Initialize Training Session Service"""
        self.db = get_zerodb_client()
        self.cloudflare = get_cloudflare_calls_service()
        self.collection = "training_sessions"
        self.attendance_collection = "session_attendance"

    def create_session(
        self,
        session_data: Dict[str, Any],
        instructor_id: UUID
    ) -> Dict[str, Any]:
        """
        Create a new training session and Cloudflare room

        Args:
            session_data: Session data dictionary with:
                - event_id (optional): UUID of associated event
                - title: Session title
                - description (optional): Session description
                - start_time: Session start datetime (ISO format)
                - duration_minutes: Duration in minutes (1-480)
                - capacity (optional): Maximum participants
                - recording_enabled: Enable recording (default: False)
                - chat_enabled: Enable chat (default: True)
            instructor_id: UUID of the instructor creating the session

        Returns:
            Created session with ID, room_id, and metadata

        Raises:
            ZeroDBValidationError: If session data is invalid
            CloudflareCallsError: If room creation fails
            ZeroDBError: If database operation fails
        """
        try:
            # Validate required fields
            if not session_data.get("title"):
                raise ZeroDBValidationError("Session title is required")

            if not session_data.get("session_date"):
                raise ZeroDBValidationError("Session session_date is required")

            if not session_data.get("duration_minutes"):
                raise ZeroDBValidationError("Session duration_minutes is required")

            # Parse and validate session_date
            session_date = session_data.get("session_date")
            if isinstance(session_date, str):
                session_date = datetime.fromisoformat(session_date.replace("Z", "+00:00"))

            # Validate start time is in the future
            if session_date <= datetime.utcnow():
                raise ZeroDBValidationError("Session session_date must be in the future")

            # Validate duration
            duration = session_data.get("duration_minutes")
            if duration < 1 or duration > 480:
                raise ZeroDBValidationError("Session duration must be between 1 and 480 minutes")

            # Validate capacity if provided
            capacity = session_data.get("capacity")
            if capacity is not None and capacity < 1:
                raise ZeroDBValidationError("Session capacity must be at least 1")

            # Check if event exists if event_id provided
            event_id = session_data.get("event_id")
            if event_id:
                try:
                    event = self.db.get_document(collection="events", document_id=str(event_id))
                    if not event:
                        raise ZeroDBValidationError(f"Event not found: {event_id}")
                except ZeroDBNotFoundError:
                    raise ZeroDBValidationError(f"Event not found: {event_id}")

            # Prepare session document
            session_doc = {
                "event_id": str(event_id) if event_id else None,
                "title": session_data.get("title"),
                "description": session_data.get("description"),
                "instructor_id": str(instructor_id),
                "session_date": session_date.isoformat() if isinstance(session_date, datetime) else session_date,
                "duration_minutes": duration,
                "max_participants": capacity,
                "recording_enabled": session_data.get("recording_enabled", False),
                "session_status": SessionStatus.SCHEDULED,
                "cloudflare_room_id": None,  # Will be set when room is created
                "started_at": None,
                "ended_at": None,
                "is_public": session_data.get("is_public", False),
                "members_only": session_data.get("members_only", True),
                "tags": session_data.get("tags", [])
            }

            logger.info(f"Creating training session: {session_doc.get('title')}")

            # Create session in ZeroDB first
            result = self.db.create_document(
                collection=self.collection,
                data=session_doc
            )

            session_id = result.get("id")

            # Try to create Cloudflare room immediately (can also be done by scheduler 1 hour before)
            # This allows immediate testing and flexibility
            try:
                room = self.cloudflare.create_room(
                    session_id=str(session_id),
                    max_participants=capacity or 50,
                    enable_recording=session_doc["recording_enabled"],
                    room_name=session_doc["title"]
                )

                # Update session with cloudflare_room_id
                self.db.update_document(
                    collection=self.collection,
                    document_id=session_id,
                    data={"cloudflare_room_id": room["room_id"]},
                    merge=True
                )

                result["cloudflare_room_id"] = room["room_id"]
                logger.info(f"Cloudflare room created for session {session_id}: {room['room_id']}")

            except CloudflareCallsError as e:
                # Log error but don't fail - room can be created later by scheduler
                logger.warning(f"Failed to create Cloudflare room immediately: {e}")
                logger.info("Room will be created automatically 1 hour before session start")

            logger.info(f"Training session created successfully with ID: {session_id}")
            return result

        except ZeroDBValidationError:
            raise
        except CloudflareCallsError as e:
            logger.error(f"Cloudflare error creating session: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create training session: {e}")
            raise ZeroDBError(f"Failed to create training session: {e}")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get a training session by ID

        Args:
            session_id: Session ID

        Returns:
            Session data

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBError: If retrieval fails
        """
        try:
            logger.info(f"Fetching training session: {session_id}")
            session = self.db.get_document(
                collection=self.collection,
                document_id=session_id
            )

            return session

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch training session: {e}")
            raise ZeroDBError(f"Failed to fetch training session: {e}")

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any],
        updated_by: UUID
    ) -> Dict[str, Any]:
        """
        Update an existing training session

        Args:
            session_id: Session ID
            updates: Updated session data
            updated_by: UUID of user updating the session

        Returns:
            Updated session data

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBValidationError: If data is invalid
            ZeroDBError: If update fails
        """
        try:
            # Check if session exists
            existing_session = self.get_session(session_id)

            # Don't allow updates to ended or canceled sessions
            if existing_session.get("status") in [SessionStatus.ENDED.value, SessionStatus.CANCELED.value]:
                raise ZeroDBValidationError("Cannot update ended or canceled sessions")

            # Validate start_time if provided
            if "start_time" in updates:
                start_time = updates["start_time"]
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

                # Only validate future time if session is still scheduled
                if existing_session.get("status") == SessionStatus.SCHEDULED.value:
                    if start_time <= datetime.utcnow():
                        raise ZeroDBValidationError("Session start_time must be in the future")

            # Validate duration if provided
            if "duration_minutes" in updates:
                duration = updates["duration_minutes"]
                if duration < 1 or duration > 480:
                    raise ZeroDBValidationError("Session duration must be between 1 and 480 minutes")

            # Validate capacity if provided
            if "capacity" in updates:
                capacity = updates["capacity"]
                if capacity is not None and capacity < 1:
                    raise ZeroDBValidationError("Session capacity must be at least 1")

            # Add audit fields
            updates["updated_at"] = datetime.utcnow().isoformat()

            # Update session in ZeroDB
            logger.info(f"Updating training session: {session_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=session_id,
                data=updates,
                merge=True
            )

            logger.info(f"Training session updated successfully: {session_id}")
            return result

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update training session: {e}")
            raise ZeroDBError(f"Failed to update training session: {e}")

    def delete_session(
        self,
        session_id: str,
        deleted_by: UUID
    ) -> Dict[str, Any]:
        """
        Cancel a training session and delete its Cloudflare room

        Args:
            session_id: Session ID
            deleted_by: UUID of user deleting the session

        Returns:
            Deletion confirmation

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBError: If deletion fails
        """
        try:
            # Check if session exists
            session = self.get_session(session_id)

            # Delete Cloudflare room if it exists
            room_id = session.get("room_id")
            if room_id:
                try:
                    self.cloudflare.delete_room(room_id)
                    logger.info(f"Cloudflare room deleted: {room_id}")
                except CloudflareCallsError as e:
                    logger.warning(f"Failed to delete Cloudflare room: {e}")

            # Mark session as canceled
            logger.info(f"Canceling training session: {session_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=session_id,
                data={
                    "status": SessionStatus.CANCELED.value,
                    "updated_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Training session canceled successfully: {session_id}")
            return result

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete training session: {e}")
            raise ZeroDBError(f"Failed to delete training session: {e}")

    def list_sessions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "start_time",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        List training sessions with filtering and pagination

        Args:
            filters: Filter criteria (e.g., {"status": "scheduled", "instructor_id": "..."})
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            sort_by: Field to sort by (default: start_time)
            sort_order: Sort order (asc or desc)

        Returns:
            Dictionary with sessions list and metadata

        Raises:
            ZeroDBError: If query fails
        """
        try:
            query_filters = filters or {}
            sort_criteria = {sort_by: sort_order}

            logger.info(f"Listing training sessions with filters: {query_filters}")
            result = self.db.query_documents(
                collection=self.collection,
                filters=query_filters,
                limit=limit,
                offset=offset,
                sort=sort_criteria
            )

            return result

        except Exception as e:
            logger.error(f"Failed to list training sessions: {e}")
            raise ZeroDBError(f"Failed to list training sessions: {e}")

    def get_upcoming_sessions(
        self,
        limit: int = 10,
        instructor_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming scheduled sessions

        Args:
            limit: Maximum number of sessions to return
            instructor_id: Optional filter by instructor

        Returns:
            List of upcoming sessions

        Raises:
            ZeroDBError: If query fails
        """
        try:
            filters = {
                "status": SessionStatus.SCHEDULED.value,
                "start_time": {"$gte": datetime.utcnow().isoformat()}
            }

            if instructor_id:
                filters["instructor_id"] = str(instructor_id)

            result = self.list_sessions(
                filters=filters,
                limit=limit,
                sort_by="start_time",
                sort_order="asc"
            )

            return result.get("documents", [])

        except Exception as e:
            logger.error(f"Failed to get upcoming sessions: {e}")
            raise ZeroDBError(f"Failed to get upcoming sessions: {e}")

    def start_session(
        self,
        session_id: str,
        instructor_id: UUID
    ) -> Dict[str, Any]:
        """
        Mark a session as live

        Args:
            session_id: Session ID
            instructor_id: UUID of instructor starting the session

        Returns:
            Updated session data

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBValidationError: If session cannot be started
            ZeroDBError: If update fails
        """
        try:
            # Check if session exists
            session = self.get_session(session_id)

            # Verify instructor
            if str(session.get("instructor_id")) != str(instructor_id):
                raise ZeroDBValidationError("Only the session instructor can start the session")

            # Verify session is scheduled
            if session.get("status") != SessionStatus.SCHEDULED.value:
                raise ZeroDBValidationError(f"Cannot start session with status: {session.get('status')}")

            # Ensure room exists
            if not session.get("room_id"):
                raise ZeroDBValidationError("Session room has not been created yet")

            # Update session to live
            logger.info(f"Starting training session: {session_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=session_id,
                data={
                    "status": SessionStatus.LIVE.value,
                    "started_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Training session started successfully: {session_id}")
            return result

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to start training session: {e}")
            raise ZeroDBError(f"Failed to start training session: {e}")

    def end_session(
        self,
        session_id: str,
        instructor_id: UUID
    ) -> Dict[str, Any]:
        """
        Mark a session as ended

        Args:
            session_id: Session ID
            instructor_id: UUID of instructor ending the session

        Returns:
            Updated session data

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBValidationError: If session cannot be ended
            ZeroDBError: If update fails
        """
        try:
            # Check if session exists
            session = self.get_session(session_id)

            # Verify instructor
            if str(session.get("instructor_id")) != str(instructor_id):
                raise ZeroDBValidationError("Only the session instructor can end the session")

            # Verify session is live
            if session.get("status") != SessionStatus.LIVE.value:
                raise ZeroDBValidationError(f"Cannot end session with status: {session.get('status')}")

            # Update session to ended
            logger.info(f"Ending training session: {session_id}")
            result = self.db.update_document(
                collection=self.collection,
                document_id=session_id,
                data={
                    "status": SessionStatus.ENDED.value,
                    "ended_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Training session ended successfully: {session_id}")
            return result

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to end training session: {e}")
            raise ZeroDBError(f"Failed to end training session: {e}")

    def can_user_join(
        self,
        session_id: str,
        user_id: UUID,
        user_role: str
    ) -> Dict[str, Any]:
        """
        Check if a user can join a training session

        Args:
            session_id: Session ID
            user_id: User's UUID
            user_role: User's role

        Returns:
            Dictionary with:
                - can_join: bool
                - reason: str (if can't join)
                - join_time_remaining: int (seconds until can join)

        Raises:
            ZeroDBNotFoundError: If session doesn't exist
            ZeroDBError: If check fails
        """
        try:
            # Get session
            session = self.get_session(session_id)

            # Check if session is canceled
            if session.get("status") == SessionStatus.CANCELED.value:
                return {
                    "can_join": False,
                    "reason": "Session has been canceled"
                }

            # Check if session has ended
            if session.get("status") == SessionStatus.ENDED.value:
                return {
                    "can_join": False,
                    "reason": "Session has ended"
                }

            # Parse start time
            start_time = session.get("start_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

            # Check if session is live
            if session.get("status") == SessionStatus.LIVE.value:
                # Can join if session is live (anytime during the session)
                return {
                    "can_join": True,
                    "reason": "Session is live"
                }

            # Check if within 10 minutes before start
            time_until_start = (start_time - datetime.utcnow()).total_seconds()

            if time_until_start > 600:  # More than 10 minutes
                return {
                    "can_join": False,
                    "reason": "Session join opens 10 minutes before start time",
                    "join_time_remaining": int(time_until_start - 600)
                }

            # Check capacity
            capacity = session.get("capacity")
            current_participants = session.get("current_participants", 0)

            if capacity and current_participants >= capacity:
                return {
                    "can_join": False,
                    "reason": "Session is at full capacity"
                }

            # Check access control
            if session.get("members_only") and user_role == UserRole.PUBLIC.value:
                return {
                    "can_join": False,
                    "reason": "This session is for members only"
                }

            # All checks passed
            return {
                "can_join": True,
                "reason": "User can join session"
            }

        except ZeroDBNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to check user join permission: {e}")
            raise ZeroDBError(f"Failed to check user join permission: {e}")


# Global service instance (singleton pattern)
_service_instance: Optional[TrainingSessionService] = None


def get_training_session_service() -> TrainingSessionService:
    """
    Get or create the global Training Session Service instance

    Returns:
        TrainingSessionService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = TrainingSessionService()

    return _service_instance
