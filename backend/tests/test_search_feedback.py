"""
Test Suite for Search Feedback System - US-040

Tests for search query logging, feedback submission, and admin analytics.

Coverage areas:
- Search query logging
- Feedback submission (positive/negative)
- IP hashing for privacy
- Flagging negative feedback
- Admin feedback viewing endpoints
- Admin statistics endpoint
- CSV export
- Validation and error handling

Target: 80%+ code coverage
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.search_service import SearchService
from backend.services.zerodb_service import ZeroDBClient, ZeroDBError
from backend.models.schemas import SearchQuery


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_zerodb():
    """Mock ZeroDB client"""
    mock_db = AsyncMock(spec=ZeroDBClient)
    return mock_db


@pytest.fixture
def search_service(mock_zerodb):
    """Create SearchService with mocked database"""
    service = SearchService(mock_zerodb)
    # Set predictable salt for testing
    service.ip_salt = "test-salt-2024"
    return service


@pytest.fixture
def sample_query_id():
    """Sample query UUID"""
    return uuid4()


@pytest.fixture
def sample_query_data(sample_query_id):
    """Sample search query document"""
    return {
        "id": str(sample_query_id),
        "query_text": "martial arts classes near me",
        "user_id": None,
        "ip_hash": "abc123...",
        "results_count": 5,
        "response_time_ms": 150,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "feedback_rating": None,
        "feedback_text": None,
        "feedback_timestamp": None,
        "flagged_for_review": False
    }


@pytest.fixture
def sample_feedback_data(sample_query_id):
    """Sample query with feedback"""
    return {
        "id": str(sample_query_id),
        "query_text": "best karate dojo",
        "user_id": None,
        "ip_hash": "def456...",
        "results_count": 3,
        "response_time_ms": 120,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "feedback_rating": "positive",
        "feedback_text": "Great results!",
        "feedback_timestamp": datetime.utcnow(),
        "flagged_for_review": False
    }


# ============================================================================
# IP HASHING TESTS
# ============================================================================

class TestIPHashing:
    """Test IP address hashing for privacy"""

    def test_hash_ip_address(self, search_service):
        """Test IP hashing produces consistent SHA256 hash"""
        ip = "192.168.1.1"
        hash1 = search_service.hash_ip_address(ip)
        hash2 = search_service.hash_ip_address(ip)

        # Should be consistent
        assert hash1 == hash2

        # Should be 64 character hex string (SHA256)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_hash_ip_with_salt(self, search_service):
        """Test IP hashing uses salt properly"""
        ip = "192.168.1.1"
        expected = hashlib.sha256(f"{ip}test-salt-2024".encode()).hexdigest()

        result = search_service.hash_ip_address(ip)
        assert result == expected

    def test_hash_different_ips_produce_different_hashes(self, search_service):
        """Test different IPs produce different hashes"""
        hash1 = search_service.hash_ip_address("192.168.1.1")
        hash2 = search_service.hash_ip_address("192.168.1.2")

        assert hash1 != hash2

    def test_hash_empty_ip(self, search_service):
        """Test hashing empty IP returns empty string"""
        result = search_service.hash_ip_address("")
        assert result == ""

    def test_hash_none_ip(self, search_service):
        """Test hashing None IP returns empty string"""
        result = search_service.hash_ip_address(None)
        assert result == ""


# ============================================================================
# QUERY LOGGING TESTS
# ============================================================================

class TestQueryLogging:
    """Test search query logging"""

    @pytest.mark.asyncio
    async def test_log_query_basic(self, search_service, mock_zerodb):
        """Test logging a basic search query"""
        query_id = uuid4()
        mock_zerodb.create_document.return_value = {"id": str(query_id)}

        result = await search_service.log_query(
            query_text="martial arts",
            results_count=10,
            response_time_ms=100
        )

        assert result == query_id
        mock_zerodb.create_document.assert_called_once()

        # Verify query data structure
        call_args = mock_zerodb.create_document.call_args
        assert call_args[0][0] == "search_queries"
        query_data = call_args[0][1]
        assert query_data["query_text"] == "martial arts"
        assert query_data["results_count"] == 10
        assert query_data["response_time_ms"] == 100

    @pytest.mark.asyncio
    async def test_log_query_with_user(self, search_service, mock_zerodb):
        """Test logging query with authenticated user"""
        query_id = uuid4()
        user_id = uuid4()
        mock_zerodb.create_document.return_value = {"id": str(query_id)}

        await search_service.log_query(
            query_text="test query",
            user_id=user_id
        )

        call_args = mock_zerodb.create_document.call_args
        query_data = call_args[0][1]
        assert query_data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_log_query_hashes_ip(self, search_service, mock_zerodb):
        """Test IP address is hashed when logging query"""
        query_id = uuid4()
        mock_zerodb.create_document.return_value = {"id": str(query_id)}

        ip = "192.168.1.1"
        expected_hash = search_service.hash_ip_address(ip)

        await search_service.log_query(
            query_text="test",
            ip_address=ip
        )

        call_args = mock_zerodb.create_document.call_args
        query_data = call_args[0][1]
        assert query_data["ip_hash"] == expected_hash

    @pytest.mark.asyncio
    async def test_log_query_with_metadata(self, search_service, mock_zerodb):
        """Test logging query with full metadata"""
        query_id = uuid4()
        mock_zerodb.create_document.return_value = {"id": str(query_id)}

        await search_service.log_query(
            query_text="test query",
            user_agent="Mozilla/5.0",
            session_id="session123",
            intent="find_school"
        )

        call_args = mock_zerodb.create_document.call_args
        query_data = call_args[0][1]
        assert query_data["user_agent"] == "Mozilla/5.0"
        assert query_data["session_id"] == "session123"
        assert query_data["intent"] == "find_school"


# ============================================================================
# FEEDBACK SUBMISSION TESTS
# ============================================================================

class TestFeedbackSubmission:
    """Test search feedback submission"""

    @pytest.mark.asyncio
    async def test_submit_positive_feedback(self, search_service, mock_zerodb, sample_query_data):
        """Test submitting positive feedback"""
        query_id = UUID(sample_query_data["id"])

        # Mock get and update
        mock_zerodb.get_document.return_value = sample_query_data
        updated_data = {**sample_query_data, "feedback_rating": "positive", "flagged_for_review": False}
        mock_zerodb.update_document.return_value = updated_data

        result = await search_service.submit_feedback(
            query_id=query_id,
            rating="positive"
        )

        # Verify result
        assert result["feedback_rating"] == "positive"
        assert result["flagged_for_review"] == False

        # Verify update was called
        mock_zerodb.update_document.assert_called_once()
        update_args = mock_zerodb.update_document.call_args[0]
        assert update_args[1] == str(query_id)

        update_data = update_args[2]
        assert update_data["feedback_rating"] == "positive"
        assert update_data["flagged_for_review"] == False

    @pytest.mark.asyncio
    async def test_submit_negative_feedback_flags_for_review(
        self, search_service, mock_zerodb, sample_query_data
    ):
        """Test submitting negative feedback automatically flags for review"""
        query_id = UUID(sample_query_data["id"])

        mock_zerodb.get_document.return_value = sample_query_data
        updated_data = {
            **sample_query_data,
            "feedback_rating": "negative",
            "flagged_for_review": True
        }
        mock_zerodb.update_document.return_value = updated_data

        result = await search_service.submit_feedback(
            query_id=query_id,
            rating="negative"
        )

        # Verify flagged for review
        assert result["feedback_rating"] == "negative"
        assert result["flagged_for_review"] == True

        update_data = mock_zerodb.update_document.call_args[0][2]
        assert update_data["flagged_for_review"] == True

    @pytest.mark.asyncio
    async def test_submit_feedback_with_text(self, search_service, mock_zerodb, sample_query_data):
        """Test submitting feedback with text comment"""
        query_id = UUID(sample_query_data["id"])

        mock_zerodb.get_document.return_value = sample_query_data
        updated_data = {**sample_query_data, "feedback_text": "Great results!"}
        mock_zerodb.update_document.return_value = updated_data

        result = await search_service.submit_feedback(
            query_id=query_id,
            rating="positive",
            feedback_text="Great results!"
        )

        update_data = mock_zerodb.update_document.call_args[0][2]
        assert update_data["feedback_text"] == "Great results!"

    @pytest.mark.asyncio
    async def test_submit_feedback_query_not_found(self, search_service, mock_zerodb):
        """Test feedback submission fails if query not found"""
        query_id = uuid4()
        mock_zerodb.get_document.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await search_service.submit_feedback(
                query_id=query_id,
                rating="positive"
            )

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(self, search_service, mock_zerodb, sample_query_data):
        """Test feedback submission fails with invalid rating"""
        query_id = UUID(sample_query_data["id"])
        mock_zerodb.get_document.return_value = sample_query_data

        with pytest.raises(ValueError, match="must be 'positive' or 'negative'"):
            await search_service.submit_feedback(
                query_id=query_id,
                rating="neutral"
            )

    @pytest.mark.asyncio
    async def test_submit_feedback_already_submitted(self, search_service, mock_zerodb, sample_feedback_data):
        """Test cannot submit feedback twice for same query"""
        query_id = UUID(sample_feedback_data["id"])

        # Query already has feedback
        mock_zerodb.get_document.return_value = sample_feedback_data

        with pytest.raises(ValueError, match="already submitted"):
            await search_service.submit_feedback(
                query_id=query_id,
                rating="positive"
            )

    @pytest.mark.asyncio
    async def test_submit_feedback_hashes_ip(self, search_service, mock_zerodb, sample_query_data):
        """Test IP is hashed when submitting feedback"""
        query_id = UUID(sample_query_data["id"])

        # Query without IP hash
        query_without_ip = {**sample_query_data, "ip_hash": None}
        mock_zerodb.get_document.return_value = query_without_ip
        mock_zerodb.update_document.return_value = query_without_ip

        ip = "192.168.1.1"
        expected_hash = search_service.hash_ip_address(ip)

        await search_service.submit_feedback(
            query_id=query_id,
            rating="positive",
            ip_address=ip
        )

        update_data = mock_zerodb.update_document.call_args[0][2]
        assert update_data["ip_hash"] == expected_hash


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestFeedbackStatistics:
    """Test feedback statistics calculation"""

    @pytest.mark.asyncio
    async def test_get_feedback_statistics(self, search_service, mock_zerodb):
        """Test calculating feedback statistics"""
        # Mock query results
        mock_queries = [
            {"id": str(uuid4()), "feedback_rating": "positive", "feedback_text": "Good"},
            {"id": str(uuid4()), "feedback_rating": "positive", "feedback_text": None},
            {"id": str(uuid4()), "feedback_rating": "negative", "feedback_text": "Bad", "flagged_for_review": True},
            {"id": str(uuid4()), "feedback_rating": None},  # No feedback
            {"id": str(uuid4()), "feedback_rating": None},  # No feedback
        ]
        mock_zerodb.query_documents.return_value = mock_queries

        stats = await search_service.get_feedback_statistics()

        assert stats["total_queries"] == 5
        assert stats["queries_with_feedback"] == 3
        assert stats["positive_count"] == 2
        assert stats["negative_count"] == 1
        assert stats["feedback_rate"] == 60.0  # 3/5 * 100
        assert stats["satisfaction_rate"] == 66.67  # 2/3 * 100 (rounded)
        assert stats["flagged_count"] == 1
        assert stats["with_text_count"] == 2

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, search_service, mock_zerodb):
        """Test statistics with no queries"""
        mock_zerodb.query_documents.return_value = []

        stats = await search_service.get_feedback_statistics()

        assert stats["total_queries"] == 0
        assert stats["feedback_rate"] == 0
        assert stats["satisfaction_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_date_range(self, search_service, mock_zerodb):
        """Test statistics with date filtering"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        mock_zerodb.query_documents.return_value = []

        await search_service.get_feedback_statistics(
            start_date=start_date,
            end_date=end_date
        )

        # Verify date filters were passed
        call_args = mock_zerodb.query_documents.call_args[0]
        filters = call_args[1]
        assert "created_at" in filters


# ============================================================================
# ADMIN QUERY TESTS
# ============================================================================

class TestAdminQueries:
    """Test admin feedback query endpoints"""

    @pytest.mark.asyncio
    async def test_get_flagged_feedback(self, search_service, mock_zerodb):
        """Test getting flagged feedback"""
        flagged_queries = [
            {
                "id": str(uuid4()),
                "feedback_rating": "negative",
                "flagged_for_review": True,
                "feedback_timestamp": datetime.utcnow()
            },
            {
                "id": str(uuid4()),
                "feedback_rating": "negative",
                "flagged_for_review": True,
                "feedback_timestamp": datetime.utcnow()
            }
        ]
        mock_zerodb.query_documents.return_value = flagged_queries

        result = await search_service.get_flagged_feedback()

        assert len(result) == 2
        assert all(q["flagged_for_review"] for q in result)

    @pytest.mark.asyncio
    async def test_get_flagged_feedback_with_pagination(self, search_service, mock_zerodb):
        """Test flagged feedback pagination"""
        mock_zerodb.query_documents.return_value = []

        await search_service.get_flagged_feedback(limit=25, offset=50)

        # Verify pagination params
        call_args = mock_zerodb.query_documents.call_args
        assert call_args[1]["limit"] == 25
        assert call_args[1]["offset"] == 50

    @pytest.mark.asyncio
    async def test_get_all_feedback(self, search_service, mock_zerodb):
        """Test getting all feedback with filters"""
        mock_queries = [
            {"id": str(uuid4()), "feedback_rating": "positive"},
            {"id": str(uuid4()), "feedback_rating": "positive"}
        ]
        mock_zerodb.query_documents.return_value = mock_queries

        result = await search_service.get_all_feedback(rating="positive")

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["limit"] == 50
        assert result["offset"] == 0

    @pytest.mark.asyncio
    async def test_get_all_feedback_with_text_filter(self, search_service, mock_zerodb):
        """Test filtering for feedback with text"""
        mock_zerodb.query_documents.return_value = []

        await search_service.get_all_feedback(has_text=True)

        call_args = mock_zerodb.query_documents.call_args[0]
        filters = call_args[1]
        assert "feedback_text" in filters

    @pytest.mark.asyncio
    async def test_unflag_feedback(self, search_service, mock_zerodb):
        """Test unflagging feedback"""
        query_id = uuid4()
        updated_query = {
            "id": str(query_id),
            "flagged_for_review": False
        }
        mock_zerodb.update_document.return_value = updated_query

        result = await search_service.unflag_feedback(query_id)

        assert result["flagged_for_review"] == False
        mock_zerodb.update_document.assert_called_once()


# ============================================================================
# INTEGRATION TESTS (Routes)
# ============================================================================

class TestSearchFeedbackRoutes:
    """Test search feedback API routes"""

    @pytest.mark.asyncio
    async def test_submit_feedback_endpoint(self, client, sample_query_data):
        """Test POST /api/search/feedback endpoint"""
        # This would require a test client setup
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_admin_get_feedback_endpoint(self, client):
        """Test GET /api/admin/search/feedback endpoint"""
        # This would require admin auth setup
        # Placeholder for integration test
        pass


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_submit_feedback_db_error(self, search_service, mock_zerodb, sample_query_data):
        """Test feedback submission handles database errors"""
        query_id = UUID(sample_query_data["id"])
        mock_zerodb.get_document.return_value = sample_query_data
        mock_zerodb.update_document.side_effect = ZeroDBError("Database error")

        with pytest.raises(ZeroDBError):
            await search_service.submit_feedback(
                query_id=query_id,
                rating="positive"
            )

    @pytest.mark.asyncio
    async def test_log_query_db_error(self, search_service, mock_zerodb):
        """Test query logging handles database errors"""
        mock_zerodb.create_document.side_effect = ZeroDBError("Database error")

        with pytest.raises(ZeroDBError):
            await search_service.log_query(query_text="test")


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Test input validation"""

    @pytest.mark.asyncio
    async def test_rating_validation(self, search_service, mock_zerodb, sample_query_data):
        """Test rating must be positive or negative"""
        query_id = UUID(sample_query_data["id"])
        mock_zerodb.get_document.return_value = sample_query_data

        invalid_ratings = ["good", "bad", "neutral", "", "YES", "NO"]

        for invalid_rating in invalid_ratings:
            with pytest.raises(ValueError):
                await search_service.submit_feedback(
                    query_id=query_id,
                    rating=invalid_rating
                )

    @pytest.mark.asyncio
    async def test_feedback_text_max_length(self, search_service, mock_zerodb, sample_query_data):
        """Test feedback text respects max length"""
        query_id = UUID(sample_query_data["id"])
        mock_zerodb.get_document.return_value = sample_query_data

        # Should not raise error - handled by Pydantic in routes
        long_text = "x" * 2001  # Over 2000 char limit

        # The service itself doesn't validate length, that's done in routes/Pydantic
        # But we can verify it gets passed through
        mock_zerodb.update_document.return_value = sample_query_data

        await search_service.submit_feedback(
            query_id=query_id,
            rating="positive",
            feedback_text=long_text
        )

        # Text should be passed as-is
        update_data = mock_zerodb.update_document.call_args[0][2]
        assert update_data["feedback_text"] == long_text


# ============================================================================
# PRIVACY TESTS
# ============================================================================

class TestPrivacy:
    """Test privacy features"""

    def test_ip_hash_not_reversible(self, search_service):
        """Test IP hash cannot be reversed to original IP"""
        ip = "192.168.1.1"
        hashed = search_service.hash_ip_address(ip)

        # Hash should not contain original IP
        assert ip not in hashed

        # Should be one-way hash
        assert len(hashed) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_no_pii_in_feedback(self, search_service, mock_zerodb, sample_query_data):
        """Test feedback doesn't store PII"""
        query_id = UUID(sample_query_data["id"])
        mock_zerodb.get_document.return_value = sample_query_data
        mock_zerodb.update_document.return_value = sample_query_data

        await search_service.submit_feedback(
            query_id=query_id,
            rating="positive",
            ip_address="192.168.1.1"
        )

        # Verify no raw IP stored
        update_data = mock_zerodb.update_document.call_args[0][2]
        assert "192.168.1.1" not in str(update_data)
        assert "ip_address" not in update_data or update_data.get("ip_address") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.services.search_service", "--cov-report=term-missing"])
