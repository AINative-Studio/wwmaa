"""
Unit Tests for GDPR Service

Tests data export functionality including:
- Data collection from all collections
- JSON export generation
- Email notifications
- File storage and URL generation
- Error handling

Target: 80%+ code coverage
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from backend.services.gdpr_service import (
    GDPRService,
    DataExportError,
    GDPRServiceError
)
from backend.services.zerodb_service import ZeroDBError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db_client():
    """Mock ZeroDB client"""
    mock = Mock()
    mock.find = Mock(return_value={"documents": []})
    mock.insert_one = Mock(return_value={"id": "audit_log_123"})
    mock.upload_object = Mock(return_value={"key": "test_key", "size": 1024})
    mock.upload_object_from_bytes = Mock(return_value={"key": "test_key", "size": 1024})
    mock.generate_signed_url = Mock(return_value="https://example.com/download/test")
    mock.get_object_metadata = Mock(return_value={
        "created_at": datetime.utcnow().isoformat(),
        "expiry_date": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "size": 1024
    })
    mock.delete_object = Mock(return_value=True)
    mock.delete_object_by_key = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    mock = Mock()
    mock._send_email = Mock()
    return mock


@pytest.fixture
def gdpr_service(mock_db_client, mock_email_service):
    """GDPR service instance with mocked dependencies"""
    return GDPRService(
        db_client=mock_db_client,
        email_service=mock_email_service
    )


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": "user_123",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data"""
    return [
        {
            "id": "profile_1",
            "user_id": "user_123",
            "name": "John Doe",
            "email": "test@example.com",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_application_data():
    """Sample application data"""
    return [
        {
            "id": "app_1",
            "user_id": "user_123",
            "status": "approved",
            "submitted_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "app_2",
            "user_id": "user_123",
            "status": "pending",
            "submitted_at": "2025-01-05T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_payment_data():
    """Sample payment data"""
    return [
        {
            "id": "pay_1",
            "user_id": "user_123",
            "amount": 5000,
            "currency": "usd",
            "status": "succeeded",
            "card_last4": "4242",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_gdpr_service_initialization():
    """Test GDPR service initialization"""
    service = GDPRService()
    assert service is not None
    assert service.db is not None
    assert service.email_service is not None


def test_gdpr_service_with_custom_clients(mock_db_client, mock_email_service):
    """Test initialization with custom clients"""
    service = GDPRService(
        db_client=mock_db_client,
        email_service=mock_email_service
    )
    assert service.db == mock_db_client
    assert service.email_service == mock_email_service


# ============================================================================
# DATA EXPORT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_export_user_data_success(
    gdpr_service,
    mock_db_client,
    mock_email_service,
    sample_user_data,
    sample_profile_data
):
    """Test successful user data export"""
    # Mock database responses
    mock_db_client.find.return_value = {"documents": sample_profile_data}

    # Execute export
    result = await gdpr_service.export_user_data(
        user_id=sample_user_data["user_id"],
        user_email=sample_user_data["email"]
    )

    # Verify result structure
    assert "export_id" in result
    assert result["status"] == "completed"
    assert "download_url" in result
    assert "expiry_date" in result
    assert "file_size_bytes" in result
    assert "record_counts" in result

    # Verify database interactions
    assert mock_db_client.find.called
    assert mock_db_client.upload_object_from_bytes.called
    assert mock_db_client.generate_signed_url.called
    assert mock_db_client.insert_one.called  # Audit log

    # Verify email sent
    assert mock_email_service._send_email.called


@pytest.mark.asyncio
async def test_export_user_data_with_multiple_collections(
    gdpr_service,
    mock_db_client,
    sample_user_data,
    sample_profile_data,
    sample_application_data,
    sample_payment_data
):
    """Test export with data from multiple collections"""
    # Mock different responses for different collections
    def mock_find_side_effect(collection, filter_query, limit):
        if collection == "profiles":
            return {"documents": sample_profile_data}
        elif collection == "applications":
            return {"documents": sample_application_data}
        elif collection == "payments":
            return {"documents": sample_payment_data}
        else:
            return {"documents": []}

    mock_db_client.find.side_effect = mock_find_side_effect

    result = await gdpr_service.export_user_data(
        user_id=sample_user_data["user_id"],
        user_email=sample_user_data["email"]
    )

    # Verify all collections were queried
    assert mock_db_client.find.call_count >= len(GDPRService.COLLECTIONS)

    # Verify record counts
    assert result["record_counts"]["profiles"] == len(sample_profile_data)
    assert result["record_counts"]["applications"] == len(sample_application_data)
    assert result["record_counts"]["payments"] == len(sample_payment_data)


@pytest.mark.asyncio
async def test_export_user_data_handles_empty_collections(
    gdpr_service,
    mock_db_client,
    sample_user_data
):
    """Test export when user has no data in some collections"""
    # Mock empty responses
    mock_db_client.find.return_value = {"documents": []}

    result = await gdpr_service.export_user_data(
        user_id=sample_user_data["user_id"],
        user_email=sample_user_data["email"]
    )

    # Verify successful export even with empty data
    assert result["status"] == "completed"
    assert all(count == 0 for count in result["record_counts"].values())


@pytest.mark.asyncio
async def test_export_user_data_handles_collection_errors(
    gdpr_service,
    mock_db_client,
    sample_user_data,
    sample_profile_data
):
    """Test export handles errors from individual collections gracefully"""
    # Mock error for one collection, success for others
    def mock_find_side_effect(collection, filter_query, limit):
        if collection == "profiles":
            return {"documents": sample_profile_data}
        elif collection == "payments":
            raise ZeroDBError("Collection not found")
        else:
            return {"documents": []}

    mock_db_client.find.side_effect = mock_find_side_effect

    # Should still complete export
    result = await gdpr_service.export_user_data(
        user_id=sample_user_data["user_id"],
        user_email=sample_user_data["email"]
    )

    assert result["status"] == "completed"
    # Profile data should be present
    assert result["record_counts"]["profiles"] == len(sample_profile_data)


@pytest.mark.asyncio
async def test_export_user_data_storage_failure(
    gdpr_service,
    mock_db_client,
    sample_user_data
):
    """Test export failure when storage fails"""
    mock_db_client.find.return_value = {"documents": []}
    mock_db_client.upload_object_from_bytes.side_effect = Exception("Storage error")

    with pytest.raises(DataExportError) as exc_info:
        await gdpr_service.export_user_data(
            user_id=sample_user_data["user_id"],
            user_email=sample_user_data["email"]
        )

    assert "Failed to export user data" in str(exc_info.value)


# ============================================================================
# DATA COLLECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_collect_collection_data(
    gdpr_service,
    mock_db_client,
    sample_profile_data
):
    """Test collecting data from a specific collection"""
    mock_db_client.find.return_value = {"documents": sample_profile_data}

    data = await gdpr_service._collect_collection_data(
        collection_name="profiles",
        user_id="user_123"
    )

    assert len(data) == len(sample_profile_data)
    assert mock_db_client.find.called
    call_args = mock_db_client.find.call_args
    assert call_args[1]["collection"] == "profiles"
    assert call_args[1]["filter_query"]["user_id"] == "user_123"


@pytest.mark.asyncio
async def test_collect_collection_data_not_found(
    gdpr_service,
    mock_db_client
):
    """Test collecting from non-existent collection"""
    mock_db_client.find.side_effect = ZeroDBError("Collection not found")

    data = await gdpr_service._collect_collection_data(
        collection_name="nonexistent",
        user_id="user_123"
    )

    assert data == []


# ============================================================================
# FILTER QUERY TESTS
# ============================================================================

def test_build_filter_query_for_profiles(gdpr_service):
    """Test filter query for profiles collection"""
    query = gdpr_service._build_filter_query("profiles", "user_123")
    assert query == {"user_id": "user_123"}


def test_build_filter_query_for_applications(gdpr_service):
    """Test filter query for applications collection"""
    query = gdpr_service._build_filter_query("applications", "user_123")
    assert query == {"user_id": "user_123"}


def test_build_filter_query_for_payments(gdpr_service):
    """Test filter query for payments collection"""
    query = gdpr_service._build_filter_query("payments", "user_123")
    assert query == {"user_id": "user_123"}


def test_build_filter_query_for_audit_logs(gdpr_service):
    """Test filter query for audit logs collection"""
    query = gdpr_service._build_filter_query("audit_logs", "user_123")
    assert query == {"user_id": "user_123"}


def test_build_filter_query_default(gdpr_service):
    """Test filter query for unknown collection"""
    query = gdpr_service._build_filter_query("unknown_collection", "user_123")
    assert query == {"user_id": "user_123"}


# ============================================================================
# DATA CLEANING TESTS
# ============================================================================

def test_clean_sensitive_data_removes_internal_fields(gdpr_service):
    """Test that sensitive fields are removed"""
    records = [
        {
            "id": "1",
            "user_id": "user_123",
            "name": "John",
            "_id": "internal_id",
            "password_hash": "secret",
            "password": "secret",
            "salt": "secret"
        }
    ]

    cleaned = gdpr_service._clean_sensitive_data(records, "profiles")

    assert len(cleaned) == 1
    assert "_id" not in cleaned[0]
    assert "password_hash" not in cleaned[0]
    assert "password" not in cleaned[0]
    assert "salt" not in cleaned[0]
    assert "name" in cleaned[0]
    assert "user_id" in cleaned[0]


def test_clean_sensitive_data_redacts_card_numbers(gdpr_service):
    """Test that card numbers are redacted in payment data"""
    records = [
        {
            "id": "pay_1",
            "user_id": "user_123",
            "amount": 5000,
            "card_last4": "4242"
        }
    ]

    cleaned = gdpr_service._clean_sensitive_data(records, "payments")

    assert cleaned[0]["card_last4"] == "****4242"


def test_clean_sensitive_data_handles_empty_records(gdpr_service):
    """Test cleaning empty record list"""
    cleaned = gdpr_service._clean_sensitive_data([], "profiles")
    assert cleaned == []


def test_clean_sensitive_data_handles_none_values(gdpr_service):
    """Test cleaning with None values"""
    records = [
        {
            "id": "pay_1",
            "user_id": "user_123",
            "card_last4": None
        }
    ]

    cleaned = gdpr_service._clean_sensitive_data(records, "payments")
    assert cleaned[0]["card_last4"] is None


# ============================================================================
# COVER LETTER TESTS
# ============================================================================

def test_generate_cover_letter(gdpr_service):
    """Test cover letter generation"""
    export_date = datetime(2025, 1, 10, 12, 0, 0)
    expiry_date = datetime(2025, 1, 11, 12, 0, 0)

    cover_letter = gdpr_service._generate_cover_letter(
        user_email="test@example.com",
        export_date=export_date,
        expiry_date=expiry_date
    )

    assert "title" in cover_letter
    assert "introduction" in cover_letter
    assert "recipient" in cover_letter
    assert "GDPR" in cover_letter["introduction"]
    assert cover_letter["recipient"] == "test@example.com"
    assert "export_date" in cover_letter
    assert "expiry_date" in cover_letter


# ============================================================================
# STORAGE AND URL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_export_file(gdpr_service, mock_db_client):
    """Test storing export file in object storage"""
    expiry_date = datetime.utcnow() + timedelta(hours=24)
    content = '{"test": "data"}'

    result = await gdpr_service._store_export_file(
        object_key="test_key",
        content=content,
        expiry_date=expiry_date
    )

    assert mock_db_client.upload_object_from_bytes.called
    call_args = mock_db_client.upload_object_from_bytes.call_args
    assert call_args[1]["key"] == "test_key"
    assert call_args[1]["content_type"] == "application/json"


@pytest.mark.asyncio
async def test_store_export_file_failure(gdpr_service, mock_db_client):
    """Test handling of storage failure"""
    mock_db_client.upload_object_from_bytes.side_effect = Exception("Storage error")
    expiry_date = datetime.utcnow() + timedelta(hours=24)

    with pytest.raises(DataExportError) as exc_info:
        await gdpr_service._store_export_file(
            object_key="test_key",
            content='{"test": "data"}',
            expiry_date=expiry_date
        )

    assert "Failed to store export file" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_download_url(gdpr_service, mock_db_client):
    """Test generating signed download URL"""
    expiry_date = datetime.utcnow() + timedelta(hours=24)

    url = await gdpr_service._generate_download_url(
        object_key="test_key",
        expiry_date=expiry_date
    )

    assert url == "https://example.com/download/test"
    assert mock_db_client.generate_signed_url.called


@pytest.mark.asyncio
async def test_generate_download_url_fallback(gdpr_service, mock_db_client):
    """Test URL generation fallback on error"""
    mock_db_client.generate_signed_url.side_effect = Exception("URL generation failed")
    expiry_date = datetime.utcnow() + timedelta(hours=24)

    with patch('backend.config.settings') as mock_settings:
        mock_settings.ZERODB_API_BASE_URL = "https://api.example.com"

        url = await gdpr_service._generate_download_url(
            object_key="test_key",
            expiry_date=expiry_date
        )

        # Should return fallback URL
        assert "test_key" in url


# ============================================================================
# AUDIT LOG TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_log_export_request(gdpr_service, mock_db_client):
    """Test logging export request to audit logs"""
    await gdpr_service._log_export_request(
        user_id="user_123",
        export_id="export_456"
    )

    assert mock_db_client.insert_one.called
    call_args = mock_db_client.insert_one.call_args
    assert call_args[1]["collection"] == "audit_logs"

    document = call_args[1]["document"]
    assert document["user_id"] == "user_123"
    assert document["action"] == "gdpr_data_export"
    assert document["details"]["export_id"] == "export_456"


@pytest.mark.asyncio
async def test_log_export_request_handles_errors(gdpr_service, mock_db_client):
    """Test that logging errors don't fail the export"""
    mock_db_client.insert_one.side_effect = Exception("Logging failed")

    # Should not raise exception
    await gdpr_service._log_export_request(
        user_id="user_123",
        export_id="export_456"
    )


# ============================================================================
# EMAIL NOTIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_send_export_ready_email(gdpr_service, mock_email_service):
    """Test sending export ready email"""
    expiry_date = datetime(2025, 1, 11, 12, 0, 0)

    await gdpr_service._send_export_ready_email(
        user_email="test@example.com",
        download_url="https://example.com/download",
        expiry_date=expiry_date
    )

    assert mock_email_service._send_email.called
    call_args = mock_email_service._send_email.call_args

    assert call_args[1]["to_email"] == "test@example.com"
    assert call_args[1]["subject"] == "Your WWMAA Data Export is Ready"
    assert "https://example.com/download" in call_args[1]["html_body"]
    assert "January 11, 2025" in call_args[1]["html_body"]


@pytest.mark.asyncio
async def test_send_export_ready_email_handles_errors(gdpr_service, mock_email_service):
    """Test that email errors don't fail the export"""
    mock_email_service._send_email.side_effect = Exception("Email failed")
    expiry_date = datetime.utcnow() + timedelta(hours=24)

    # Should not raise exception
    await gdpr_service._send_export_ready_email(
        user_email="test@example.com",
        download_url="https://example.com/download",
        expiry_date=expiry_date
    )


# ============================================================================
# EXPORT STATUS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_export_status_found(gdpr_service, mock_db_client):
    """Test getting export status when export exists"""
    result = await gdpr_service.get_export_status(
        user_id="user_123",
        export_id="export_456"
    )

    assert result["status"] == "completed"
    assert "created_at" in result
    assert "expiry_date" in result
    assert "file_size_bytes" in result


@pytest.mark.asyncio
async def test_get_export_status_not_found(gdpr_service, mock_db_client):
    """Test getting export status when export doesn't exist"""
    mock_db_client.get_object_metadata.side_effect = Exception("Not found")

    result = await gdpr_service.get_export_status(
        user_id="user_123",
        export_id="export_456"
    )

    assert result["status"] == "not_found"


# ============================================================================
# EXPORT DELETION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_export_success(gdpr_service, mock_db_client):
    """Test successful export deletion"""
    result = await gdpr_service.delete_export(
        user_id="user_123",
        export_id="export_456"
    )

    assert result is True
    assert mock_db_client.delete_object_by_key.called
    call_args = mock_db_client.delete_object_by_key.call_args
    assert "export_456" in call_args[1]["key"]


@pytest.mark.asyncio
async def test_delete_export_failure(gdpr_service, mock_db_client):
    """Test export deletion failure"""
    mock_db_client.delete_object_by_key.side_effect = Exception("Delete failed")

    result = await gdpr_service.delete_export(
        user_id="user_123",
        export_id="export_456"
    )

    assert result is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_export_workflow(
    gdpr_service,
    mock_db_client,
    mock_email_service,
    sample_user_data,
    sample_profile_data,
    sample_application_data,
    sample_payment_data
):
    """Test complete export workflow end-to-end"""
    # Setup mock responses
    def mock_find_side_effect(collection, filter_query, limit):
        if collection == "profiles":
            return {"documents": sample_profile_data}
        elif collection == "applications":
            return {"documents": sample_application_data}
        elif collection == "payments":
            return {"documents": sample_payment_data}
        else:
            return {"documents": []}

    mock_db_client.find.side_effect = mock_find_side_effect

    # Execute export
    result = await gdpr_service.export_user_data(
        user_id=sample_user_data["user_id"],
        user_email=sample_user_data["email"]
    )

    # Verify complete workflow
    assert result["status"] == "completed"
    assert result["export_id"]
    assert result["download_url"]
    assert result["expiry_date"]

    # Verify all components were called
    assert mock_db_client.find.called  # Data collection
    assert mock_db_client.upload_object_from_bytes.called  # File storage
    assert mock_db_client.generate_signed_url.called  # URL generation
    assert mock_db_client.insert_one.called  # Audit logging
    assert mock_email_service._send_email.called  # Email notification

    # Verify export file content would be valid JSON
    upload_call_args = mock_db_client.upload_object_from_bytes.call_args
    content = upload_call_args[1]["content"].decode('utf-8')
    export_data = json.loads(content)

    assert "export_metadata" in export_data
    assert "cover_letter" in export_data
    assert "data" in export_data
    assert len(export_data["data"]) == len(GDPRService.COLLECTIONS)


@pytest.mark.asyncio
async def test_constants_are_correct(gdpr_service):
    """Test that service constants are properly defined"""
    assert GDPRService.EXPORT_EXPIRY_HOURS == 24
    assert isinstance(GDPRService.COLLECTIONS, dict)
    assert len(GDPRService.COLLECTIONS) == 8  # Verify all expected collections
    assert "profiles" in GDPRService.COLLECTIONS
    assert "applications" in GDPRService.COLLECTIONS
    assert "subscriptions" in GDPRService.COLLECTIONS
    assert "payments" in GDPRService.COLLECTIONS
    assert "rsvps" in GDPRService.COLLECTIONS
    assert "search_queries" in GDPRService.COLLECTIONS
    assert "attendees" in GDPRService.COLLECTIONS
    assert "audit_logs" in GDPRService.COLLECTIONS
