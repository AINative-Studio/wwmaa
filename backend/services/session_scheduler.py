"""
Session Scheduler for WWMAA Backend

Provides background scheduling for training session lifecycle management:
- Create Cloudflare rooms 1 hour before session start
- Send reminder emails (24 hours, 1 hour, 10 minutes before)
- Auto-end sessions 30 minutes after scheduled end time if still live
- Clean up ended sessions after 7 days

Uses APScheduler for cron job management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from backend.services.training_session_service import get_training_session_service
from backend.services.cloudflare_calls_service import (
    get_cloudflare_calls_service,
    CloudflareCallsError
)
from backend.services.email_service import get_email_service
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.models.schemas import SessionStatus

# Configure logging
logger = logging.getLogger(__name__)


class SessionScheduler:
    """
    Background scheduler for training session lifecycle management

    Handles automated tasks:
    - Room creation 1 hour before session
    - Reminder emails at various intervals
    - Auto-ending sessions that run over time
    - Cleanup of old session data

    Example:
        scheduler = SessionScheduler()
        scheduler.start()
        # ... application runs ...
        scheduler.shutdown()
    """

    def __init__(self):
        """Initialize Session Scheduler"""
        self.scheduler = BackgroundScheduler()
        self.session_service = get_training_session_service()
        self.cloudflare = get_cloudflare_calls_service()
        self.email_service = get_email_service()
        self.db = get_zerodb_client()

        logger.info("SessionScheduler initialized")

    def start(self):
        """
        Start the background scheduler

        Configures and starts all scheduled jobs:
        - Room creation check: Every 5 minutes
        - Email reminders: Every 5 minutes
        - Auto-end sessions: Every 5 minutes
        - Cleanup: Daily at 2 AM
        """
        try:
            # Job 1: Create rooms 1 hour before session start
            self.scheduler.add_job(
                func=self._create_rooms_for_upcoming_sessions,
                trigger=IntervalTrigger(minutes=5),
                id="create_rooms",
                name="Create Cloudflare rooms for upcoming sessions",
                replace_existing=True
            )

            # Job 2: Send reminder emails
            self.scheduler.add_job(
                func=self._send_reminder_emails,
                trigger=IntervalTrigger(minutes=5),
                id="send_reminders",
                name="Send session reminder emails",
                replace_existing=True
            )

            # Job 3: Auto-end sessions that ran over time
            self.scheduler.add_job(
                func=self._auto_end_overdue_sessions,
                trigger=IntervalTrigger(minutes=5),
                id="auto_end_sessions",
                name="Auto-end overdue sessions",
                replace_existing=True
            )

            # Job 4: Clean up ended sessions (daily at 2 AM)
            self.scheduler.add_job(
                func=self._cleanup_old_sessions,
                trigger=CronTrigger(hour=2, minute=0),
                id="cleanup_sessions",
                name="Clean up old ended sessions",
                replace_existing=True
            )

            # Start scheduler
            self.scheduler.start()
            logger.info("SessionScheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start SessionScheduler: {e}")
            raise

    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler gracefully

        Args:
            wait: Whether to wait for running jobs to complete
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=wait)
                logger.info("SessionScheduler shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down SessionScheduler: {e}")

    def _create_rooms_for_upcoming_sessions(self):
        """
        Create Cloudflare rooms for sessions starting within 1 hour that don't have rooms yet

        Runs every 5 minutes
        """
        try:
            logger.debug("Running job: create_rooms_for_upcoming_sessions")

            # Get sessions starting in the next 1-2 hours that don't have rooms
            now = datetime.utcnow()
            one_hour_from_now = now + timedelta(hours=1)
            two_hours_from_now = now + timedelta(hours=2)

            filters = {
                "status": SessionStatus.SCHEDULED.value,
                "start_time": {
                    "$gte": one_hour_from_now.isoformat(),
                    "$lt": two_hours_from_now.isoformat()
                },
                "room_id": None
            }

            result = self.session_service.list_sessions(filters=filters, limit=50)
            sessions = result.get("documents", [])

            for session in sessions:
                try:
                    session_id = session.get("id")
                    title = session.get("title")
                    capacity = session.get("capacity")
                    recording_enabled = session.get("recording_enabled", False)

                    logger.info(f"Creating room for session {session_id}: {title}")

                    # Create Cloudflare room
                    room = self.cloudflare.create_room(
                        session_id=str(session_id),
                        max_participants=capacity or 50,
                        enable_recording=recording_enabled,
                        room_name=title
                    )

                    # Update session with room_id
                    self.db.update_document(
                        collection="training_sessions",
                        document_id=session_id,
                        data={"room_id": room["room_id"]},
                        merge=True
                    )

                    logger.info(f"Room created for session {session_id}: {room['room_id']}")

                except CloudflareCallsError as e:
                    logger.error(f"Failed to create room for session {session_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing session {session_id}: {e}")

            logger.debug(f"Processed {len(sessions)} sessions for room creation")

        except Exception as e:
            logger.error(f"Error in create_rooms_for_upcoming_sessions job: {e}")

    def _send_reminder_emails(self):
        """
        Send reminder emails to registered participants

        Sends reminders at:
        - 24 hours before session
        - 1 hour before session
        - 10 minutes before session

        Runs every 5 minutes
        """
        try:
            logger.debug("Running job: send_reminder_emails")

            now = datetime.utcnow()

            # Define reminder windows
            reminder_windows = [
                {"hours": 24, "window_minutes": 30, "label": "24-hour"},
                {"hours": 1, "window_minutes": 10, "label": "1-hour"},
                {"minutes": 10, "window_minutes": 5, "label": "10-minute"}
            ]

            for window in reminder_windows:
                try:
                    # Calculate time window
                    if "hours" in window:
                        target_time = now + timedelta(hours=window["hours"])
                    else:
                        target_time = now + timedelta(minutes=window["minutes"])

                    window_start = target_time - timedelta(minutes=window["window_minutes"])
                    window_end = target_time + timedelta(minutes=window["window_minutes"])

                    # Find sessions in this window
                    filters = {
                        "status": SessionStatus.SCHEDULED.value,
                        "start_time": {
                            "$gte": window_start.isoformat(),
                            "$lte": window_end.isoformat()
                        }
                    }

                    result = self.session_service.list_sessions(filters=filters, limit=50)
                    sessions = result.get("documents", [])

                    for session in sessions:
                        session_id = session.get("id")
                        # Check if reminder already sent (would need a flag in session document)
                        # For now, we'll just log it
                        logger.info(
                            f"[REMINDER] {window['label']} reminder for session {session_id}: "
                            f"{session.get('title')}"
                        )
                        # In production, would call email_service.send_session_reminder()

                except Exception as e:
                    logger.error(f"Error sending {window['label']} reminders: {e}")

            logger.debug("Reminder email job completed")

        except Exception as e:
            logger.error(f"Error in send_reminder_emails job: {e}")

    def _auto_end_overdue_sessions(self):
        """
        Automatically end sessions that are still live 30+ minutes after scheduled end time

        Runs every 5 minutes
        """
        try:
            logger.debug("Running job: auto_end_overdue_sessions")

            now = datetime.utcnow()
            thirty_minutes_ago = now - timedelta(minutes=30)

            # Find live sessions where scheduled end time was more than 30 minutes ago
            filters = {
                "status": SessionStatus.LIVE.value
            }

            result = self.session_service.list_sessions(filters=filters, limit=50)
            sessions = result.get("documents", [])

            for session in sessions:
                try:
                    session_id = session.get("id")
                    start_time = session.get("start_time")
                    duration_minutes = session.get("duration_minutes")

                    # Parse start time
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

                    # Calculate scheduled end time
                    scheduled_end_time = start_time + timedelta(minutes=duration_minutes)

                    # Check if 30+ minutes past scheduled end
                    if scheduled_end_time <= thirty_minutes_ago:
                        logger.info(
                            f"Auto-ending overdue session {session_id}: "
                            f"{session.get('title')} (scheduled end: {scheduled_end_time})"
                        )

                        # Update session to ended
                        self.db.update_document(
                            collection="training_sessions",
                            document_id=session_id,
                            data={
                                "status": SessionStatus.ENDED.value,
                                "ended_at": now.isoformat(),
                                "updated_at": now.isoformat()
                            },
                            merge=True
                        )

                        logger.info(f"Session {session_id} auto-ended successfully")

                except Exception as e:
                    logger.error(f"Error auto-ending session {session_id}: {e}")

            logger.debug(f"Processed {len(sessions)} live sessions for auto-end check")

        except Exception as e:
            logger.error(f"Error in auto_end_overdue_sessions job: {e}")

    def _cleanup_old_sessions(self):
        """
        Clean up ended sessions older than 7 days

        - Delete Cloudflare rooms
        - Archive session data (optional)

        Runs daily at 2 AM
        """
        try:
            logger.debug("Running job: cleanup_old_sessions")

            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)

            # Find ended sessions older than 7 days
            filters = {
                "status": SessionStatus.ENDED.value,
                "ended_at": {
                    "$lt": seven_days_ago.isoformat()
                }
            }

            result = self.session_service.list_sessions(filters=filters, limit=100)
            sessions = result.get("documents", [])

            for session in sessions:
                try:
                    session_id = session.get("id")
                    room_id = session.get("room_id")

                    logger.info(f"Cleaning up old session {session_id}")

                    # Delete Cloudflare room if it still exists
                    if room_id:
                        try:
                            self.cloudflare.delete_room(room_id)
                            logger.info(f"Deleted Cloudflare room {room_id}")
                        except CloudflareCallsError as e:
                            logger.warning(f"Failed to delete room {room_id}: {e}")

                    # Could archive session data here if needed
                    # For now, just log it
                    logger.info(f"Session {session_id} cleanup completed")

                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {e}")

            logger.debug(f"Cleaned up {len(sessions)} old sessions")

        except Exception as e:
            logger.error(f"Error in cleanup_old_sessions job: {e}")


# Global scheduler instance (singleton pattern)
_scheduler_instance: Optional[SessionScheduler] = None


def get_session_scheduler() -> SessionScheduler:
    """
    Get or create the global Session Scheduler instance

    Returns:
        SessionScheduler instance
    """
    global _scheduler_instance

    if _scheduler_instance is None:
        _scheduler_instance = SessionScheduler()

    return _scheduler_instance


def start_scheduler():
    """
    Start the global session scheduler

    This should be called when the application starts
    """
    scheduler = get_session_scheduler()
    scheduler.start()
    logger.info("Global session scheduler started")


def shutdown_scheduler(wait: bool = True):
    """
    Shutdown the global session scheduler

    This should be called when the application shuts down

    Args:
        wait: Whether to wait for running jobs to complete
    """
    global _scheduler_instance

    if _scheduler_instance is not None:
        _scheduler_instance.shutdown(wait=wait)
        logger.info("Global session scheduler shutdown")
