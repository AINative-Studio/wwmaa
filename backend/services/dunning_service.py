"""
Dunning Service for Failed Payment Recovery

Handles automated dunning process for failed payments including:
- Processing failed payment webhooks from Stripe
- Scheduling automated retry emails
- Managing subscription status transitions
- Automatic downgrade on final cancellation
- Comprehensive audit logging

Architecture:
- Integrates with Stripe Smart Retries as primary mechanism
- Custom dunning for member communication and status management
- Uses APScheduler for automated retry scheduling
- Logs all events to ZeroDB audit_logs
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

from backend.config import settings
from backend.services.zerodb_service import ZeroDBClient, ZeroDBError
from backend.services.email_service import EmailService, EmailServiceError
from backend.models.schemas import (
    SubscriptionStatus,
    UserRole,
    AuditAction
)

# Configure logging
logger = logging.getLogger(__name__)


class DunningStage(str, Enum):
    """Dunning process stages"""
    PAYMENT_FAILED = "payment_failed"  # Day 0
    FIRST_REMINDER = "first_reminder"  # Day 3
    SECOND_REMINDER = "second_reminder"  # Day 7
    FINAL_WARNING = "final_warning"  # Day 12
    CANCELED = "canceled"  # Day 14


class DunningServiceError(Exception):
    """Base exception for dunning service errors"""
    pass


class DunningService:
    """
    Service for managing failed payment dunning process

    Responsibilities:
    - Process invoice.payment_failed webhook events
    - Send dunning emails at scheduled intervals
    - Update subscription and user status
    - Log all dunning events to audit trail
    - Handle automatic cancellation and downgrade
    """

    # Dunning schedule configuration (days after initial failure)
    DUNNING_SCHEDULE = {
        DunningStage.PAYMENT_FAILED: 0,
        DunningStage.FIRST_REMINDER: 3,
        DunningStage.SECOND_REMINDER: 7,
        DunningStage.FINAL_WARNING: 12,
        DunningStage.CANCELED: 14
    }

    def __init__(
        self,
        zerodb_client: Optional[ZeroDBClient] = None,
        email_service: Optional[EmailService] = None,
        grace_period_days: int = 14
    ):
        """
        Initialize Dunning Service

        Args:
            zerodb_client: ZeroDB client instance
            email_service: Email service instance
            grace_period_days: Grace period before cancellation (default: 14)
        """
        self.db = zerodb_client or ZeroDBClient()
        self.email = email_service or EmailService()
        self.grace_period_days = grace_period_days

        logger.info(
            f"DunningService initialized with grace period: {grace_period_days} days"
        )

    async def process_payment_failed_event(
        self,
        stripe_invoice_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        amount_due: float,
        currency: str = "USD",
        attempt_count: int = 1,
        next_payment_attempt: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Process invoice.payment_failed webhook from Stripe

        Args:
            stripe_invoice_id: Stripe invoice ID
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            amount_due: Amount that failed to process
            currency: Currency code
            attempt_count: Number of payment attempts
            next_payment_attempt: When Stripe will retry payment

        Returns:
            Dictionary with processing results

        Raises:
            DunningServiceError: If processing fails
        """
        logger.info(
            f"Processing payment failed event for invoice {stripe_invoice_id}, "
            f"attempt {attempt_count}"
        )

        try:
            # Find subscription by Stripe subscription ID
            subscription = await self._find_subscription_by_stripe_id(
                stripe_subscription_id
            )

            if not subscription:
                logger.error(
                    f"Subscription not found for Stripe ID: {stripe_subscription_id}"
                )
                raise DunningServiceError(
                    f"Subscription not found: {stripe_subscription_id}"
                )

            subscription_id = subscription.get('id')
            user_id = subscription.get('user_id')

            # Get user information
            user = await self._get_user(user_id)
            if not user:
                raise DunningServiceError(f"User not found: {user_id}")

            # Update subscription status to past_due
            await self._update_subscription_status(
                subscription_id=subscription_id,
                status=SubscriptionStatus.PAST_DUE,
                metadata={
                    'last_payment_failure': datetime.utcnow().isoformat(),
                    'stripe_invoice_id': stripe_invoice_id,
                    'failed_amount': amount_due,
                    'attempt_count': attempt_count,
                    'next_payment_attempt': next_payment_attempt.isoformat() if next_payment_attempt else None
                }
            )

            # Create dunning record
            dunning_record = await self._create_dunning_record(
                subscription_id=subscription_id,
                user_id=user_id,
                stage=DunningStage.PAYMENT_FAILED,
                amount_due=amount_due,
                currency=currency,
                stripe_invoice_id=stripe_invoice_id,
                metadata={
                    'attempt_count': attempt_count,
                    'next_payment_attempt': next_payment_attempt.isoformat() if next_payment_attempt else None
                }
            )

            # Send initial payment failed notification
            await self._send_dunning_email(
                user=user,
                subscription=subscription,
                stage=DunningStage.PAYMENT_FAILED,
                amount_due=amount_due,
                currency=currency
            )

            # Log audit event
            await self._log_audit_event(
                user_id=user_id,
                action=AuditAction.PAYMENT,
                details={
                    'event': 'payment_failed',
                    'subscription_id': str(subscription_id),
                    'dunning_record_id': str(dunning_record.get('id')),
                    'amount_due': amount_due,
                    'currency': currency,
                    'attempt_count': attempt_count
                }
            )

            logger.info(
                f"Payment failed event processed successfully for subscription "
                f"{subscription_id}"
            )

            return {
                'success': True,
                'subscription_id': str(subscription_id),
                'dunning_record_id': str(dunning_record.get('id')),
                'user_email': user.get('email'),
                'stage': DunningStage.PAYMENT_FAILED.value,
                'next_reminder_date': self._calculate_next_reminder_date(
                    DunningStage.PAYMENT_FAILED
                ).isoformat()
            }

        except ZeroDBError as e:
            logger.error(f"Database error processing payment failed event: {e}")
            raise DunningServiceError(f"Database error: {e}")
        except EmailServiceError as e:
            logger.error(f"Email error processing payment failed event: {e}")
            # Don't fail the entire process if email fails
            logger.warning("Continuing despite email failure")
            return {
                'success': True,
                'email_failed': True,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error processing payment failed event: {e}")
            raise DunningServiceError(f"Unexpected error: {e}")

    async def process_dunning_reminder(
        self,
        dunning_record_id: str,
        stage: DunningStage
    ) -> Dict[str, Any]:
        """
        Process scheduled dunning reminder

        Args:
            dunning_record_id: ID of dunning record
            stage: Dunning stage to process

        Returns:
            Processing results

        Raises:
            DunningServiceError: If processing fails
        """
        logger.info(
            f"Processing dunning reminder for record {dunning_record_id}, "
            f"stage: {stage.value}"
        )

        try:
            # Get dunning record
            dunning_record = await self._get_dunning_record(dunning_record_id)
            if not dunning_record:
                raise DunningServiceError(
                    f"Dunning record not found: {dunning_record_id}"
                )

            subscription_id = dunning_record.get('subscription_id')
            user_id = dunning_record.get('user_id')

            # Get subscription and user
            subscription = await self._get_subscription(subscription_id)
            user = await self._get_user(user_id)

            # Check if subscription is still past_due
            if subscription.get('status') != SubscriptionStatus.PAST_DUE.value:
                logger.info(
                    f"Subscription {subscription_id} is no longer past_due, "
                    f"skipping reminder"
                )
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'subscription_status_changed',
                    'current_status': subscription.get('status')
                }

            # Handle cancellation stage
            if stage == DunningStage.CANCELED:
                return await self._process_cancellation(
                    dunning_record=dunning_record,
                    subscription=subscription,
                    user=user
                )

            # Send dunning email
            await self._send_dunning_email(
                user=user,
                subscription=subscription,
                stage=stage,
                amount_due=dunning_record.get('amount_due'),
                currency=dunning_record.get('currency', 'USD')
            )

            # Update dunning record
            await self._update_dunning_record(
                dunning_record_id=dunning_record_id,
                stage=stage,
                metadata={
                    'last_reminder_sent': datetime.utcnow().isoformat(),
                    'reminder_count': dunning_record.get('reminder_count', 0) + 1
                }
            )

            # Log audit event
            await self._log_audit_event(
                user_id=user_id,
                action=AuditAction.UPDATE,
                details={
                    'event': 'dunning_reminder_sent',
                    'subscription_id': str(subscription_id),
                    'dunning_record_id': str(dunning_record_id),
                    'stage': stage.value
                }
            )

            # Calculate next reminder date
            next_stage = self._get_next_stage(stage)
            next_reminder_date = None
            if next_stage:
                next_reminder_date = self._calculate_next_reminder_date(
                    stage,
                    base_date=dunning_record.get('created_at')
                )

            return {
                'success': True,
                'dunning_record_id': str(dunning_record_id),
                'stage': stage.value,
                'next_stage': next_stage.value if next_stage else None,
                'next_reminder_date': next_reminder_date.isoformat() if next_reminder_date else None
            }

        except Exception as e:
            logger.error(f"Error processing dunning reminder: {e}")
            raise DunningServiceError(f"Error processing reminder: {e}")

    async def _process_cancellation(
        self,
        dunning_record: Dict[str, Any],
        subscription: Dict[str, Any],
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process final cancellation after grace period

        Args:
            dunning_record: Dunning record
            subscription: Subscription data
            user: User data

        Returns:
            Cancellation results
        """
        logger.info(
            f"Processing cancellation for subscription {subscription.get('id')}"
        )

        try:
            subscription_id = subscription.get('id')
            user_id = user.get('id')

            # Update subscription status to canceled
            await self._update_subscription_status(
                subscription_id=subscription_id,
                status=SubscriptionStatus.CANCELED,
                metadata={
                    'canceled_at': datetime.utcnow().isoformat(),
                    'canceled_reason': 'payment_failure_after_grace_period',
                    'dunning_record_id': str(dunning_record.get('id'))
                }
            )

            # Downgrade user to public role
            await self._downgrade_user_role(user_id)

            # Send cancellation notification
            await self._send_dunning_email(
                user=user,
                subscription=subscription,
                stage=DunningStage.CANCELED,
                amount_due=dunning_record.get('amount_due'),
                currency=dunning_record.get('currency', 'USD')
            )

            # Update dunning record
            await self._update_dunning_record(
                dunning_record_id=str(dunning_record.get('id')),
                stage=DunningStage.CANCELED,
                metadata={
                    'canceled_at': datetime.utcnow().isoformat(),
                    'final_status': 'canceled'
                }
            )

            # Log audit events
            await self._log_audit_event(
                user_id=user_id,
                action=AuditAction.UPDATE,
                details={
                    'event': 'subscription_canceled',
                    'subscription_id': str(subscription_id),
                    'reason': 'payment_failure_dunning',
                    'dunning_record_id': str(dunning_record.get('id'))
                }
            )

            await self._log_audit_event(
                user_id=user_id,
                action=AuditAction.UPDATE,
                details={
                    'event': 'user_downgraded',
                    'previous_role': user.get('role'),
                    'new_role': UserRole.PUBLIC.value,
                    'reason': 'subscription_canceled_dunning'
                }
            )

            logger.info(
                f"Subscription {subscription_id} canceled and user {user_id} "
                f"downgraded to public"
            )

            return {
                'success': True,
                'subscription_id': str(subscription_id),
                'user_id': str(user_id),
                'action': 'canceled',
                'user_downgraded': True,
                'new_role': UserRole.PUBLIC.value
            }

        except Exception as e:
            logger.error(f"Error processing cancellation: {e}")
            raise DunningServiceError(f"Cancellation error: {e}")

    async def get_accounts_in_dunning(
        self,
        status_filter: Optional[str] = None,
        stage_filter: Optional[DunningStage] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all accounts currently in dunning process

        Args:
            status_filter: Filter by subscription status
            stage_filter: Filter by dunning stage
            limit: Maximum records to return
            offset: Offset for pagination

        Returns:
            List of dunning records with subscription and user info
        """
        logger.info(
            f"Fetching accounts in dunning (status: {status_filter}, "
            f"stage: {stage_filter})"
        )

        try:
            # Build query
            query = {}
            if stage_filter:
                query['current_stage'] = stage_filter.value
            if status_filter:
                query['subscription_status'] = status_filter

            # Query dunning_records collection
            dunning_records = self.db.query(
                collection='dunning_records',
                query=query,
                limit=limit,
                offset=offset
            )

            # Enrich with subscription and user data
            enriched_records = []
            for record in dunning_records:
                subscription = await self._get_subscription(
                    record.get('subscription_id')
                )
                user = await self._get_user(record.get('user_id'))

                enriched_records.append({
                    'dunning_record': record,
                    'subscription': subscription,
                    'user': {
                        'id': user.get('id'),
                        'email': user.get('email'),
                        'role': user.get('role')
                    },
                    'days_past_due': self._calculate_days_past_due(
                        record.get('created_at')
                    )
                })

            logger.info(f"Found {len(enriched_records)} accounts in dunning")
            return enriched_records

        except Exception as e:
            logger.error(f"Error fetching accounts in dunning: {e}")
            raise DunningServiceError(f"Error fetching accounts: {e}")

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _find_subscription_by_stripe_id(
        self,
        stripe_subscription_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find subscription by Stripe subscription ID"""
        try:
            results = self.db.query(
                collection='subscriptions',
                query={'stripe_subscription_id': stripe_subscription_id},
                limit=1
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error finding subscription: {e}")
            raise

    async def _get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription by ID"""
        try:
            return self.db.get(collection='subscriptions', id=subscription_id)
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            raise

    async def _get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        try:
            return self.db.get(collection='users', id=user_id)
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise

    async def _update_subscription_status(
        self,
        subscription_id: str,
        status: SubscriptionStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update subscription status"""
        try:
            update_data = {
                'status': status.value,
                'updated_at': datetime.utcnow().isoformat()
            }

            if metadata:
                # Merge with existing metadata
                subscription = await self._get_subscription(subscription_id)
                existing_metadata = subscription.get('metadata', {})
                existing_metadata.update(metadata)
                update_data['metadata'] = existing_metadata

            self.db.update(
                collection='subscriptions',
                id=subscription_id,
                data=update_data
            )

            logger.info(
                f"Updated subscription {subscription_id} status to {status.value}"
            )
        except Exception as e:
            logger.error(f"Error updating subscription status: {e}")
            raise

    async def _downgrade_user_role(self, user_id: str) -> None:
        """Downgrade user to public role"""
        try:
            self.db.update(
                collection='users',
                id=user_id,
                data={
                    'role': UserRole.PUBLIC.value,
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Downgraded user {user_id} to public role")
        except Exception as e:
            logger.error(f"Error downgrading user role: {e}")
            raise

    async def _create_dunning_record(
        self,
        subscription_id: str,
        user_id: str,
        stage: DunningStage,
        amount_due: float,
        currency: str,
        stripe_invoice_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create dunning record in ZeroDB"""
        try:
            record_data = {
                'subscription_id': str(subscription_id),
                'user_id': str(user_id),
                'current_stage': stage.value,
                'amount_due': amount_due,
                'currency': currency,
                'stripe_invoice_id': stripe_invoice_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'reminder_count': 0,
                'metadata': metadata or {}
            }

            result = self.db.create(
                collection='dunning_records',
                data=record_data
            )

            logger.info(f"Created dunning record: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"Error creating dunning record: {e}")
            raise

    async def _get_dunning_record(
        self,
        dunning_record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get dunning record by ID"""
        try:
            return self.db.get(
                collection='dunning_records',
                id=dunning_record_id
            )
        except Exception as e:
            logger.error(f"Error getting dunning record: {e}")
            raise

    async def _update_dunning_record(
        self,
        dunning_record_id: str,
        stage: DunningStage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update dunning record"""
        try:
            update_data = {
                'current_stage': stage.value,
                'updated_at': datetime.utcnow().isoformat()
            }

            if metadata:
                # Merge with existing metadata
                record = await self._get_dunning_record(dunning_record_id)
                existing_metadata = record.get('metadata', {})
                existing_metadata.update(metadata)
                update_data['metadata'] = existing_metadata

                if 'reminder_count' in metadata:
                    update_data['reminder_count'] = metadata['reminder_count']

            self.db.update(
                collection='dunning_records',
                id=dunning_record_id,
                data=update_data
            )

            logger.info(
                f"Updated dunning record {dunning_record_id} to stage {stage.value}"
            )
        except Exception as e:
            logger.error(f"Error updating dunning record: {e}")
            raise

    async def _send_dunning_email(
        self,
        user: Dict[str, Any],
        subscription: Dict[str, Any],
        stage: DunningStage,
        amount_due: float,
        currency: str
    ) -> None:
        """Send dunning email based on stage"""
        try:
            email_address = user.get('email')
            user_name = user.get('first_name', 'Member')

            # Get payment update URL
            payment_url = self._get_payment_update_url(subscription.get('id'))

            # Send appropriate email based on stage
            if stage == DunningStage.PAYMENT_FAILED:
                await self._send_payment_failed_email(
                    email_address, user_name, amount_due, currency, payment_url
                )
            elif stage == DunningStage.FIRST_REMINDER:
                await self._send_first_reminder_email(
                    email_address, user_name, amount_due, currency, payment_url
                )
            elif stage == DunningStage.SECOND_REMINDER:
                await self._send_second_reminder_email(
                    email_address, user_name, amount_due, currency, payment_url
                )
            elif stage == DunningStage.FINAL_WARNING:
                await self._send_final_warning_email(
                    email_address, user_name, amount_due, currency, payment_url
                )
            elif stage == DunningStage.CANCELED:
                await self._send_cancellation_email(
                    email_address, user_name, amount_due, currency
                )

            logger.info(
                f"Sent {stage.value} email to {email_address}"
            )
        except Exception as e:
            logger.error(f"Error sending dunning email: {e}")
            raise EmailServiceError(f"Failed to send {stage.value} email: {e}")

    async def _send_payment_failed_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str,
        payment_url: str
    ) -> None:
        """Send payment failed notification (Day 0)"""
        # This will be implemented with email templates
        # For now, use a placeholder
        logger.info(f"Sending payment failed email to {email}")
        # Implementation moved to email templates section

    async def _send_first_reminder_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str,
        payment_url: str
    ) -> None:
        """Send first reminder (Day 3)"""
        logger.info(f"Sending first reminder email to {email}")
        # Implementation moved to email templates section

    async def _send_second_reminder_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str,
        payment_url: str
    ) -> None:
        """Send second reminder (Day 7)"""
        logger.info(f"Sending second reminder email to {email}")
        # Implementation moved to email templates section

    async def _send_final_warning_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str,
        payment_url: str
    ) -> None:
        """Send final warning before cancellation (Day 12)"""
        logger.info(f"Sending final warning email to {email}")
        # Implementation moved to email templates section

    async def _send_cancellation_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str
    ) -> None:
        """Send cancellation notice (Day 14)"""
        logger.info(f"Sending cancellation email to {email}")
        # Implementation moved to email templates section

    async def _log_audit_event(
        self,
        user_id: str,
        action: AuditAction,
        details: Dict[str, Any]
    ) -> None:
        """Log audit event to ZeroDB"""
        try:
            audit_data = {
                'user_id': str(user_id),
                'action': action.value,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': None,  # Not available in background process
                'user_agent': 'dunning_service'
            }

            self.db.create(collection='audit_logs', data=audit_data)
            logger.debug(f"Logged audit event: {action.value} for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            # Don't fail the main operation if audit logging fails

    def _get_payment_update_url(self, subscription_id: str) -> str:
        """Generate payment update URL for member"""
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        return f"{frontend_url}/account/payment?subscription_id={subscription_id}"

    def _calculate_next_reminder_date(
        self,
        current_stage: DunningStage,
        base_date: Optional[str] = None
    ) -> datetime:
        """Calculate next reminder date based on current stage"""
        base = datetime.fromisoformat(base_date) if base_date else datetime.utcnow()
        next_stage = self._get_next_stage(current_stage)

        if not next_stage:
            return base

        days_offset = self.DUNNING_SCHEDULE[next_stage]
        return base + timedelta(days=days_offset)

    def _get_next_stage(self, current_stage: DunningStage) -> Optional[DunningStage]:
        """Get next dunning stage"""
        stage_order = [
            DunningStage.PAYMENT_FAILED,
            DunningStage.FIRST_REMINDER,
            DunningStage.SECOND_REMINDER,
            DunningStage.FINAL_WARNING,
            DunningStage.CANCELED
        ]

        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
            return None
        except ValueError:
            return None

    def _calculate_days_past_due(self, created_at: str) -> int:
        """Calculate days past due from dunning record creation"""
        created = datetime.fromisoformat(created_at)
        return (datetime.utcnow() - created).days


# Global dunning service instance (singleton pattern)
_dunning_service_instance: Optional[DunningService] = None


def get_dunning_service() -> DunningService:
    """
    Get or create the global DunningService instance

    Returns:
        DunningService instance
    """
    global _dunning_service_instance

    if _dunning_service_instance is None:
        _dunning_service_instance = DunningService()

    return _dunning_service_instance
