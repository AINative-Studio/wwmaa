"""
Comprehensive Tests for Stripe Webhook Handler

Tests cover:
- Signature verification (valid/invalid)
- Each event type handler
- Idempotency (duplicate events)
- Error handling
- ZeroDB document creation/updates
- Email notifications

Target: 80%+ test coverage
"""

import json
import time
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app import app
from backend.services.webhook_service import (
    WebhookService,
    DuplicateEventError,
    WebhookProcessingError
)


class TestWebhookSignatureVerification:
    """Test webhook signature verification"""

    def test_missing_signature_header(self):
        """Test webhook with missing signature header returns 400"""
        client = TestClient(app)

        response = client.post(
            "/api/webhooks/stripe",
            json={"type": "test.event"},
            headers={}
        )

        assert response.status_code == 400
        assert "Stripe-Signature" in response.json()["detail"]

    @patch("stripe.Webhook.construct_event")
    def test_invalid_signature(self, mock_construct_event):
        """Test webhook with invalid signature returns 400"""
        mock_construct_event.side_effect = Exception("Invalid signature")

        client = TestClient(app)

        response = client.post(
            "/api/webhooks/stripe",
            json={"type": "test.event"},
            headers={"Stripe-Signature": "invalid_signature"}
        )

        assert response.status_code == 400

    @patch("stripe.Webhook.construct_event")
    @patch("backend.services.webhook_service.WebhookService.process_webhook_event")
    def test_valid_signature(self, mock_process, mock_construct_event):
        """Test webhook with valid signature processes successfully"""
        # Mock Stripe event
        mock_event = Mock()
        mock_event.id = "evt_test123"
        mock_event.type = "checkout.session.completed"
        mock_event.to_dict.return_value = {"id": "evt_test123", "type": "checkout.session.completed"}

        mock_construct_event.return_value = mock_event
        mock_process.return_value = {"status": "success"}

        client = TestClient(app)

        response = client.post(
            "/api/webhooks/stripe",
            json={"type": "checkout.session.completed"},
            headers={"Stripe-Signature": "valid_signature"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestWebhookIdempotency:
    """Test webhook idempotency (duplicate event handling)"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_duplicate_event_detection(self, mock_db):
        """Test that duplicate events are detected"""
        # Mock database to return existing event
        mock_db.query_documents.return_value = {
            "documents": [{"id": "event_123", "stripe_event_id": "evt_test123"}]
        }

        service = WebhookService()
        service.db = mock_db

        assert service._is_duplicate_event("evt_test123") is True

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_new_event_not_duplicate(self, mock_db):
        """Test that new events are not marked as duplicates"""
        # Mock database to return no existing events
        mock_db.query_documents.return_value = {"documents": []}

        service = WebhookService()
        service.db = mock_db

        assert service._is_duplicate_event("evt_new123") is False

    @patch("stripe.Webhook.construct_event")
    @patch("backend.services.webhook_service.WebhookService._is_duplicate_event")
    def test_duplicate_event_returns_200(self, mock_is_duplicate, mock_construct_event):
        """Test that duplicate events return 200 OK to prevent Stripe retries"""
        mock_event = Mock()
        mock_event.id = "evt_test123"
        mock_event.type = "test.event"
        mock_event.to_dict.return_value = {}

        mock_construct_event.return_value = mock_event
        mock_is_duplicate.return_value = True

        client = TestClient(app)

        response = client.post(
            "/api/webhooks/stripe",
            json={},
            headers={"Stripe-Signature": "valid_signature"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"


class TestCheckoutCompletedEvent:
    """Test checkout.session.completed event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    @patch("backend.services.email_service.EmailService")
    def test_checkout_completed_creates_subscription(self, mock_email, mock_db):
        """Test that checkout.session.completed creates subscription in ZeroDB"""
        # Mock user lookup
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"id": "user_123", "data": {"id": "user_123", "email": "test@example.com", "role": "public"}}]},  # User lookup
        ]

        # Mock document creation
        mock_db.create_document.return_value = {"id": "sub_123"}
        mock_db.update_document.return_value = {}

        event_data = {
            "data": {
                "object": {
                    "id": "cs_test123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "customer_email": "test@example.com",
                    "amount_total": 2000,
                    "currency": "usd",
                    "payment_status": "paid"
                }
            }
        }

        service = WebhookService()
        service.db = mock_db
        service.email_service = mock_email

        result = service._handle_checkout_completed(event_data)

        assert result["status"] == "success"
        assert result["action"] == "checkout_completed"

        # Verify subscription was created
        assert mock_db.create_document.called
        create_call = mock_db.create_document.call_args
        assert create_call[1]["collection"] == "subscriptions"

        # Verify user role was updated to 'member'
        assert mock_db.update_document.called

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_checkout_completed_user_not_found(self, mock_db):
        """Test checkout.session.completed fails when user not found"""
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": []},  # No user found by customer ID
            {"documents": []},  # No user found by email
        ]

        event_data = {
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "customer_email": "notfound@example.com"
                }
            }
        }

        service = WebhookService()
        service.db = mock_db

        with pytest.raises(WebhookProcessingError):
            service._handle_checkout_completed(event_data)


class TestInvoicePaidEvent:
    """Test invoice.paid event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    @patch("backend.services.email_service.EmailService")
    def test_invoice_paid_creates_payment_record(self, mock_email, mock_db):
        """Test that invoice.paid creates payment record in ZeroDB"""
        # Mock lookups
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"data": {"id": "user_123", "email": "test@example.com"}}]},  # User lookup
            {"documents": [{"data": {"id": "sub_123"}}]},  # Subscription lookup
        ]

        # Mock payment creation
        mock_db.create_document.return_value = {"id": "payment_123"}

        event_data = {
            "data": {
                "object": {
                    "id": "in_test123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "amount_paid": 2000,
                    "currency": "usd",
                    "payment_intent": "pi_test123",
                    "charge": "ch_test123",
                    "hosted_invoice_url": "https://invoice.stripe.com/i/test"
                }
            }
        }

        service = WebhookService()
        service.db = mock_db
        service.email_service = mock_email

        result = service._handle_invoice_paid(event_data)

        assert result["status"] == "success"
        assert result["action"] == "invoice_paid"

        # Verify payment record was created
        assert mock_db.create_document.called
        create_call = mock_db.create_document.call_args
        assert create_call[1]["collection"] == "payments"
        assert create_call[1]["data"]["amount"] == 20.0  # Converted from cents


class TestInvoicePaymentFailedEvent:
    """Test invoice.payment_failed event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    @patch("backend.services.email_service.EmailService")
    def test_invoice_payment_failed_updates_subscription(self, mock_email, mock_db):
        """Test that invoice.payment_failed updates subscription to past_due"""
        # Mock lookups
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"data": {"id": "user_123", "email": "test@example.com", "first_name": "Test"}}]},  # User lookup
            {"documents": [{"data": {"id": "sub_123"}}]},  # Subscription lookup
        ]

        # Mock updates
        mock_db.update_document.return_value = {}
        mock_db.create_document.return_value = {"id": "payment_123"}

        event_data = {
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "amount_due": 2000,
                    "currency": "usd",
                    "payment_intent": "pi_test123",
                    "attempt_count": 1
                }
            }
        }

        service = WebhookService()
        service.db = mock_db
        service.email_service = mock_email

        result = service._handle_invoice_payment_failed(event_data)

        assert result["status"] == "success"
        assert result["subscription_status"] == "past_due"

        # Verify subscription status was updated
        assert mock_db.update_document.called

        # Verify dunning email was sent
        assert mock_email.send_payment_failed_email.called


class TestSubscriptionUpdatedEvent:
    """Test customer.subscription.updated event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_subscription_updated_changes_status(self, mock_db):
        """Test that subscription.updated updates subscription status"""
        # Mock lookups
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"data": {"id": "sub_123", "user_id": "user_123", "status": "active"}}]},  # Subscription lookup
        ]

        mock_db.update_document.return_value = {}

        event_data = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "status": "past_due",
                    "current_period_end": 1234567890,
                    "canceled_at": None,
                    "cancel_at_period_end": False
                }
            }
        }

        service = WebhookService()
        service.db = mock_db

        result = service._handle_subscription_updated(event_data)

        assert result["status"] == "success"
        assert result["new_status"] == "past_due"

        # Verify subscription was updated
        assert mock_db.update_document.called


class TestSubscriptionDeletedEvent:
    """Test customer.subscription.deleted event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    @patch("backend.services.email_service.EmailService")
    def test_subscription_deleted_downgrades_user(self, mock_email, mock_db):
        """Test that subscription.deleted downgrades user to public role"""
        # Mock lookups
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"data": {"id": "user_123", "email": "test@example.com", "role": "member", "first_name": "Test"}}]},  # User lookup
            {"documents": [{"data": {"id": "sub_123"}}]},  # Subscription lookup
        ]

        mock_db.update_document.return_value = {}

        event_data = {
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123"
                }
            }
        }

        service = WebhookService()
        service.db = mock_db
        service.email_service = mock_email

        result = service._handle_subscription_deleted(event_data)

        assert result["status"] == "success"
        assert result["new_role"] == "public"

        # Verify subscription was canceled
        assert mock_db.update_document.called

        # Verify cancellation email was sent
        assert mock_email.send_subscription_canceled_email.called


class TestChargeRefundedEvent:
    """Test charge.refunded event handler"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    @patch("backend.services.email_service.EmailService")
    def test_charge_refunded_updates_payment(self, mock_email, mock_db):
        """Test that charge.refunded updates payment record"""
        # Mock lookups
        mock_db.query_documents.side_effect = [
            {"documents": []},  # No duplicate event
            {"documents": [{"data": {"id": "user_123", "email": "test@example.com", "first_name": "Test"}}]},  # User lookup
            {"documents": [{"id": "payment_123", "data": {"status": "succeeded"}}]},  # Payment lookup
        ]

        mock_db.update_document.return_value = {}

        event_data = {
            "data": {
                "object": {
                    "id": "ch_test123",
                    "customer": "cus_test123",
                    "amount_refunded": 2000,
                    "currency": "usd",
                    "refunds": {
                        "data": [
                            {"reason": "requested_by_customer"}
                        ]
                    }
                }
            }
        }

        service = WebhookService()
        service.db = mock_db
        service.email_service = mock_email

        result = service._handle_charge_refunded(event_data)

        assert result["status"] == "success"
        assert result["refund_amount"] == 20.0  # Converted from cents

        # Verify payment record was updated
        assert mock_db.update_document.called

        # Verify refund email was sent
        assert mock_email.send_refund_confirmation_email.called


class TestWebhookEventStorage:
    """Test webhook event storage for debugging"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_successful_event_stored(self, mock_db):
        """Test that successful events are stored in ZeroDB"""
        mock_db.create_document.return_value = {"id": "webhook_event_123"}

        service = WebhookService()
        service.db = mock_db

        result = service._store_webhook_event(
            event_id="evt_test123",
            event_type="checkout.session.completed",
            event_data={"test": "data"},
            processing_status="processed"
        )

        assert mock_db.create_document.called
        create_call = mock_db.create_document.call_args
        assert create_call[1]["collection"] == "webhook_events"
        assert create_call[1]["data"]["stripe_event_id"] == "evt_test123"
        assert create_call[1]["data"]["processing_status"] == "processed"

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_failed_event_stored_with_error(self, mock_db):
        """Test that failed events are stored with error message"""
        mock_db.create_document.return_value = {"id": "webhook_event_123"}

        service = WebhookService()
        service.db = mock_db

        result = service._store_webhook_event(
            event_id="evt_test123",
            event_type="checkout.session.completed",
            event_data={"test": "data"},
            processing_status="failed",
            error_message="Processing error occurred"
        )

        assert mock_db.create_document.called
        create_call = mock_db.create_document.call_args
        assert create_call[1]["data"]["processing_status"] == "failed"
        assert create_call[1]["data"]["error_message"] == "Processing error occurred"


class TestWebhookAuditLogging:
    """Test audit logging for webhook events"""

    @patch("backend.services.zerodb_service.ZeroDBClient")
    def test_audit_log_created_for_event(self, mock_db):
        """Test that audit logs are created for webhook events"""
        mock_db.create_document.return_value = {"id": "audit_log_123"}

        service = WebhookService()
        service.db = mock_db

        result = service._create_audit_log(
            action="payment",
            resource_type="payments",
            resource_id="payment_123",
            description="Payment received",
            user_id="user_123",
            success=True
        )

        assert mock_db.create_document.called
        create_call = mock_db.create_document.call_args
        assert create_call[1]["collection"] == "audit_logs"
        assert create_call[1]["data"]["action"] == "payment"
        assert create_call[1]["data"]["resource_type"] == "payments"


class TestWebhookPerformance:
    """Test webhook response time requirements"""

    @patch("stripe.Webhook.construct_event")
    @patch("backend.services.webhook_service.WebhookService.process_webhook_event")
    def test_webhook_responds_within_5_seconds(self, mock_process, mock_construct_event):
        """Test that webhook responds within 5 seconds (Stripe requirement)"""
        mock_event = Mock()
        mock_event.id = "evt_test123"
        mock_event.type = "test.event"
        mock_event.to_dict.return_value = {}

        mock_construct_event.return_value = mock_event
        mock_process.return_value = {"status": "success", "processing_time_seconds": 0.5}

        client = TestClient(app)

        start_time = time.time()
        response = client.post(
            "/api/webhooks/stripe",
            json={},
            headers={"Stripe-Signature": "valid_signature"}
        )
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5.0  # Must respond within 5 seconds


class TestWebhookHealthCheck:
    """Test webhook health check endpoint"""

    def test_webhook_health_endpoint(self):
        """Test webhook health check returns status"""
        client = TestClient(app)

        response = client.get("/api/webhooks/stripe/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "webhook_secret_configured" in response.json()


class TestWebhookErrorHandling:
    """Test webhook error handling"""

    @patch("stripe.Webhook.construct_event")
    @patch("backend.services.webhook_service.WebhookService.process_webhook_event")
    def test_processing_error_returns_200(self, mock_process, mock_construct_event):
        """Test that processing errors still return 200 OK to prevent retries"""
        mock_event = Mock()
        mock_event.id = "evt_test123"
        mock_event.type = "test.event"
        mock_event.to_dict.return_value = {}

        mock_construct_event.return_value = mock_event
        mock_process.side_effect = WebhookProcessingError("Processing failed")

        client = TestClient(app)

        response = client.post(
            "/api/webhooks/stripe",
            json={},
            headers={"Stripe-Signature": "valid_signature"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend/services/webhook_service", "--cov=backend/routes/webhooks", "--cov-report=term-missing"])
