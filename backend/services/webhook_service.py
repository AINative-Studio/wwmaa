"""
Stripe Webhook Service for WWMAA Backend

Handles all Stripe webhook events to maintain payment synchronization with ZeroDB.
This is a CRITICAL service that ensures subscription status, payment records, and
user roles stay synchronized with Stripe.

Webhook Events Handled:
- checkout.session.completed: Create subscription and activate membership
- invoice.paid: Record payment in ZeroDB
- invoice.payment_failed: Update subscription status, send dunning email
- customer.subscription.updated: Update subscription in ZeroDB
- customer.subscription.deleted: Deactivate membership, downgrade user role
- charge.refunded: Update payment record, handle refund logic

All webhook events are:
1. Idempotent (event IDs tracked to prevent duplicate processing)
2. Fast (respond within 5 seconds to avoid Stripe retries)
3. Logged comprehensively for debugging
4. Stored in ZeroDB for replay/audit purposes
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from backend.config import settings
from backend.services.zerodb_service import get_zerodb_client, ZeroDBError
from backend.services.email_service import get_email_service
from backend.services.dunning_service import get_dunning_service, DunningServiceError
from backend.models.schemas import (
    SubscriptionStatus,
    PaymentStatus,
    UserRole,
    AuditAction
)

# Configure logging
logger = logging.getLogger(__name__)


class WebhookServiceError(Exception):
    """Base exception for webhook service errors"""
    pass


class WebhookProcessingError(WebhookServiceError):
    """Exception raised when webhook event processing fails"""
    pass


class DuplicateEventError(WebhookServiceError):
    """Exception raised when a webhook event has already been processed"""
    pass


class WebhookService:
    """
    Stripe Webhook Event Processing Service

    Handles all Stripe webhook events with:
    - Idempotent processing (tracks event IDs)
    - Comprehensive error handling
    - Audit logging for all events
    - Email notifications for payment events
    - Fast response times (< 5 seconds)
    """

    def __init__(self):
        """Initialize webhook service with ZeroDB, email, and dunning clients"""
        self.db = get_zerodb_client()
        self.email_service = get_email_service()
        self.dunning_service = get_dunning_service()
        logger.info("WebhookService initialized with dunning support")

    def _is_duplicate_event(self, event_id: str) -> bool:
        """
        Check if webhook event has already been processed (idempotency check)

        Args:
            event_id: Stripe event ID

        Returns:
            True if event has been processed, False otherwise
        """
        try:
            # Query webhook_events collection for this event ID
            result = self.db.query_documents(
                collection="webhook_events",
                filters={"stripe_event_id": event_id},
                limit=1
            )

            documents = result.get("documents", [])
            if documents:
                logger.warning(f"Duplicate webhook event detected: {event_id}")
                return True

            return False

        except ZeroDBError as e:
            logger.error(f"Error checking for duplicate event: {e}")
            # If we can't check for duplicates, assume it's not a duplicate
            # to avoid blocking legitimate events
            return False

    def _store_webhook_event(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        processing_status: str = "processed",
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store webhook event in ZeroDB for replay/debugging

        Args:
            event_id: Stripe event ID
            event_type: Event type (e.g., 'checkout.session.completed')
            event_data: Full event data from Stripe
            processing_status: Processing status (processed/failed)
            error_message: Error message if processing failed

        Returns:
            Created webhook event document
        """
        try:
            webhook_event_data = {
                "stripe_event_id": event_id,
                "event_type": event_type,
                "event_data": event_data,
                "processing_status": processing_status,
                "error_message": error_message,
                "processed_at": datetime.utcnow().isoformat()
            }

            result = self.db.create_document(
                collection="webhook_events",
                data=webhook_event_data
            )

            logger.info(f"Stored webhook event {event_id} in ZeroDB")
            return result

        except ZeroDBError as e:
            logger.error(f"Failed to store webhook event: {e}")
            # Don't raise error here - event storage failure shouldn't block processing
            return {}

    def _create_audit_log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        description: str,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create audit log entry in ZeroDB

        Args:
            action: Action performed (from AuditAction enum)
            resource_type: Resource type (collection name)
            resource_id: Resource document ID
            description: Action description
            user_id: User ID (optional)
            changes: Before/after changes (optional)
            success: Action success status
            error_message: Error message if failed

        Returns:
            Created audit log document
        """
        try:
            audit_data = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "changes": changes or {},
                "success": success,
                "error_message": error_message,
                "severity": "error" if not success else "info",
                "tags": ["webhook", "stripe"],
                "metadata": {
                    "source": "stripe_webhook",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            result = self.db.create_document(
                collection="audit_logs",
                data=audit_data
            )

            return result

        except ZeroDBError as e:
            logger.error(f"Failed to create audit log: {e}")
            return {}

    def process_webhook_event(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process webhook event and route to appropriate handler

        Args:
            event_id: Stripe event ID
            event_type: Event type (e.g., 'checkout.session.completed')
            event_data: Full event data from Stripe

        Returns:
            Processing result with status and details

        Raises:
            DuplicateEventError: If event has already been processed
            WebhookProcessingError: If event processing fails
        """
        start_time = time.time()

        # Check for duplicate event (idempotency)
        if self._is_duplicate_event(event_id):
            raise DuplicateEventError(f"Event {event_id} has already been processed")

        logger.info(f"Processing webhook event: {event_type} (ID: {event_id})")

        try:
            # Route to appropriate handler based on event type
            if event_type == "checkout.session.completed":
                result = self._handle_checkout_completed(event_data)
            elif event_type == "invoice.paid":
                result = self._handle_invoice_paid(event_data)
            elif event_type == "invoice.payment_failed":
                result = self._handle_invoice_payment_failed(event_data)
            elif event_type == "customer.subscription.updated":
                result = self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                result = self._handle_subscription_deleted(event_data)
            elif event_type == "charge.refunded":
                result = self._handle_charge_refunded(event_data)
            else:
                logger.warning(f"Unhandled event type: {event_type}")
                result = {"status": "ignored", "message": f"Event type {event_type} not handled"}

            # Store successful event in ZeroDB
            self._store_webhook_event(
                event_id=event_id,
                event_type=event_type,
                event_data=event_data,
                processing_status="processed"
            )

            elapsed_time = time.time() - start_time
            logger.info(f"Webhook event {event_id} processed successfully in {elapsed_time:.2f}s")

            result["processing_time_seconds"] = elapsed_time
            return result

        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Failed to process webhook event {event_id}: {str(e)}"
            logger.error(error_msg)

            # Store failed event in ZeroDB
            self._store_webhook_event(
                event_id=event_id,
                event_type=event_type,
                event_data=event_data,
                processing_status="failed",
                error_message=str(e)
            )

            # Create audit log for failure
            self._create_audit_log(
                action="webhook_processing",
                resource_type="webhook_events",
                resource_id=event_id,
                description=f"Failed to process {event_type} event",
                success=False,
                error_message=str(e)
            )

            raise WebhookProcessingError(error_msg)

    def _handle_checkout_completed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle checkout.session.completed event

        Handles both:
        - Membership subscriptions (existing logic)
        - Event RSVP payments (new logic for US-032)

        Actions for membership:
        1. Create subscription in ZeroDB
        2. Activate membership
        3. Upgrade user role to 'member'
        4. Send welcome/confirmation email

        Actions for event RSVP:
        1. Create RSVP record in ZeroDB
        2. Create payment record
        3. Update event attendee count
        4. Generate QR code
        5. Send ticket/confirmation email

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        session = event_data.get("data", {}).get("object", {})
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        customer_email = session.get("customer_email")
        metadata = session.get("metadata", {})
        payment_type = metadata.get("type", "membership")

        logger.info(f"Processing checkout completion for customer {customer_id}, type: {payment_type}")

        # Route to appropriate handler based on payment type
        if payment_type == "event_rsvp":
            return self._handle_event_rsvp_payment(session)

        # Default to membership payment handling (existing logic)

        # Find user by Stripe customer ID or email
        user = self._find_user_by_stripe_customer_id(customer_id)
        if not user and customer_email:
            user = self._find_user_by_email(customer_email)

        if not user:
            error_msg = f"User not found for customer {customer_id} or email {customer_email}"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        user_id = user.get("data", {}).get("id")

        # Create subscription record in ZeroDB
        subscription_data = {
            "user_id": user_id,
            "tier": "basic",  # Default tier, should be determined from session metadata
            "status": SubscriptionStatus.ACTIVE.value,
            "stripe_subscription_id": subscription_id,
            "stripe_customer_id": customer_id,
            "start_date": datetime.utcnow().isoformat(),
            "amount": session.get("amount_total", 0) / 100,  # Convert from cents
            "currency": session.get("currency", "usd").upper(),
            "interval": "month",  # Default, should be from session
            "features": {},
            "metadata": {
                "checkout_session_id": session.get("id"),
                "payment_status": session.get("payment_status")
            }
        }

        subscription = self.db.create_document(
            collection="subscriptions",
            data=subscription_data
        )

        logger.info(f"Created subscription {subscription.get('id')} for user {user_id}")

        # Update user role to 'member'
        self.db.update_document(
            collection="users",
            document_id=user_id,
            data={"role": UserRole.MEMBER.value},
            merge=True
        )

        logger.info(f"Upgraded user {user_id} role to 'member'")

        # Update Stripe customer ID if not already set
        if not user.get("data", {}).get("stripe_customer_id"):
            self.db.update_document(
                collection="users",
                document_id=user_id,
                data={"stripe_customer_id": customer_id},
                merge=True
            )

        # Create audit log
        self._create_audit_log(
            action=AuditAction.PAYMENT.value,
            resource_type="subscriptions",
            resource_id=subscription.get("id"),
            description=f"Checkout completed: subscription created for user {user_id}",
            user_id=user_id,
            changes={
                "before": {"role": user.get("data", {}).get("role", "public")},
                "after": {"role": "member", "subscription_id": subscription.get("id")}
            }
        )

        # Send welcome email
        try:
            user_email = user.get("data", {}).get("email")
            user_name = user.get("data", {}).get("first_name", "Member")

            self.email_service.send_payment_success_email(
                email=user_email,
                user_name=user_name,
                amount=subscription_data["amount"],
                currency=subscription_data["currency"]
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            # Don't fail the webhook if email fails

        return {
            "status": "success",
            "action": "checkout_completed",
            "subscription_id": subscription.get("id"),
            "user_id": user_id
        }

    def _handle_invoice_paid(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle invoice.paid event

        Actions:
        1. Record payment in ZeroDB payments collection
        2. Send payment receipt email

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        invoice = event_data.get("data", {}).get("object", {})
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")

        logger.info(f"Processing invoice payment for customer {customer_id}")

        # Find user by Stripe customer ID
        user = self._find_user_by_stripe_customer_id(customer_id)
        if not user:
            error_msg = f"User not found for customer {customer_id}"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        user_id = user.get("data", {}).get("id")

        # Find subscription in ZeroDB
        zerodb_subscription = self._find_subscription_by_stripe_id(subscription_id)
        subscription_uuid = zerodb_subscription.get("data", {}).get("id") if zerodb_subscription else None

        # Create payment record in ZeroDB
        payment_data = {
            "user_id": user_id,
            "subscription_id": subscription_uuid,
            "amount": invoice.get("amount_paid", 0) / 100,  # Convert from cents
            "currency": invoice.get("currency", "usd").upper(),
            "status": PaymentStatus.SUCCEEDED.value,
            "stripe_payment_intent_id": invoice.get("payment_intent"),
            "stripe_charge_id": invoice.get("charge"),
            "payment_method": invoice.get("payment_method_types", ["card"])[0],
            "description": invoice.get("description", "Subscription payment"),
            "receipt_url": invoice.get("hosted_invoice_url"),
            "processed_at": datetime.utcnow().isoformat(),
            "metadata": {
                "invoice_id": invoice.get("id"),
                "invoice_number": invoice.get("number"),
                "billing_reason": invoice.get("billing_reason")
            }
        }

        payment = self.db.create_document(
            collection="payments",
            data=payment_data
        )

        logger.info(f"Created payment record {payment.get('id')} for user {user_id}")

        # Create audit log
        self._create_audit_log(
            action=AuditAction.PAYMENT.value,
            resource_type="payments",
            resource_id=payment.get("id"),
            description=f"Invoice paid: ${payment_data['amount']} {payment_data['currency']}",
            user_id=user_id
        )

        # Send payment receipt email
        try:
            user_email = user.get("data", {}).get("email")
            user_name = user.get("data", {}).get("first_name", "Member")

            self.email_service.send_payment_success_email(
                email=user_email,
                user_name=user_name,
                amount=payment_data["amount"],
                currency=payment_data["currency"],
                receipt_url=payment_data.get("receipt_url")
            )
        except Exception as e:
            logger.error(f"Failed to send payment receipt email: {e}")
            # Don't fail the webhook if email fails

        return {
            "status": "success",
            "action": "invoice_paid",
            "payment_id": payment.get("id"),
            "user_id": user_id
        }

    def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle invoice.payment_failed event with comprehensive dunning support

        Actions:
        1. Extract invoice details from Stripe event
        2. Delegate to DunningService for comprehensive handling:
           - Update subscription status to 'past_due'
           - Create dunning record in ZeroDB
           - Send dunning email to user
           - Log audit event
           - Schedule future dunning reminders
        3. Create failed payment record for tracking

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        invoice = event_data.get("data", {}).get("object", {})
        stripe_invoice_id = invoice.get("id")
        stripe_customer_id = invoice.get("customer")
        stripe_subscription_id = invoice.get("subscription")
        amount_due = invoice.get("amount_due", 0) / 100  # Convert cents to dollars
        currency = invoice.get("currency", "usd").upper()
        attempt_count = invoice.get("attempt_count", 1)

        # Parse next_payment_attempt (Unix timestamp)
        next_payment_attempt = invoice.get("next_payment_attempt")
        next_payment_datetime = None
        if next_payment_attempt:
            next_payment_datetime = datetime.fromtimestamp(next_payment_attempt)

        logger.warning(
            f"Processing failed payment for invoice {stripe_invoice_id}, "
            f"customer {stripe_customer_id}, attempt {attempt_count}"
        )

        try:
            # Delegate to comprehensive dunning service
            dunning_result = await self.dunning_service.process_payment_failed_event(
                stripe_invoice_id=stripe_invoice_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                amount_due=amount_due,
                currency=currency,
                attempt_count=attempt_count,
                next_payment_attempt=next_payment_datetime
            )

            logger.info(
                f"Dunning service processed payment failure successfully: "
                f"dunning_record_id={dunning_result.get('dunning_record_id')}"
            )

            # Create failed payment record for transaction history
            user_id = dunning_result.get('user_id')

            # Find subscription to get UUID
            zerodb_subscription = self._find_subscription_by_stripe_id(stripe_subscription_id)
            subscription_uuid = zerodb_subscription.get("data", {}).get("id") if zerodb_subscription else None

            payment_data = {
                "user_id": user_id,
                "subscription_id": subscription_uuid,
                "amount": amount_due,
                "currency": currency,
                "status": PaymentStatus.FAILED.value,
                "stripe_payment_intent_id": invoice.get("payment_intent"),
                "description": "Payment failed - dunning initiated",
                "processed_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "invoice_id": stripe_invoice_id,
                    "attempt_count": attempt_count,
                    "next_payment_attempt": next_payment_datetime.isoformat() if next_payment_datetime else None,
                    "dunning_record_id": dunning_result.get('dunning_record_id'),
                    "dunning_stage": dunning_result.get('stage')
                }
            }

            payment = self.db.create_document(
                collection="payments",
                data=payment_data
            )

            logger.info(f"Created failed payment record {payment.get('id')}")

            return {
                "status": "success",
                "action": "invoice_payment_failed",
                "payment_id": payment.get("id"),
                "user_id": user_id,
                "subscription_status": "past_due",
                "dunning_record_id": dunning_result.get('dunning_record_id'),
                "dunning_stage": dunning_result.get('stage'),
                "next_reminder_date": dunning_result.get('next_reminder_date')
            }

        except DunningServiceError as e:
            # Dunning service failed - log error but don't block webhook
            logger.error(f"Dunning service error: {e}")

            # Fall back to basic handling
            user = self._find_user_by_stripe_customer_id(stripe_customer_id)
            if not user:
                error_msg = f"User not found for customer {stripe_customer_id}"
                logger.error(error_msg)
                raise WebhookProcessingError(error_msg)

            user_id = user.get("data", {}).get("id")

            # Create basic payment failure record
            payment_data = {
                "user_id": user_id,
                "amount": amount_due,
                "currency": currency,
                "status": PaymentStatus.FAILED.value,
                "description": "Payment failed - dunning service error",
                "processed_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "invoice_id": stripe_invoice_id,
                    "attempt_count": attempt_count,
                    "dunning_service_error": str(e)
                }
            }

            payment = self.db.create_document(
                collection="payments",
                data=payment_data
            )

            # Create audit log for dunning failure
            self._create_audit_log(
                action=AuditAction.PAYMENT.value,
                resource_type="payments",
                resource_id=payment.get("id"),
                description=f"Payment failed but dunning service error occurred",
                user_id=user_id,
                success=False,
                error_message=str(e)
            )

            return {
                "status": "partial_success",
                "action": "invoice_payment_failed",
                "payment_id": payment.get("id"),
                "user_id": user_id,
                "error": "Dunning service failed - manual intervention required"
            }

    def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle customer.subscription.updated event

        Actions:
        1. Update subscription in ZeroDB with new data

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        subscription = event_data.get("data", {}).get("object", {})
        stripe_subscription_id = subscription.get("id")

        logger.info(f"Processing subscription update for {stripe_subscription_id}")

        # Find subscription in ZeroDB
        zerodb_subscription = self._find_subscription_by_stripe_id(stripe_subscription_id)
        if not zerodb_subscription:
            error_msg = f"Subscription not found for Stripe subscription {stripe_subscription_id}"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        subscription_uuid = zerodb_subscription.get("data", {}).get("id")
        user_id = zerodb_subscription.get("data", {}).get("user_id")

        # Map Stripe status to our SubscriptionStatus enum
        stripe_status = subscription.get("status")
        status_mapping = {
            "active": SubscriptionStatus.ACTIVE.value,
            "past_due": SubscriptionStatus.PAST_DUE.value,
            "canceled": SubscriptionStatus.CANCELED.value,
            "incomplete": SubscriptionStatus.PAST_DUE.value,
            "incomplete_expired": SubscriptionStatus.EXPIRED.value,
            "trialing": SubscriptionStatus.ACTIVE.value,
            "unpaid": SubscriptionStatus.PAST_DUE.value
        }

        new_status = status_mapping.get(stripe_status, SubscriptionStatus.ACTIVE.value)

        # Update subscription in ZeroDB
        update_data = {
            "status": new_status,
            "end_date": subscription.get("current_period_end"),
            "canceled_at": subscription.get("canceled_at"),
            "metadata": {
                "cancel_at_period_end": subscription.get("cancel_at_period_end"),
                "cancellation_details": subscription.get("cancellation_details")
            }
        }

        updated_subscription = self.db.update_document(
            collection="subscriptions",
            document_id=subscription_uuid,
            data=update_data,
            merge=True
        )

        logger.info(f"Updated subscription {subscription_uuid} with new status: {new_status}")

        # Create audit log
        self._create_audit_log(
            action=AuditAction.UPDATE.value,
            resource_type="subscriptions",
            resource_id=subscription_uuid,
            description=f"Subscription updated: status changed to {new_status}",
            user_id=user_id,
            changes={
                "before": {"status": zerodb_subscription.get("data", {}).get("status")},
                "after": {"status": new_status}
            }
        )

        return {
            "status": "success",
            "action": "subscription_updated",
            "subscription_id": subscription_uuid,
            "new_status": new_status
        }

    def _handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle customer.subscription.deleted event

        Actions:
        1. Deactivate membership
        2. Downgrade user role to 'public'
        3. Update subscription status to 'canceled'
        4. Send cancellation email

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        subscription = event_data.get("data", {}).get("object", {})
        stripe_subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")

        logger.info(f"Processing subscription deletion for {stripe_subscription_id}")

        # Find user by Stripe customer ID
        user = self._find_user_by_stripe_customer_id(customer_id)
        if not user:
            error_msg = f"User not found for customer {customer_id}"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        user_id = user.get("data", {}).get("id")
        current_role = user.get("data", {}).get("role")

        # Find subscription in ZeroDB
        zerodb_subscription = self._find_subscription_by_stripe_id(stripe_subscription_id)
        if zerodb_subscription:
            subscription_uuid = zerodb_subscription.get("data", {}).get("id")

            # Update subscription status to 'canceled'
            self.db.update_document(
                collection="subscriptions",
                document_id=subscription_uuid,
                data={
                    "status": SubscriptionStatus.CANCELED.value,
                    "canceled_at": datetime.utcnow().isoformat()
                },
                merge=True
            )

            logger.info(f"Updated subscription {subscription_uuid} status to 'canceled'")
        else:
            subscription_uuid = None
            logger.warning(f"Subscription not found for Stripe subscription {stripe_subscription_id}")

        # Downgrade user role to 'public' (only if currently 'member')
        if current_role == UserRole.MEMBER.value:
            self.db.update_document(
                collection="users",
                document_id=user_id,
                data={"role": UserRole.PUBLIC.value},
                merge=True
            )

            logger.info(f"Downgraded user {user_id} role from 'member' to 'public'")

        # Create audit log
        self._create_audit_log(
            action=AuditAction.DELETE.value,
            resource_type="subscriptions",
            resource_id=subscription_uuid,
            description=f"Subscription canceled: user {user_id} downgraded to public",
            user_id=user_id,
            changes={
                "before": {"role": current_role, "subscription_status": "active"},
                "after": {"role": UserRole.PUBLIC.value, "subscription_status": "canceled"}
            }
        )

        # Send cancellation email
        try:
            user_email = user.get("data", {}).get("email")
            user_name = user.get("data", {}).get("first_name", "Member")

            self.email_service.send_subscription_canceled_email(
                email=user_email,
                user_name=user_name
            )
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")
            # Don't fail the webhook if email fails

        return {
            "status": "success",
            "action": "subscription_deleted",
            "subscription_id": subscription_uuid,
            "user_id": user_id,
            "new_role": UserRole.PUBLIC.value
        }

    def _handle_charge_refunded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle charge.refunded event

        Actions:
        1. Find payment record by Stripe charge ID
        2. Update payment record with refund information
        3. Send refund confirmation email

        Args:
            event_data: Stripe event data

        Returns:
            Processing result
        """
        charge = event_data.get("data", {}).get("object", {})
        charge_id = charge.get("id")
        refund_amount = charge.get("amount_refunded", 0) / 100
        customer_id = charge.get("customer")

        logger.info(f"Processing charge refund for charge {charge_id}")

        # Find user by Stripe customer ID
        user = self._find_user_by_stripe_customer_id(customer_id)
        if not user:
            error_msg = f"User not found for customer {customer_id}"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        user_id = user.get("data", {}).get("id")

        # Find payment record by Stripe charge ID
        payment_result = self.db.query_documents(
            collection="payments",
            filters={"stripe_charge_id": charge_id},
            limit=1
        )

        payments = payment_result.get("documents", [])
        if not payments:
            logger.warning(f"Payment record not found for charge {charge_id}")
            # Create a new payment record for the refund
            payment_data = {
                "user_id": user_id,
                "amount": refund_amount,
                "currency": charge.get("currency", "usd").upper(),
                "status": PaymentStatus.REFUNDED.value,
                "stripe_charge_id": charge_id,
                "description": "Refund",
                "refunded_amount": refund_amount,
                "refunded_at": datetime.utcnow().isoformat(),
                "refund_reason": charge.get("refunds", {}).get("data", [{}])[0].get("reason", "requested_by_customer"),
                "processed_at": datetime.utcnow().isoformat()
            }

            payment = self.db.create_document(
                collection="payments",
                data=payment_data
            )
            payment_id = payment.get("id")
        else:
            payment = payments[0]
            payment_id = payment.get("id")

            # Update existing payment record with refund information
            refund_data = {
                "status": PaymentStatus.REFUNDED.value,
                "refunded_amount": refund_amount,
                "refunded_at": datetime.utcnow().isoformat(),
                "refund_reason": charge.get("refunds", {}).get("data", [{}])[0].get("reason", "requested_by_customer")
            }

            self.db.update_document(
                collection="payments",
                document_id=payment_id,
                data=refund_data,
                merge=True
            )

        logger.info(f"Updated payment record {payment_id} with refund information")

        # Create audit log
        self._create_audit_log(
            action=AuditAction.PAYMENT.value,
            resource_type="payments",
            resource_id=payment_id,
            description=f"Charge refunded: ${refund_amount}",
            user_id=user_id,
            changes={
                "before": {"status": payment.get("data", {}).get("status", "succeeded")},
                "after": {"status": PaymentStatus.REFUNDED.value, "refunded_amount": refund_amount}
            }
        )

        # Send refund confirmation email
        try:
            user_email = user.get("data", {}).get("email")
            user_name = user.get("data", {}).get("first_name", "Member")

            self.email_service.send_refund_confirmation_email(
                email=user_email,
                user_name=user_name,
                amount=refund_amount,
                currency=charge.get("currency", "usd").upper()
            )
        except Exception as e:
            logger.error(f"Failed to send refund email: {e}")
            # Don't fail the webhook if email fails

        return {
            "status": "success",
            "action": "charge_refunded",
            "payment_id": payment_id,
            "refund_amount": refund_amount,
            "user_id": user_id
        }

    def _handle_event_rsvp_payment(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle successful payment for event RSVP (US-032)

        Actions:
        1. Extract event and user info from session metadata
        2. Create RSVP record in ZeroDB with confirmed status
        3. Create payment record for transaction history
        4. Update event attendee count
        5. Generate QR code for check-in
        6. Send ticket/confirmation email with QR code

        Args:
            session: Stripe checkout session data

        Returns:
            Processing result with RSVP details

        Raises:
            WebhookProcessingError: If RSVP creation fails
        """
        metadata = session.get("metadata", {})
        event_id = metadata.get("event_id")
        user_id = metadata.get("user_id")
        amount_total = session.get("amount_total", 0) / 100  # Convert cents to dollars

        if not event_id or not user_id:
            error_msg = "Missing event_id or user_id in session metadata"
            logger.error(error_msg)
            raise WebhookProcessingError(error_msg)

        logger.info(f"Processing event RSVP payment for user {user_id}, event {event_id}")

        try:
            # Get event details
            event_result = self.db.get_document("events", event_id)
            event = event_result.get("data", {})

            if not event:
                raise WebhookProcessingError(f"Event {event_id} not found")

            # Get user details
            user_result = self.db.get_document("users", user_id)
            user = user_result.get("data", {})

            if not user:
                raise WebhookProcessingError(f"User {user_id} not found")

            # Check for duplicate RSVP (idempotency)
            existing_rsvp_result = self.db.query_documents(
                collection="rsvps",
                filters={
                    "event_id": event_id,
                    "user_id": user_id
                },
                limit=1
            )

            if existing_rsvp_result.get("documents"):
                logger.warning(f"RSVP already exists for user {user_id}, event {event_id}")
                existing_rsvp = existing_rsvp_result.get("documents")[0].get("data", {})
                return {
                    "status": "success",
                    "action": "event_rsvp_payment",
                    "rsvp_id": existing_rsvp.get("id"),
                    "message": "RSVP already exists"
                }

            # Create payment record
            now = datetime.utcnow()
            payment_data = {
                "user_id": user_id,
                "amount": amount_total,
                "currency": session.get("currency", "usd").upper(),
                "status": PaymentStatus.SUCCEEDED.value,
                "stripe_payment_intent_id": session.get("payment_intent"),
                "stripe_charge_id": None,  # Will be populated from payment_intent
                "payment_method": "card",
                "description": f"Event registration: {event.get('title')}",
                "processed_at": now.isoformat(),
                "metadata": {
                    "type": "event_rsvp",
                    "event_id": event_id,
                    "checkout_session_id": session.get("id")
                }
            }

            payment_result = self.db.create_document("payments", payment_data)
            payment_id = payment_result.get("id")

            logger.info(f"Created payment record {payment_id} for event RSVP")

            # Create RSVP record
            rsvp_data = {
                "event_id": event_id,
                "user_id": user_id,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or session.get("customer_email"),
                "user_email": user.get("email") or session.get("customer_email"),
                "user_phone": user.get("phone"),
                "rsvp_date": now.isoformat(),
                "status": RSVPStatus.CONFIRMED.value,
                "payment_id": payment_id,
                "payment_status": PaymentStatus.SUCCEEDED.value,
                "check_in_status": False,
                "check_in_time": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }

            rsvp_result = self.db.create_document("rsvps", rsvp_data)
            rsvp_id = rsvp_result.get("id")

            logger.info(f"Created RSVP {rsvp_id} for user {user_id}, event {event_id}")

            # Update event attendee count
            current_attendees = event.get("current_attendees", 0)
            self.db.update_document(
                "events",
                event_id,
                {"current_attendees": current_attendees + 1},
                merge=True
            )

            # Generate QR code for check-in
            from backend.services.rsvp_service import get_rsvp_service
            rsvp_service = get_rsvp_service()
            qr_code = rsvp_service.generate_qr_code(rsvp_id, event_id, user_id)

            # Send ticket/confirmation email with QR code
            try:
                self.email_service.send_paid_event_ticket(
                    email=rsvp_data["user_email"],
                    user_name=rsvp_data["user_name"],
                    event_title=event.get("title"),
                    event_date=event.get("start_datetime"),
                    event_location=event.get("location_name"),
                    event_address=event.get("address"),
                    amount=amount_total,
                    currency="USD",
                    qr_code=qr_code,
                    rsvp_id=rsvp_id
                )
                logger.info(f"Sent event ticket email to {rsvp_data['user_email']}")
            except Exception as e:
                logger.error(f"Failed to send event ticket email: {e}")
                # Don't fail webhook if email fails

            # Create audit log
            self._create_audit_log(
                action=AuditAction.PAYMENT.value,
                resource_type="rsvps",
                resource_id=rsvp_id,
                description=f"Event RSVP payment completed: ${amount_total} for {event.get('title')}",
                user_id=user_id,
                changes={
                    "payment_id": payment_id,
                    "event_id": event_id,
                    "amount": amount_total
                }
            )

            return {
                "status": "success",
                "action": "event_rsvp_payment",
                "rsvp_id": rsvp_id,
                "payment_id": payment_id,
                "user_id": user_id,
                "event_id": event_id,
                "amount": amount_total
            }

        except Exception as e:
            logger.error(f"Error processing event RSVP payment: {e}")
            raise WebhookProcessingError(f"Failed to process event RSVP payment: {str(e)}")

    # Helper methods

    def _find_user_by_stripe_customer_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Find user by Stripe customer ID"""
        try:
            result = self.db.query_documents(
                collection="users",
                filters={"stripe_customer_id": customer_id},
                limit=1
            )

            documents = result.get("documents", [])
            return documents[0] if documents else None

        except ZeroDBError as e:
            logger.error(f"Error finding user by Stripe customer ID: {e}")
            return None

    def _find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email address"""
        try:
            result = self.db.query_documents(
                collection="users",
                filters={"email": email.lower()},
                limit=1
            )

            documents = result.get("documents", [])
            return documents[0] if documents else None

        except ZeroDBError as e:
            logger.error(f"Error finding user by email: {e}")
            return None

    def _find_subscription_by_stripe_id(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Find subscription by Stripe subscription ID"""
        try:
            result = self.db.query_documents(
                collection="subscriptions",
                filters={"stripe_subscription_id": subscription_id},
                limit=1
            )

            documents = result.get("documents", [])
            return documents[0] if documents else None

        except ZeroDBError as e:
            logger.error(f"Error finding subscription by Stripe ID: {e}")
            return None


# Global webhook service instance (singleton pattern)
_webhook_service_instance: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """
    Get or create the global WebhookService instance

    Returns:
        WebhookService instance
    """
    global _webhook_service_instance

    if _webhook_service_instance is None:
        _webhook_service_instance = WebhookService()

    return _webhook_service_instance
