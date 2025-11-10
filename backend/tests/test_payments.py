"""
Unit tests for payment history routes

Tests payment listing, filtering, pagination, CSV export,
and access control for payment records.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi import status
from fastapi.testclient import TestClient

from backend.routes.payments import (
    format_payment_response,
    filter_payments_by_date_range,
)


class TestPaymentFormatting:
    """Test payment data formatting functions"""

    def test_format_payment_response_basic(self):
        """Test basic payment formatting"""
        payment = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "amount": 99.00,
            "currency": "USD",
            "status": "succeeded",
            "payment_method": "card_1234567890",
            "description": "Annual Membership",
            "created_at": "2025-01-15T10:30:00Z",
        }

        result = format_payment_response(payment)

        assert result["id"] == str(payment["id"])
        assert result["amount"] == 99.00
        assert result["currency"] == "USD"
        assert result["status"] == "succeeded"
        assert result["payment_method"] == "****7890"  # Last 4 digits
        assert result["description"] == "Annual Membership"

    def test_format_payment_response_with_refund(self):
        """Test formatting payment with refund data"""
        payment = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "amount": 49.00,
            "currency": "USD",
            "status": "refunded",
            "refunded_amount": 49.00,
            "refunded_at": "2025-01-20T14:00:00Z",
            "refund_reason": "Customer request",
            "created_at": "2025-01-15T10:30:00Z",
        }

        result = format_payment_response(payment)

        assert result["status"] == "refunded"
        assert result["refunded_amount"] == 49.00
        assert result["refunded_at"] == "2025-01-20T14:00:00Z"
        assert result["refund_reason"] == "Customer request"

    def test_format_payment_response_with_stripe_urls(self):
        """Test formatting with Stripe receipt and invoice URLs"""
        payment = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "amount": 99.00,
            "currency": "USD",
            "status": "succeeded",
            "stripe_charge_id": "ch_123456",
            "stripe_payment_intent_id": "pi_123456",
            "created_at": "2025-01-15T10:30:00Z",
        }

        result = format_payment_response(payment)

        assert "ch_123456" in result["receipt_url"]
        assert "pi_123456" in result["invoice_url"]

    def test_format_payment_response_missing_fields(self):
        """Test formatting with minimal payment data"""
        payment = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "amount": 99.00,
            "created_at": "2025-01-15T10:30:00Z",
        }

        result = format_payment_response(payment)

        assert result["currency"] == "USD"  # Default
        assert result["status"] == "pending"  # Default
        assert result["payment_method"] == ""
        assert result["description"] is None
        assert result["refunded_amount"] == 0.0


class TestDateRangeFiltering:
    """Test date range filtering functionality"""

    def test_filter_payments_no_dates(self):
        """Test filtering with no date range returns all payments"""
        payments = [
            {"id": "1", "created_at": "2025-01-15T10:00:00Z"},
            {"id": "2", "created_at": "2025-01-20T10:00:00Z"},
            {"id": "3", "created_at": "2025-01-25T10:00:00Z"},
        ]

        result = filter_payments_by_date_range(payments, None, None)

        assert len(result) == 3

    def test_filter_payments_with_start_date(self):
        """Test filtering with start date"""
        payments = [
            {"id": "1", "created_at": "2025-01-15T10:00:00Z"},
            {"id": "2", "created_at": "2025-01-20T10:00:00Z"},
            {"id": "3", "created_at": "2025-01-25T10:00:00Z"},
        ]

        start_date = datetime(2025, 1, 20, 0, 0, 0)
        result = filter_payments_by_date_range(payments, start_date, None)

        assert len(result) == 2
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"

    def test_filter_payments_with_end_date(self):
        """Test filtering with end date"""
        payments = [
            {"id": "1", "created_at": "2025-01-15T10:00:00Z"},
            {"id": "2", "created_at": "2025-01-20T10:00:00Z"},
            {"id": "3", "created_at": "2025-01-25T10:00:00Z"},
        ]

        end_date = datetime(2025, 1, 20, 23, 59, 59)
        result = filter_payments_by_date_range(payments, None, end_date)

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    def test_filter_payments_with_date_range(self):
        """Test filtering with both start and end dates"""
        payments = [
            {"id": "1", "created_at": "2025-01-15T10:00:00Z"},
            {"id": "2", "created_at": "2025-01-20T10:00:00Z"},
            {"id": "3", "created_at": "2025-01-25T10:00:00Z"},
        ]

        start_date = datetime(2025, 1, 18, 0, 0, 0)
        end_date = datetime(2025, 1, 22, 23, 59, 59)
        result = filter_payments_by_date_range(payments, start_date, end_date)

        assert len(result) == 1
        assert result[0]["id"] == "2"

    def test_filter_payments_invalid_date_format(self):
        """Test filtering handles invalid date formats gracefully"""
        payments = [
            {"id": "1", "created_at": "invalid-date"},
            {"id": "2", "created_at": "2025-01-20T10:00:00Z"},
        ]

        start_date = datetime(2025, 1, 18, 0, 0, 0)
        result = filter_payments_by_date_range(payments, start_date, None)

        assert len(result) == 1
        assert result[0]["id"] == "2"


class TestPaymentListEndpoint:
    """Test the GET /api/payments endpoint"""

    @pytest.fixture
    def mock_zerodb_client(self):
        """Mock ZeroDB client"""
        with patch("backend.routes.payments.get_zerodb_client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_auth(self, client):
        """Mock authentication"""
        user_data = {"id": str(uuid4()), "email": "test@example.com"}

        async def mock_get_current_user():
            return user_data

        # Override dependency
        with patch("backend.routes.payments.get_current_user", mock_get_current_user):
            yield user_data

    @pytest.fixture
    def sample_payments(self):
        """Sample payment data"""
        user_id = str(uuid4())
        return [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "amount": 99.00,
                "currency": "USD",
                "status": "succeeded",
                "payment_method": "card_1234",
                "description": "Payment 1",
                "created_at": "2025-01-15T10:00:00Z",
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "amount": 49.00,
                "currency": "USD",
                "status": "succeeded",
                "payment_method": "card_5678",
                "description": "Payment 2",
                "created_at": "2025-01-10T10:00:00Z",
            },
        ]

    def test_list_payments_success(
        self, client, mock_zerodb_client, mock_auth, sample_payments
    ):
        """Test successful payment listing"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": sample_payments,
            "total": len(sample_payments),
        }

        response = client.get("/api/payments?page=1&per_page=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "payments" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        assert len(data["payments"]) == 2

    def test_list_payments_with_pagination(
        self, client, mock_zerodb_client, mock_auth, sample_payments
    ):
        """Test payment listing with pagination"""
        # Create 15 mock payments
        payments = sample_payments * 8  # 16 total
        mock_zerodb_client.query_documents.return_value = {
            "documents": payments,
            "total": len(payments),
        }

        # Request page 2 with 10 items per page
        response = client.get("/api/payments?page=2&per_page=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] == 16
        assert data["total_pages"] == 2

    def test_list_payments_with_status_filter(
        self, client, mock_zerodb_client, mock_auth
    ):
        """Test payment listing with status filter"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": [],
            "total": 0,
        }

        response = client.get("/api/payments?status=succeeded")

        assert response.status_code == status.HTTP_200_OK
        # Verify the filter was passed to ZeroDB
        mock_zerodb_client.query_documents.assert_called_once()
        call_kwargs = mock_zerodb_client.query_documents.call_args[1]
        assert call_kwargs["filters"]["status"]["$eq"] == "succeeded"

    def test_list_payments_with_date_filters(
        self, client, mock_zerodb_client, mock_auth, sample_payments
    ):
        """Test payment listing with date range filters"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": sample_payments,
            "total": len(sample_payments),
        }

        response = client.get(
            "/api/payments?start_date=2025-01-01T00:00:00Z&end_date=2025-01-31T23:59:59Z"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["payments"]) > 0

    def test_list_payments_invalid_date_format(
        self, client, mock_zerodb_client, mock_auth
    ):
        """Test payment listing with invalid date format"""
        response = client.get("/api/payments?start_date=invalid-date")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_payments_unauthorized(self, client, mock_zerodb_client):
        """Test payment listing without authentication"""
        with patch("backend.routes.payments.get_current_user") as mock_auth:
            mock_auth.side_effect = Exception("Unauthorized")

            response = client.get("/api/payments")

            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

    def test_list_payments_empty_result(
        self, client, mock_zerodb_client, mock_auth
    ):
        """Test payment listing with no payments"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": [],
            "total": 0,
        }

        response = client.get("/api/payments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["payments"] == []
        assert data["total"] == 0


class TestPaymentDetailEndpoint:
    """Test the GET /api/payments/{payment_id} endpoint"""

    @pytest.fixture
    def mock_zerodb_client(self):
        """Mock ZeroDB client"""
        with patch("backend.routes.payments.get_zerodb_client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_auth(self, client):
        """Mock authentication"""
        user_id = str(uuid4())
        user_data = {"id": user_id, "email": "test@example.com"}

        async def mock_get_current_user():
            return user_data

        # Override dependency
        with patch("backend.routes.payments.get_current_user", mock_get_current_user):
            yield user_data, user_id

    def test_get_payment_success(self, client, mock_zerodb_client, mock_auth):
        """Test successful payment retrieval"""
        mock_auth_func, user_id = mock_auth
        payment_id = str(uuid4())

        mock_zerodb_client.get_document.return_value = {
            "id": payment_id,
            "user_id": user_id,
            "amount": 99.00,
            "currency": "USD",
            "status": "succeeded",
            "created_at": "2025-01-15T10:00:00Z",
        }

        response = client.get(f"/api/payments/{payment_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == payment_id
        assert data["amount"] == 99.00

    def test_get_payment_not_found(self, client, mock_zerodb_client, mock_auth):
        """Test payment not found"""
        from backend.services.zerodb_service import ZeroDBNotFoundError

        payment_id = str(uuid4())
        mock_zerodb_client.get_document.side_effect = ZeroDBNotFoundError(
            "Payment not found"
        )

        response = client.get(f"/api/payments/{payment_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_payment_access_denied(self, client, mock_zerodb_client, mock_auth):
        """Test user cannot access another user's payment"""
        mock_auth_func, user_id = mock_auth
        payment_id = str(uuid4())
        other_user_id = str(uuid4())

        mock_zerodb_client.get_document.return_value = {
            "id": payment_id,
            "user_id": other_user_id,  # Different user
            "amount": 99.00,
            "currency": "USD",
            "status": "succeeded",
            "created_at": "2025-01-15T10:00:00Z",
        }

        response = client.get(f"/api/payments/{payment_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPaymentExportEndpoint:
    """Test the GET /api/payments/export/csv endpoint"""

    @pytest.fixture
    def mock_zerodb_client(self):
        """Mock ZeroDB client"""
        with patch("backend.routes.payments.get_zerodb_client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_auth(self, client):
        """Mock authentication"""
        user_data = {"id": str(uuid4()), "email": "test@example.com"}

        async def mock_get_current_user():
            return user_data

        # Override dependency
        with patch("backend.routes.payments.get_current_user", mock_get_current_user):
            yield user_data

    @pytest.fixture
    def sample_payments(self):
        """Sample payment data"""
        user_id = str(uuid4())
        return [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "amount": 99.00,
                "currency": "USD",
                "status": "succeeded",
                "description": "Payment 1",
                "created_at": "2025-01-15T10:00:00Z",
            },
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "amount": 49.00,
                "currency": "USD",
                "status": "succeeded",
                "description": "Payment 2",
                "created_at": "2025-01-10T10:00:00Z",
            },
        ]

    def test_export_csv_success(
        self, client, mock_zerodb_client, mock_auth, sample_payments
    ):
        """Test successful CSV export"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": sample_payments,
            "total": len(sample_payments),
        }

        response = client.get("/api/payments/export/csv")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Check CSV content
        content = response.text
        assert "Date,Amount,Currency,Status" in content
        assert "Payment 1" in content
        assert "Payment 2" in content

    def test_export_csv_with_filters(
        self, client, mock_zerodb_client, mock_auth, sample_payments
    ):
        """Test CSV export with filters"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": sample_payments,
            "total": len(sample_payments),
        }

        response = client.get(
            "/api/payments/export/csv?status=succeeded&start_date=2025-01-01T00:00:00Z"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    def test_export_csv_empty(self, client, mock_zerodb_client, mock_auth):
        """Test CSV export with no payments"""
        mock_zerodb_client.query_documents.return_value = {
            "documents": [],
            "total": 0,
        }

        response = client.get("/api/payments/export/csv")

        assert response.status_code == status.HTTP_200_OK
        # Should still return CSV with header
        content = response.text
        assert "Date,Amount,Currency,Status" in content


@pytest.fixture(scope="function")
def client():
    """Create test client"""
    from backend.app import app

    return TestClient(app)
