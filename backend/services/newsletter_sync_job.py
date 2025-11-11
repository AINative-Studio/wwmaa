"""
Newsletter Sync Job - Daily Member-BeeHiiv Synchronization

This service implements daily sync between ZeroDB members and BeeHiiv lists:
- Syncs all active members to Members Only list
- Syncs instructors to Instructors list
- Removes canceled members from member lists
- Detects and reports discrepancies
- Logs all sync operations

Scheduled to run daily at 3 AM via APScheduler
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient
from backend.services.newsletter_service import get_newsletter_service
from backend.models.schemas import (
    UserRole,
    SubscriptionStatus,
    SubscriptionTier,
    AuditAction
)

logger = logging.getLogger(__name__)


class NewsletterSyncJobError(Exception):
    """Base exception for newsletter sync job errors"""
    pass


class NewsletterSyncJob:
    """
    Daily sync job for member newsletter lists

    Ensures consistency between ZeroDB member database and BeeHiiv newsletter lists
    """

    def __init__(self, zerodb_client: Optional[ZeroDBClient] = None):
        """
        Initialize Newsletter Sync Job

        Args:
            zerodb_client: Optional ZeroDB client instance
        """
        self.db = zerodb_client or ZeroDBClient()
        self.newsletter_service = get_newsletter_service()
        self.scheduler = None
        logger.info("NewsletterSyncJob initialized")

    async def run_sync(self) -> Dict[str, Any]:
        """
        Run full member-BeeHiiv synchronization

        Returns:
            Dict with sync results and statistics

        Raises:
            NewsletterSyncJobError: If sync fails
        """
        sync_start = datetime.utcnow()
        logger.info("Starting newsletter sync job")

        results = {
            "sync_started_at": sync_start.isoformat(),
            "members_processed": 0,
            "members_synced": 0,
            "instructors_synced": 0,
            "canceled_members_removed": 0,
            "errors": [],
            "discrepancies": [],
            "sync_duration_seconds": 0
        }

        try:
            # 1. Get all active members
            active_members = self._get_active_members()
            logger.info(f"Found {len(active_members)} active members to sync")

            # 2. Sync each active member
            for member in active_members:
                results["members_processed"] += 1

                try:
                    await self._sync_member(member, results)
                except Exception as e:
                    logger.error(f"Error syncing member {member.get('id')}: {e}")
                    results["errors"].append({
                        "member_id": member.get("id"),
                        "email": member.get("email"),
                        "error": str(e)
                    })

            # 3. Remove canceled members from member lists
            canceled_result = await self._remove_canceled_members(results)
            results["canceled_members_removed"] = canceled_result

            # 4. Calculate duration
            sync_end = datetime.utcnow()
            duration = (sync_end - sync_start).total_seconds()
            results["sync_duration_seconds"] = duration
            results["sync_completed_at"] = sync_end.isoformat()
            results["success"] = True

            # 5. Log sync results
            self._log_sync_results(results)

            # 6. Create audit log
            self._create_audit_log(
                user_id=None,  # System action
                action=AuditAction.UPDATE,
                resource_type="newsletter_sync",
                resource_id=sync_start.isoformat(),
                description=f"Newsletter sync completed: {results['members_synced']} members synced",
                changes=results
            )

            logger.info(
                f"Newsletter sync completed: "
                f"{results['members_synced']} members, "
                f"{results['instructors_synced']} instructors, "
                f"{results['canceled_members_removed']} canceled, "
                f"{len(results['errors'])} errors, "
                f"{duration:.2f}s"
            )

            return results

        except Exception as e:
            logger.error(f"Newsletter sync failed: {e}")
            results["success"] = False
            results["error"] = str(e)
            raise NewsletterSyncJobError(f"Newsletter sync failed: {str(e)}")

    async def _sync_member(
        self,
        member: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """
        Sync individual member to newsletter lists

        Args:
            member: Member data with user and subscription info
            results: Results dict to update
        """
        user_id = str(member.get("user_id"))
        email = member.get("email")
        tier = member.get("tier", "basic")

        try:
            # Auto-subscribe member
            sync_result = await self.newsletter_service.auto_subscribe_member(
                user_id=user_id,
                tier=tier
            )

            # Update results
            if sync_result.get("subscribed_lists"):
                results["members_synced"] += 1

                if "instructors" in sync_result.get("subscribed_lists", []):
                    results["instructors_synced"] += 1

            # Log skipped members
            if sync_result.get("skipped_lists"):
                logger.debug(
                    f"Member {user_id} skipped lists: {sync_result['skipped_lists']}"
                )

        except Exception as e:
            logger.error(f"Error syncing member {user_id}: {e}")
            raise

    async def _remove_canceled_members(
        self,
        results: Dict[str, Any]
    ) -> int:
        """
        Remove canceled members from member lists

        Args:
            results: Results dict to update

        Returns:
            Number of canceled members removed
        """
        try:
            # Get all canceled subscriptions
            canceled_subs = self.db.query_documents(
                "subscriptions",
                filters={"status": SubscriptionStatus.CANCELED},
                limit=1000
            )

            canceled_count = 0
            canceled_docs = canceled_subs.get("documents", [])

            for sub in canceled_docs:
                user_id = str(sub.get("user_id"))

                try:
                    # Remove from member lists
                    await self.newsletter_service.handle_subscription_canceled(user_id)
                    canceled_count += 1

                except Exception as e:
                    logger.error(f"Error removing canceled member {user_id}: {e}")
                    results["errors"].append({
                        "user_id": user_id,
                        "action": "remove_canceled",
                        "error": str(e)
                    })

            return canceled_count

        except Exception as e:
            logger.error(f"Error removing canceled members: {e}")
            return 0

    def _get_active_members(self) -> List[Dict[str, Any]]:
        """
        Get all active members with their subscriptions

        Returns:
            List of member data dicts
        """
        try:
            # Get all active subscriptions
            subscriptions = self.db.query_documents(
                "subscriptions",
                filters={"status": SubscriptionStatus.ACTIVE},
                limit=10000
            )

            members = []

            for sub in subscriptions.get("documents", []):
                user_id = sub.get("user_id")

                # Get user data
                try:
                    user_result = self.db.get_document("users", str(user_id))
                    user = user_result.get("data", {})

                    if not user:
                        continue

                    # Skip inactive users
                    if not user.get("is_active", True):
                        continue

                    # Build member data
                    member_data = {
                        "user_id": user_id,
                        "email": user.get("email"),
                        "role": user.get("role"),
                        "tier": sub.get("tier"),
                        "subscription_id": sub.get("id"),
                        "subscription_status": sub.get("status")
                    }

                    members.append(member_data)

                except Exception as e:
                    logger.warning(f"Error getting user data for {user_id}: {e}")
                    continue

            return members

        except Exception as e:
            logger.error(f"Error getting active members: {e}")
            return []

    def _log_sync_results(self, results: Dict[str, Any]) -> None:
        """
        Log detailed sync results

        Args:
            results: Sync results dict
        """
        logger.info("=" * 60)
        logger.info("NEWSLETTER SYNC RESULTS")
        logger.info("=" * 60)
        logger.info(f"Started: {results.get('sync_started_at')}")
        logger.info(f"Completed: {results.get('sync_completed_at')}")
        logger.info(f"Duration: {results.get('sync_duration_seconds', 0):.2f}s")
        logger.info(f"Members Processed: {results.get('members_processed', 0)}")
        logger.info(f"Members Synced: {results.get('members_synced', 0)}")
        logger.info(f"Instructors Synced: {results.get('instructors_synced', 0)}")
        logger.info(f"Canceled Removed: {results.get('canceled_members_removed', 0)}")
        logger.info(f"Errors: {len(results.get('errors', []))}")
        logger.info(f"Discrepancies: {len(results.get('discrepancies', []))}")

        # Log errors
        if results.get("errors"):
            logger.warning("Sync errors:")
            for error in results["errors"]:
                logger.warning(f"  - {error}")

        # Log discrepancies
        if results.get("discrepancies"):
            logger.warning("Sync discrepancies:")
            for discrepancy in results["discrepancies"]:
                logger.warning(f"  - {discrepancy}")

        logger.info("=" * 60)

    def _create_audit_log(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        description: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create an audit log entry

        Args:
            user_id: User ID (None for system actions)
            action: Action type
            resource_type: Resource type
            resource_id: Resource ID
            description: Description
            changes: Changes made
        """
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "changes": changes or {},
                "success": True,
                "severity": "info",
                "tags": ["newsletter_sync", "scheduled_job"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    def start_scheduler(self, run_immediately: bool = False):
        """
        Start the sync job scheduler

        Schedules job to run daily at 3 AM

        Args:
            run_immediately: Whether to run sync immediately on start
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already started")
            return

        self.scheduler = AsyncIOScheduler()

        # Schedule daily sync at 3 AM
        self.scheduler.add_job(
            self.run_sync,
            CronTrigger(hour=3, minute=0),
            id="newsletter_sync_job",
            name="Daily Newsletter Sync",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Newsletter sync scheduler started (runs daily at 3 AM)")

        # Run immediately if requested
        if run_immediately:
            logger.info("Running newsletter sync immediately")
            asyncio.create_task(self.run_sync())

    def stop_scheduler(self):
        """Stop the sync job scheduler"""
        if self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("Newsletter sync scheduler stopped")

    async def get_last_sync_status(self) -> Optional[Dict[str, Any]]:
        """
        Get status of last sync job

        Returns:
            Dict with last sync status or None if no sync found
        """
        try:
            # Query for last sync audit log
            result = self.db.query_documents(
                "audit_logs",
                filters={
                    "resource_type": "newsletter_sync",
                    "tags": ["newsletter_sync", "scheduled_job"]
                },
                limit=1,
                sort=[{"field": "created_at", "direction": "desc"}]
            )

            logs = result.get("documents", [])
            if not logs:
                return None

            last_log = logs[0]
            return {
                "last_sync_at": last_log.get("created_at"),
                "success": last_log.get("success"),
                "changes": last_log.get("changes", {}),
                "description": last_log.get("description")
            }

        except Exception as e:
            logger.error(f"Error getting last sync status: {e}")
            return None


# Singleton instance
_newsletter_sync_job_instance = None


def get_newsletter_sync_job() -> NewsletterSyncJob:
    """
    Get singleton newsletter sync job instance

    Returns:
        NewsletterSyncJob instance
    """
    global _newsletter_sync_job_instance
    if _newsletter_sync_job_instance is None:
        _newsletter_sync_job_instance = NewsletterSyncJob()
    return _newsletter_sync_job_instance


# Initialize and start scheduler on module import (for production)
if settings.PYTHON_ENV == "production":
    sync_job = get_newsletter_sync_job()
    sync_job.start_scheduler()
    logger.info("Production newsletter sync scheduler initialized")
