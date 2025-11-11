"""
Subscription Service - Membership Subscription Lifecycle Management

This service manages subscription lifecycle with newsletter integration:
- Create subscription -> Auto-subscribe to Members Only list
- Upgrade subscription -> Update newsletter lists based on tier
- Cancel subscription -> Remove from member lists
- Reactivate subscription -> Re-add to member lists

Integrates with:
- Stripe for payment processing
- BeeHiiv for newsletter management (US-059)
- ZeroDB for subscription storage
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient, ZeroDBNotFoundError
from backend.services.membership_webhook_handler import get_membership_webhook_handler
from backend.models.schemas import (
    SubscriptionTier,
    SubscriptionStatus,
    AuditAction
)

logger = logging.getLogger(__name__)


class SubscriptionServiceError(Exception):
    """Base exception for subscription service errors"""
    pass


class SubscriptionNotFoundError(SubscriptionServiceError):
    """Exception raised when subscription is not found"""
    pass


class SubscriptionService:
    """
    Service for managing membership subscriptions

    Implements:
    - Subscription creation with newsletter integration
    - Subscription upgrades/downgrades
    - Subscription cancellation
    - Subscription reactivation
    """

    def __init__(self, zerodb_client: Optional[ZeroDBClient] = None):
        """
        Initialize Subscription Service

        Args:
            zerodb_client: Optional ZeroDB client instance
        """
        self.db = zerodb_client or ZeroDBClient()
        self.webhook_handler = get_membership_webhook_handler()
        logger.info("SubscriptionService initialized")

    async def create_subscription(
        self,
        user_id: str,
        tier: str,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        amount: float = 0.0,
        interval: str = "year"
    ) -> Dict[str, Any]:
        """
        Create new subscription and auto-subscribe to newsletter

        Args:
            user_id: User ID
            tier: Subscription tier (basic, premium, lifetime)
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID
            amount: Subscription amount
            interval: Billing interval (month, year)

        Returns:
            Dict with subscription data

        Raises:
            SubscriptionServiceError: If creation fails
        """
        try:
            # Calculate dates
            start_date = datetime.utcnow()
            end_date = None

            if interval == "year":
                end_date = start_date + timedelta(days=365)
            elif interval == "month":
                end_date = start_date + timedelta(days=30)
            # lifetime has no end_date

            # Create subscription record
            subscription_data = {
                "user_id": user_id,
                "tier": tier,
                "status": SubscriptionStatus.ACTIVE,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "amount": amount,
                "currency": "USD",
                "interval": interval,
                "features": self._get_tier_features(tier),
                "metadata": {}
            }

            result = self.db.create_document("subscriptions", subscription_data)
            subscription = result.get("data", {})
            subscription_id = result.get("id")

            logger.info(
                f"Subscription created: {subscription_id} for user {user_id}, tier {tier}"
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="subscriptions",
                resource_id=subscription_id,
                description=f"Subscription created: {tier}",
                changes={
                    "tier": tier,
                    "amount": amount,
                    "interval": interval
                }
            )

            # Auto-subscribe to newsletter (US-059)
            try:
                newsletter_result = await self.webhook_handler.handle_subscription_created(
                    subscription_id
                )
                logger.info(
                    f"Newsletter subscription triggered for subscription {subscription_id}"
                )
            except Exception as e:
                logger.error(f"Failed to trigger newsletter subscription: {e}")
                # Don't fail subscription creation if newsletter fails

            return {
                "success": True,
                "subscription_id": subscription_id,
                "subscription": subscription,
                "newsletter_result": newsletter_result if 'newsletter_result' in locals() else None
            }

        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise SubscriptionServiceError(f"Failed to create subscription: {str(e)}")

    async def upgrade_subscription(
        self,
        subscription_id: str,
        new_tier: str,
        new_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Upgrade subscription tier and update newsletter lists

        Args:
            subscription_id: Subscription ID
            new_tier: New subscription tier
            new_amount: New subscription amount (optional)

        Returns:
            Dict with updated subscription data

        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionServiceError: If upgrade fails
        """
        try:
            # Get current subscription
            sub_result = self.db.get_document("subscriptions", subscription_id)
            subscription = sub_result.get("data", {})

            if not subscription:
                raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

            old_tier = subscription.get("tier")
            user_id = str(subscription.get("user_id"))

            # Update subscription
            update_data = {
                "tier": new_tier,
                "features": self._get_tier_features(new_tier),
                "updated_at": datetime.utcnow().isoformat()
            }

            if new_amount is not None:
                update_data["amount"] = new_amount

            updated_result = self.db.update_document(
                "subscriptions",
                subscription_id,
                update_data,
                merge=True
            )

            updated_subscription = updated_result.get("data", {})

            logger.info(
                f"Subscription upgraded: {subscription_id} from {old_tier} to {new_tier}"
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="subscriptions",
                resource_id=subscription_id,
                description=f"Subscription upgraded: {old_tier} -> {new_tier}",
                changes={
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "new_amount": new_amount
                }
            )

            # Update newsletter lists (US-059)
            try:
                newsletter_result = await self.webhook_handler.handle_tier_upgrade(
                    user_id=user_id,
                    old_tier=old_tier,
                    new_tier=new_tier
                )
                logger.info(
                    f"Newsletter lists updated for tier upgrade: {subscription_id}"
                )
            except Exception as e:
                logger.error(f"Failed to update newsletter lists: {e}")
                # Don't fail upgrade if newsletter update fails

            return {
                "success": True,
                "subscription_id": subscription_id,
                "subscription": updated_subscription,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "newsletter_result": newsletter_result if 'newsletter_result' in locals() else None
            }

        except ZeroDBNotFoundError:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            raise SubscriptionServiceError(f"Failed to upgrade subscription: {str(e)}")

    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: Optional[str] = None,
        cancel_at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel subscription and update newsletter lists

        Args:
            subscription_id: Subscription ID
            reason: Cancellation reason
            cancel_at_period_end: Whether to cancel at period end or immediately

        Returns:
            Dict with cancellation details

        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionServiceError: If cancellation fails
        """
        try:
            # Get subscription
            sub_result = self.db.get_document("subscriptions", subscription_id)
            subscription = sub_result.get("data", {})

            if not subscription:
                raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

            user_id = str(subscription.get("user_id"))

            # Update subscription status
            update_data = {
                "status": SubscriptionStatus.CANCELED,
                "canceled_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    **subscription.get("metadata", {}),
                    "cancellation_reason": reason or "",
                    "cancel_at_period_end": cancel_at_period_end
                }
            }

            # If not canceling at period end, set end_date to now
            if not cancel_at_period_end:
                update_data["end_date"] = datetime.utcnow().isoformat()

            updated_result = self.db.update_document(
                "subscriptions",
                subscription_id,
                update_data,
                merge=True
            )

            updated_subscription = updated_result.get("data", {})

            logger.info(
                f"Subscription canceled: {subscription_id} "
                f"(cancel_at_period_end={cancel_at_period_end})"
            )

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="subscriptions",
                resource_id=subscription_id,
                description=f"Subscription canceled: {reason or 'No reason provided'}",
                changes={
                    "status": SubscriptionStatus.CANCELED,
                    "reason": reason,
                    "cancel_at_period_end": cancel_at_period_end
                }
            )

            # Update newsletter lists (US-059)
            try:
                newsletter_result = await self.webhook_handler.handle_subscription_canceled(
                    subscription_id
                )
                logger.info(
                    f"Newsletter lists updated for cancellation: {subscription_id}"
                )
            except Exception as e:
                logger.error(f"Failed to update newsletter lists: {e}")
                # Don't fail cancellation if newsletter update fails

            return {
                "success": True,
                "subscription_id": subscription_id,
                "subscription": updated_subscription,
                "cancel_at_period_end": cancel_at_period_end,
                "newsletter_result": newsletter_result if 'newsletter_result' in locals() else None
            }

        except ZeroDBNotFoundError:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            raise SubscriptionServiceError(f"Failed to cancel subscription: {str(e)}")

    async def reactivate_subscription(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Reactivate canceled subscription and re-add to newsletter

        Args:
            subscription_id: Subscription ID

        Returns:
            Dict with reactivation details

        Raises:
            SubscriptionNotFoundError: If subscription not found
            SubscriptionServiceError: If reactivation fails
        """
        try:
            # Get subscription
            sub_result = self.db.get_document("subscriptions", subscription_id)
            subscription = sub_result.get("data", {})

            if not subscription:
                raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")

            if subscription.get("status") != SubscriptionStatus.CANCELED:
                raise SubscriptionServiceError("Only canceled subscriptions can be reactivated")

            user_id = str(subscription.get("user_id"))
            tier = subscription.get("tier")

            # Calculate new end date
            start_date = datetime.utcnow()
            interval = subscription.get("interval", "year")

            if interval == "year":
                end_date = start_date + timedelta(days=365)
            elif interval == "month":
                end_date = start_date + timedelta(days=30)
            else:
                end_date = None

            # Update subscription
            update_data = {
                "status": SubscriptionStatus.ACTIVE,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat() if end_date else None,
                "canceled_at": None,
                "updated_at": datetime.utcnow().isoformat()
            }

            updated_result = self.db.update_document(
                "subscriptions",
                subscription_id,
                update_data,
                merge=True
            )

            updated_subscription = updated_result.get("data", {})

            logger.info(f"Subscription reactivated: {subscription_id}")

            # Create audit log
            self._create_audit_log(
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="subscriptions",
                resource_id=subscription_id,
                description="Subscription reactivated",
                changes={
                    "status": SubscriptionStatus.ACTIVE,
                    "new_end_date": end_date.isoformat() if end_date else None
                }
            )

            # Re-subscribe to newsletter (US-059)
            try:
                newsletter_result = await self.webhook_handler.handle_subscription_created(
                    subscription_id
                )
                logger.info(
                    f"Newsletter re-subscription triggered: {subscription_id}"
                )
            except Exception as e:
                logger.error(f"Failed to re-subscribe to newsletter: {e}")
                # Don't fail reactivation if newsletter fails

            return {
                "success": True,
                "subscription_id": subscription_id,
                "subscription": updated_subscription,
                "newsletter_result": newsletter_result if 'newsletter_result' in locals() else None
            }

        except ZeroDBNotFoundError:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        except Exception as e:
            logger.error(f"Error reactivating subscription: {e}")
            raise SubscriptionServiceError(f"Failed to reactivate subscription: {str(e)}")

    def _get_tier_features(self, tier: str) -> Dict[str, Any]:
        """
        Get features for a subscription tier

        Args:
            tier: Subscription tier

        Returns:
            Dict of tier features
        """
        features = {
            SubscriptionTier.FREE: {
                "access_level": "limited",
                "event_access": False,
                "training_videos": False,
                "newsletter": True
            },
            SubscriptionTier.BASIC: {
                "access_level": "basic",
                "event_access": True,
                "training_videos": False,
                "newsletter": True,
                "member_directory": True
            },
            SubscriptionTier.PREMIUM: {
                "access_level": "premium",
                "event_access": True,
                "training_videos": True,
                "newsletter": True,
                "member_directory": True,
                "priority_support": True
            },
            SubscriptionTier.LIFETIME: {
                "access_level": "instructor",
                "event_access": True,
                "training_videos": True,
                "newsletter": True,
                "member_directory": True,
                "priority_support": True,
                "instructor_badge": True,
                "lifetime_access": True
            }
        }

        return features.get(tier, features[SubscriptionTier.FREE])

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
                "tags": ["subscription", "membership"],
                "metadata": {}
            }

            self.db.create_document("audit_logs", audit_data)
            logger.debug(f"Audit log created: {action} on {resource_type}/{resource_id}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


# Singleton instance
_subscription_service_instance = None


def get_subscription_service() -> SubscriptionService:
    """
    Get singleton subscription service instance

    Returns:
        SubscriptionService instance
    """
    global _subscription_service_instance
    if _subscription_service_instance is None:
        _subscription_service_instance = SubscriptionService()
    return _subscription_service_instance
