"""
Subscriber Sync Service

Service for synchronizing newsletter subscribers between ZeroDB and BeeHiiv.
Handles bidirectional sync, unsubscribe management, and subscriber data consistency.

Usage:
    sync_service = SubscriberSyncService(db, beehiiv_service)
    await sync_service.sync_from_beehiiv()
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from services.beehiiv_service import BeeHiivService, BeeHiivAPIError
from database.zerodb import ZeroDBClient
from models.schemas import NewsletterSubscriber, NewsletterSubscriberStatus

logger = logging.getLogger(__name__)


class SubscriberSyncService:
    """
    Subscriber synchronization service

    Keeps newsletter subscribers in sync between ZeroDB and BeeHiiv.
    """

    def __init__(self, db: ZeroDBClient, beehiiv_service: BeeHiivService):
        """
        Initialize sync service

        Args:
            db: ZeroDB client instance
            beehiiv_service: BeeHiiv service instance
        """
        self.db = db
        self.beehiiv = beehiiv_service

    async def sync_subscriber_to_beehiiv(
        self,
        user_email: str,
        user_name: Optional[str] = None,
        list_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sync a subscriber from ZeroDB to BeeHiiv

        Args:
            user_email: Subscriber email
            user_name: Subscriber name
            list_id: Target list ID (optional)
            user_id: Associated user ID (optional)
            metadata: Additional subscriber metadata

        Returns:
            Sync result with subscriber data
        """
        try:
            # Add subscriber to BeeHiiv
            beehiiv_result = self.beehiiv.add_subscriber(
                email=user_email,
                name=user_name,
                list_id=list_id,
                metadata=metadata
            )

            # Check if subscriber exists in ZeroDB
            existing = await self.db.find_one(
                "newsletter_subscribers",
                {"email": user_email.lower()}
            )

            subscriber_data = {
                "email": user_email.lower(),
                "name": user_name,
                "list_ids": [list_id] if list_id else [],
                "status": NewsletterSubscriberStatus.ACTIVE,
                "subscribed_at": datetime.utcnow(),
                "beehiiv_subscriber_id": beehiiv_result.get("data", {}).get("id"),
                "last_synced_at": datetime.utcnow(),
                "user_id": user_id,
                "metadata": metadata or {}
            }

            if existing:
                # Update existing subscriber
                await self.db.update_one(
                    "newsletter_subscribers",
                    {"email": user_email.lower()},
                    {
                        "name": user_name,
                        "status": NewsletterSubscriberStatus.ACTIVE,
                        "last_synced_at": datetime.utcnow(),
                        "beehiiv_subscriber_id": beehiiv_result.get("data", {}).get("id"),
                        "updated_at": datetime.utcnow()
                    }
                )
                logger.info(f"Updated subscriber in ZeroDB: {user_email}")
            else:
                # Create new subscriber record
                subscriber_data["id"] = uuid4()
                subscriber_data["created_at"] = datetime.utcnow()
                subscriber_data["updated_at"] = datetime.utcnow()

                await self.db.insert_one("newsletter_subscribers", subscriber_data)
                logger.info(f"Created new subscriber in ZeroDB: {user_email}")

            return {
                "success": True,
                "email": user_email,
                "action": "updated" if existing else "created",
                "beehiiv_id": beehiiv_result.get("data", {}).get("id")
            }

        except BeeHiivAPIError as e:
            logger.error(f"Failed to sync subscriber to BeeHiiv: {str(e)}")
            return {
                "success": False,
                "email": user_email,
                "error": str(e)
            }

    async def sync_from_beehiiv(
        self,
        page_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Pull subscriber updates from BeeHiiv and sync to ZeroDB

        Args:
            page_limit: Maximum number of pages to fetch

        Returns:
            Sync statistics
        """
        logger.info("Starting BeeHiiv subscriber sync...")

        stats = {
            "total_fetched": 0,
            "updated": 0,
            "created": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }

        try:
            page = 1
            has_more = True

            while has_more and page <= page_limit:
                # Fetch subscribers from BeeHiiv
                result = self.beehiiv.list_subscribers(page=page, limit=100)

                subscribers = result.get("data", [])
                stats["total_fetched"] += len(subscribers)

                # Process each subscriber
                for subscriber in subscribers:
                    try:
                        email = subscriber.get("email", "").lower()
                        if not email:
                            continue

                        # Check if exists in ZeroDB
                        existing = await self.db.find_one(
                            "newsletter_subscribers",
                            {"email": email}
                        )

                        subscriber_data = {
                            "email": email,
                            "name": subscriber.get("name"),
                            "status": self._map_beehiiv_status(subscriber.get("status")),
                            "beehiiv_subscriber_id": subscriber.get("id"),
                            "last_synced_at": datetime.utcnow(),
                            "metadata": {
                                "utm_source": subscriber.get("utm_source"),
                                "utm_medium": subscriber.get("utm_medium"),
                                "referring_site": subscriber.get("referring_site")
                            }
                        }

                        if existing:
                            # Update existing
                            await self.db.update_one(
                                "newsletter_subscribers",
                                {"email": email},
                                {
                                    **subscriber_data,
                                    "updated_at": datetime.utcnow()
                                }
                            )
                            stats["updated"] += 1
                        else:
                            # Create new
                            subscriber_data["id"] = uuid4()
                            subscriber_data["list_ids"] = []
                            subscriber_data["subscribed_at"] = subscriber.get("created_at") or datetime.utcnow()
                            subscriber_data["created_at"] = datetime.utcnow()
                            subscriber_data["updated_at"] = datetime.utcnow()
                            subscriber_data["email_opens"] = 0
                            subscriber_data["email_clicks"] = 0

                            await self.db.insert_one("newsletter_subscribers", subscriber_data)
                            stats["created"] += 1

                    except Exception as e:
                        logger.error(f"Error processing subscriber {email}: {str(e)}")
                        stats["errors"] += 1

                # Check pagination
                pagination = result.get("pagination", {})
                has_more = pagination.get("has_more", False)
                page += 1

            # Update sync timestamp in config
            await self.db.update_one(
                "beehiiv_config",
                {},
                {"last_sync_at": datetime.utcnow()}
            )

            stats["end_time"] = datetime.utcnow()
            stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()

            logger.info(f"Sync completed: {stats}")
            return stats

        except BeeHiivAPIError as e:
            logger.error(f"BeeHiiv API error during sync: {str(e)}")
            stats["errors"] += 1
            stats["error_message"] = str(e)
            return stats

    async def handle_unsubscribe(
        self,
        email: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle unsubscribe request

        Updates both ZeroDB and BeeHiiv to mark subscriber as unsubscribed.

        Args:
            email: Subscriber email
            reason: Unsubscribe reason (optional)

        Returns:
            Unsubscribe result
        """
        try:
            # Unsubscribe from BeeHiiv
            beehiiv_result = self.beehiiv.remove_subscriber(email)

            # Update in ZeroDB
            await self.db.update_one(
                "newsletter_subscribers",
                {"email": email.lower()},
                {
                    "status": NewsletterSubscriberStatus.UNSUBSCRIBED,
                    "unsubscribed_at": datetime.utcnow(),
                    "last_synced_at": datetime.utcnow(),
                    "metadata.unsubscribe_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            )

            logger.info(f"Unsubscribed: {email}")

            return {
                "success": True,
                "email": email,
                "message": "Successfully unsubscribed"
            }

        except BeeHiivAPIError as e:
            logger.error(f"Failed to unsubscribe {email}: {str(e)}")
            return {
                "success": False,
                "email": email,
                "error": str(e)
            }

    async def bulk_sync_users_to_list(
        self,
        user_emails: List[str],
        list_id: str
    ) -> Dict[str, Any]:
        """
        Bulk sync multiple users to a specific list

        Args:
            user_emails: List of user emails
            list_id: Target list ID

        Returns:
            Bulk sync statistics
        """
        stats = {
            "total": len(user_emails),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for email in user_emails:
            result = await self.sync_subscriber_to_beehiiv(
                user_email=email,
                list_id=list_id
            )

            if result.get("success"):
                stats["success"] += 1
            else:
                stats["failed"] += 1
                stats["errors"].append({
                    "email": email,
                    "error": result.get("error")
                })

        logger.info(f"Bulk sync completed: {stats['success']}/{stats['total']} successful")
        return stats

    async def sync_member_subscriptions(self):
        """
        Sync all active members to the Members Only list

        Automatically subscribes all users with MEMBER role or higher
        to the members-only newsletter list.
        """
        # Get config to find members list ID
        config = await self.db.find_one("beehiiv_config", {})
        if not config or not config.get("list_ids", {}).get("members_only"):
            logger.warning("Members Only list ID not configured")
            return

        members_list_id = config["list_ids"]["members_only"]

        # Find all active members
        from models.schemas import UserRole
        members = await self.db.find(
            "users",
            {
                "role": {"$in": [UserRole.MEMBER, UserRole.INSTRUCTOR, UserRole.BOARD_MEMBER, UserRole.ADMIN]},
                "is_active": True
            }
        )

        # Get their profiles for names
        member_emails = []
        for member in members:
            # Get profile for name
            profile = await self.db.find_one("profiles", {"user_id": member["id"]})
            name = None
            if profile:
                name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

            await self.sync_subscriber_to_beehiiv(
                user_email=member["email"],
                user_name=name,
                list_id=members_list_id,
                user_id=member["id"]
            )
            member_emails.append(member["email"])

        logger.info(f"Synced {len(member_emails)} members to Members Only list")

    def _map_beehiiv_status(self, beehiiv_status: Optional[str]) -> str:
        """
        Map BeeHiiv status to NewsletterSubscriberStatus

        Args:
            beehiiv_status: BeeHiiv status string

        Returns:
            Mapped status
        """
        status_map = {
            "active": NewsletterSubscriberStatus.ACTIVE,
            "unsubscribed": NewsletterSubscriberStatus.UNSUBSCRIBED,
            "bounced": NewsletterSubscriberStatus.BOUNCED,
            "pending": NewsletterSubscriberStatus.PENDING
        }

        return status_map.get(
            beehiiv_status.lower() if beehiiv_status else "active",
            NewsletterSubscriberStatus.ACTIVE
        )

    async def cleanup_old_sync_data(self, days: int = 90):
        """
        Clean up old sync data

        Removes subscriber records that have been unsubscribed for longer
        than the specified number of days.

        Args:
            days: Number of days to retain unsubscribed data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.delete_many(
            "newsletter_subscribers",
            {
                "status": NewsletterSubscriberStatus.UNSUBSCRIBED,
                "unsubscribed_at": {"$lt": cutoff_date}
            }
        )

        logger.info(f"Cleaned up {result.get('deleted_count', 0)} old subscriber records")
        return result
