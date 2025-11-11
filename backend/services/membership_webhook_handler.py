"""
Membership Webhook Handler - Auto-Subscribe Newsletter Integration

This service handles webhook events for membership lifecycle:
- Application approval -> Auto-subscribe to Members Only list
- Subscription created -> Auto-subscribe to Members Only list
- Tier upgrade -> Add to Instructors list
- Subscription canceled -> Remove from Members Only, keep in General
- Email changed -> Sync across all BeeHiiv lists

Integrates with existing webhook system from Sprint 3 (US-023)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.services.newsletter_service import get_newsletter_service
from backend.models.schemas import SubscriptionTier, SubscriptionStatus, AuditAction

logger = logging.getLogger(__name__)


class MembershipWebhookHandlerError(Exception):
    """Base exception for membership webhook handler errors"""
    pass


class MembershipWebhookHandler:
    """
    Handler for membership lifecycle webhook events

    Automatically manages newsletter subscriptions based on membership status changes
    """

    def __init__(self, zerodb_client: Optional[ZeroDBClient] = None):
        """
        Initialize Membership Webhook Handler

        Args:
            zerodb_client: Optional ZeroDB client instance
        """
        self.db = zerodb_client or ZeroDBClient()
        self.newsletter_service = get_newsletter_service()
        logger.info("MembershipWebhookHandler initialized")

    async def handle_application_approved(self, application_id: str) -> Dict[str, Any]:
        """
        Handle application approval event

        Auto-subscribes approved applicant to newsletter based on tier

        Args:
            application_id: Application ID

        Returns:
            Dict with processing results

        Raises:
            MembershipWebhookHandlerError: If processing fails
        """
        try:
            # Get application data
            app_result = self.db.get_document("applications", application_id)
            application = app_result.get("data", {})

            if not application:
                raise MembershipWebhookHandlerError(f"Application {application_id} not found")

            user_id = str(application.get("user_id"))
            tier = application.get("subscription_tier", "basic")

            logger.info(
                f"Processing application approval for newsletter: "
                f"application_id={application_id}, user_id={user_id}, tier={tier}"
            )

            # Auto-subscribe to newsletter
            result = await self.newsletter_service.auto_subscribe_member(
                user_id=user_id,
                tier=tier
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="membership_webhook",
                resource_id=application_id,
                description="Processed application approval webhook - auto-subscribed to newsletter",
                changes={
                    "event": "application_approved",
                    "newsletter_result": result
                }
            )

            logger.info(
                f"Application approval processed: {application_id} -> "
                f"subscribed to {result.get('subscribed_lists', [])}"
            )

            return {
                "success": True,
                "event": "application_approved",
                "application_id": application_id,
                "user_id": user_id,
                "newsletter_result": result
            }

        except Exception as e:
            logger.error(f"Error handling application approval: {e}")
            raise MembershipWebhookHandlerError(f"Failed to handle application approval: {str(e)}")

    async def handle_subscription_created(self, subscription_id: str) -> Dict[str, Any]:
        """
        Handle subscription creation event (first payment)

        Auto-subscribes member to newsletter if not already subscribed

        Args:
            subscription_id: Subscription ID

        Returns:
            Dict with processing results

        Raises:
            MembershipWebhookHandlerError: If processing fails
        """
        try:
            # Get subscription data
            sub_result = self.db.get_document("subscriptions", subscription_id)
            subscription = sub_result.get("data", {})

            if not subscription:
                raise MembershipWebhookHandlerError(f"Subscription {subscription_id} not found")

            user_id = str(subscription.get("user_id"))
            tier = subscription.get("tier", "basic")

            logger.info(
                f"Processing subscription creation for newsletter: "
                f"subscription_id={subscription_id}, user_id={user_id}, tier={tier}"
            )

            # Auto-subscribe to newsletter
            result = await self.newsletter_service.auto_subscribe_member(
                user_id=user_id,
                tier=tier
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="membership_webhook",
                resource_id=subscription_id,
                description="Processed subscription creation webhook - auto-subscribed to newsletter",
                changes={
                    "event": "subscription_created",
                    "newsletter_result": result
                }
            )

            logger.info(
                f"Subscription creation processed: {subscription_id} -> "
                f"subscribed to {result.get('subscribed_lists', [])}"
            )

            return {
                "success": True,
                "event": "subscription_created",
                "subscription_id": subscription_id,
                "user_id": user_id,
                "newsletter_result": result
            }

        except Exception as e:
            logger.error(f"Error handling subscription creation: {e}")
            raise MembershipWebhookHandlerError(f"Failed to handle subscription creation: {str(e)}")

    async def handle_tier_upgrade(
        self,
        user_id: str,
        old_tier: str,
        new_tier: str
    ) -> Dict[str, Any]:
        """
        Handle subscription tier upgrade

        Adds member to Instructors list if upgrading to lifetime/instructor tier

        Args:
            user_id: User ID
            old_tier: Previous tier
            new_tier: New tier

        Returns:
            Dict with processing results

        Raises:
            MembershipWebhookHandlerError: If processing fails
        """
        try:
            logger.info(
                f"Processing tier upgrade for newsletter: "
                f"user_id={user_id}, old_tier={old_tier}, new_tier={new_tier}"
            )

            results = {
                "success": True,
                "event": "tier_upgrade",
                "user_id": user_id,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "newsletter_changes": []
            }

            # If upgrading to Instructor tier, add to Instructors list
            if new_tier in ["lifetime", SubscriptionTier.LIFETIME]:
                if old_tier not in ["lifetime", SubscriptionTier.LIFETIME]:
                    result = await self.newsletter_service.upgrade_to_instructor(user_id)
                    results["newsletter_changes"].append({
                        "action": "added_to_instructors",
                        "result": result
                    })

            # If downgrading from Instructor tier, remove from Instructors list
            if old_tier in ["lifetime", SubscriptionTier.LIFETIME]:
                if new_tier not in ["lifetime", SubscriptionTier.LIFETIME]:
                    result = await self.newsletter_service.downgrade_from_instructor(user_id)
                    results["newsletter_changes"].append({
                        "action": "removed_from_instructors",
                        "result": result
                    })

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="membership_webhook",
                resource_id=user_id,
                description=f"Processed tier upgrade webhook: {old_tier} -> {new_tier}",
                changes={
                    "event": "tier_upgrade",
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "newsletter_changes": results["newsletter_changes"]
                }
            )

            logger.info(
                f"Tier upgrade processed: {user_id} from {old_tier} to {new_tier}"
            )

            return results

        except Exception as e:
            logger.error(f"Error handling tier upgrade: {e}")
            raise MembershipWebhookHandlerError(f"Failed to handle tier upgrade: {str(e)}")

    async def handle_subscription_canceled(self, subscription_id: str) -> Dict[str, Any]:
        """
        Handle subscription cancellation

        Removes member from Members Only and Instructors lists,
        but keeps in General list if they subscribed publicly

        Args:
            subscription_id: Subscription ID

        Returns:
            Dict with processing results

        Raises:
            MembershipWebhookHandlerError: If processing fails
        """
        try:
            # Get subscription data
            sub_result = self.db.get_document("subscriptions", subscription_id)
            subscription = sub_result.get("data", {})

            if not subscription:
                raise MembershipWebhookHandlerError(f"Subscription {subscription_id} not found")

            user_id = str(subscription.get("user_id"))

            logger.info(
                f"Processing subscription cancellation for newsletter: "
                f"subscription_id={subscription_id}, user_id={user_id}"
            )

            # Handle newsletter unsubscribes
            result = await self.newsletter_service.handle_subscription_canceled(user_id)

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="membership_webhook",
                resource_id=subscription_id,
                description="Processed subscription cancellation webhook - removed from member lists",
                changes={
                    "event": "subscription_canceled",
                    "newsletter_result": result
                }
            )

            logger.info(
                f"Subscription cancellation processed: {subscription_id} -> "
                f"removed from {result.get('unsubscribed_lists', [])}"
            )

            return {
                "success": True,
                "event": "subscription_canceled",
                "subscription_id": subscription_id,
                "user_id": user_id,
                "newsletter_result": result
            }

        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            raise MembershipWebhookHandlerError(f"Failed to handle subscription cancellation: {str(e)}")

    async def handle_email_changed(
        self,
        user_id: str,
        old_email: str,
        new_email: str
    ) -> Dict[str, Any]:
        """
        Handle user email change

        Syncs email change across all BeeHiiv lists

        Args:
            user_id: User ID
            old_email: Old email address
            new_email: New email address

        Returns:
            Dict with processing results

        Raises:
            MembershipWebhookHandlerError: If processing fails
        """
        try:
            logger.info(
                f"Processing email change for newsletter: "
                f"user_id={user_id}, old_email={old_email}, new_email={new_email}"
            )

            # Sync email change in BeeHiiv
            result = await self.newsletter_service.sync_email_change(
                old_email=old_email,
                new_email=new_email
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="membership_webhook",
                resource_id=user_id,
                description=f"Processed email change webhook: {old_email} -> {new_email}",
                changes={
                    "event": "email_changed",
                    "old_email": old_email,
                    "new_email": new_email,
                    "newsletter_result": result
                }
            )

            logger.info(
                f"Email change processed: {user_id} from {old_email} to {new_email}"
            )

            return {
                "success": True,
                "event": "email_changed",
                "user_id": user_id,
                "old_email": old_email,
                "new_email": new_email,
                "newsletter_result": result
            }

        except Exception as e:
            logger.error(f"Error handling email change: {e}")
            raise MembershipWebhookHandlerError(f"Failed to handle email change: {str(e)}")

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
                "tags": ["membership_webhook", "newsletter", "auto_subscribe"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


# Singleton instance
_membership_webhook_handler_instance = None


def get_membership_webhook_handler() -> MembershipWebhookHandler:
    """
    Get singleton membership webhook handler instance

    Returns:
        MembershipWebhookHandler instance
    """
    global _membership_webhook_handler_instance
    if _membership_webhook_handler_instance is None:
        _membership_webhook_handler_instance = MembershipWebhookHandler()
    return _membership_webhook_handler_instance
