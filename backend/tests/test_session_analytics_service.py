"""
Tests for Session Analytics Service

Tests cover:
- Comprehensive analytics generation
- Attendance statistics calculation
- Engagement metrics tracking
- Peak concurrent viewers calculation
- VOD metrics integration
- Comparative analytics
- CSV export functionality
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
import io

from backend.services.session_analytics_service import (
    SessionAnalyticsService,
    SessionAnalyticsError,
    CloudflareAnalyticsError,
    get_session_analytics_service
)
from backend.services.zerodb_service import (
    ZeroDBNotFoundError,
    ZeroDBError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def analytics_service():
    """Create a SessionAnalyticsService instance for testing"""
    return SessionAnalyticsService()


@pytest.fixture
def mock_session():
    """Mock training session data"""
    return {
        "id": str(uuid4()),
        "title": "Advanced Karate Techniques",
        "instructor_id": str(uuid4()),
        "session_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "duration_minutes": 60,
        "session_status": "ended",
        "started_at": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
        "ended_at": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
        "cloudflare_video_id": "test-video-123"
    }


@pytest.fixture
def mock_attendance_records():
    """Mock attendance records"""
    base_time = datetime.utcnow() - timedelta(hours=25)

    return [
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "user_name": "Alice Smith",
            "user_email": "alice@example.com",
            "joined_at": base_time.isoformat(),
            "left_at": (base_time + timedelta(minutes=55)).isoformat(),
            "watched_vod": True,
            "vod_watch_time_minutes": 45,
            "vod_completion_percent": 75
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "user_name": "Bob Johnson",
            "user_email": "bob@example.com",
            "joined_at": (base_time + timedelta(minutes=10)).isoformat(),
            "left_at": (base_time + timedelta(minutes=60)).isoformat(),
            "watched_vod": False,
            "vod_watch_time_minutes": 0,
            "vod_completion_percent": 0
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "user_name": "Carol Davis",
            "user_email": "carol@example.com",
            "joined_at": None,  # Registered but didn't attend
            "left_at": None,
            "watched_vod": True,
            "vod_watch_time_minutes": 60,
            "vod_completion_percent": 100
        }
    ]


@pytest.fixture
def mock_chat_messages():
    """Mock chat messages"""
    return [
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "message": "Great technique!",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "message": "Can you explain the stance again?",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "message": "How do we practice this at home?",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def mock_reactions():
    """Mock reaction records"""
    return [
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "reaction_type": "👍",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "reaction_type": "👏",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "reaction_type": "👍",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def mock_feedback():
    """Mock feedback records"""
    return [
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "rating": 5,
            "comment": "Excellent session, very informative!",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "rating": 4,
            "comment": "Good content but could be more interactive",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]


# ============================================================================
# TEST: SERVICE INITIALIZATION
# ============================================================================

def test_service_initialization():
    """Test analytics service initializes correctly"""
    service = SessionAnalyticsService()

    assert service.db is not None
    assert service.sessions_collection == "training_sessions"
    assert service.attendance_collection == "session_attendance"
    assert service.chat_collection == "session_chat"
    assert service.feedback_collection == "session_feedback"
    assert service.reactions_collection == "session_reactions"


def test_get_service_singleton():
    """Test service singleton pattern"""
    service1 = get_session_analytics_service()
    service2 = get_session_analytics_service()

    assert service1 is service2


# ============================================================================
# TEST: ATTENDANCE STATISTICS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_attendance_stats_success(mock_db_client, analytics_service, mock_session, mock_attendance_records):
    """Test successful attendance statistics calculation"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.return_value = {
        "documents": mock_attendance_records,
        "total": len(mock_attendance_records)
    }

    # Reinitialize service with mocked db
    analytics_service.db = mock_db

    stats = analytics_service.get_attendance_stats("test-session-1")

    assert stats["total_registered"] == 3
    assert stats["total_attended"] == 2
    assert stats["attendance_rate"] == 66.67  # 2/3 * 100
    assert stats["on_time_arrivals"] >= 0
    assert stats["late_arrivals"] >= 0
    assert "average_duration_minutes" in stats


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_attendance_stats_no_attendees(mock_db_client, analytics_service, mock_session):
    """Test attendance stats with no attendees"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.return_value = {
        "documents": [],
        "total": 0
    }

    analytics_service.db = mock_db

    stats = analytics_service.get_attendance_stats("test-session-1")

    assert stats["total_registered"] == 0
    assert stats["total_attended"] == 0
    assert stats["attendance_rate"] == 0


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_attendance_stats_error(mock_db_client, analytics_service):
    """Test attendance stats handles errors"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.side_effect = Exception("Database error")

    analytics_service.db = mock_db

    with pytest.raises(SessionAnalyticsError):
        analytics_service.get_attendance_stats("test-session-1")


# ============================================================================
# TEST: ENGAGEMENT METRICS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_engagement_metrics_success(
    mock_db_client,
    analytics_service,
    mock_session,
    mock_chat_messages,
    mock_reactions,
    mock_attendance_records
):
    """Test successful engagement metrics calculation"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    # Mock different query responses
    def query_side_effect(collection, **kwargs):
        if collection == "session_chat":
            return {"documents": mock_chat_messages}
        elif collection == "session_reactions":
            return {"documents": mock_reactions}
        elif collection == "session_attendance":
            return {"documents": mock_attendance_records}
        return {"documents": []}

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.side_effect = query_side_effect

    analytics_service.db = mock_db

    metrics = analytics_service.get_engagement_metrics("test-session-1")

    assert metrics["chat_message_count"] == 3
    assert metrics["unique_chatters"] > 0
    assert metrics["questions_asked"] == 2  # Two messages end with '?'
    assert metrics["reaction_count"] == 3
    assert "👍" in metrics["reaction_breakdown"]
    assert "👏" in metrics["reaction_breakdown"]


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_engagement_metrics_no_activity(mock_db_client, analytics_service, mock_session, mock_attendance_records):
    """Test engagement metrics with no activity"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    def query_side_effect(collection, **kwargs):
        if collection == "session_attendance":
            return {"documents": mock_attendance_records}
        return {"documents": []}

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.side_effect = query_side_effect

    analytics_service.db = mock_db

    metrics = analytics_service.get_engagement_metrics("test-session-1")

    assert metrics["chat_message_count"] == 0
    assert metrics["unique_chatters"] == 0
    assert metrics["questions_asked"] == 0
    assert metrics["reaction_count"] == 0


# ============================================================================
# TEST: PEAK CONCURRENT VIEWERS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_peak_concurrent_viewers_success(mock_db_client, analytics_service, mock_attendance_records):
    """Test peak concurrent viewers calculation"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.query_documents.return_value = {
        "documents": mock_attendance_records[:2]  # Only attendees who joined
    }

    analytics_service.db = mock_db

    result = analytics_service.get_peak_concurrent_viewers("test-session-1")

    assert "peak_count" in result
    assert "peak_timestamp" in result
    assert "timeline" in result
    assert result["peak_count"] >= 0


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_peak_concurrent_viewers_no_attendees(mock_db_client, analytics_service):
    """Test peak concurrent viewers with no attendees"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.query_documents.return_value = {"documents": []}

    analytics_service.db = mock_db

    result = analytics_service.get_peak_concurrent_viewers("test-session-1")

    assert result["peak_count"] == 0
    assert result["peak_timestamp"] is None


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_peak_concurrent_viewers_timeline_sampling(mock_db_client, analytics_service):
    """Test timeline is sampled to max 100 points"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    # Create many attendance records to test sampling
    base_time = datetime.utcnow() - timedelta(hours=1)
    many_attendees = []

    for i in range(150):
        many_attendees.append({
            "id": str(uuid4()),
            "session_id": "test-session-1",
            "user_id": str(uuid4()),
            "joined_at": (base_time + timedelta(seconds=i*10)).isoformat(),
            "left_at": (base_time + timedelta(seconds=i*10 + 300)).isoformat()
        })

    mock_db.query_documents.return_value = {"documents": many_attendees}

    analytics_service.db = mock_db

    result = analytics_service.get_peak_concurrent_viewers("test-session-1")

    assert len(result["timeline"]) <= 100


# ============================================================================
# TEST: VOD METRICS
# ============================================================================

@patch('backend.services.session_analytics_service.requests.get')
def test_get_vod_metrics_success(mock_get, analytics_service):
    """Test successful VOD metrics retrieval from Cloudflare"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "totalViews": 50,
            "uniqueViewers": 35,
            "totalTimeViewedMinutes": 1200,
            "averageTimeViewedMinutes": 24,
            "completionRate": 0.75,
            "qualityDistribution": {"720p": 30, "1080p": 20},
            "countryViews": {"US": 40, "CA": 10},
            "deviceDistribution": {"desktop": 35, "mobile": 15},
            "viewershipTimeSeries": []
        }
    }
    mock_get.return_value = mock_response

    metrics = analytics_service.get_vod_metrics("test-session-1", "video-123")

    assert metrics["total_views"] == 50
    assert metrics["unique_viewers"] == 35
    assert metrics["completion_rate"] == 75.0
    assert "quality_distribution" in metrics


@patch('backend.services.session_analytics_service.requests.get')
def test_get_vod_metrics_api_failure(mock_get, analytics_service):
    """Test VOD metrics handles API failures gracefully"""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    metrics = analytics_service.get_vod_metrics("test-session-1", "video-123")

    # Should return mock data structure
    assert metrics["total_views"] == 0
    assert "note" in metrics


@patch('backend.services.session_analytics_service.requests.get')
def test_get_vod_metrics_missing_credentials(mock_get, analytics_service):
    """Test VOD metrics fails without credentials"""
    # Temporarily clear credentials
    analytics_service.cloudflare_account_id = None

    with pytest.raises(CloudflareAnalyticsError):
        analytics_service.get_vod_metrics("test-session-1", "video-123")


# ============================================================================
# TEST: COMPREHENSIVE ANALYTICS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_session_analytics_success(
    mock_db_client,
    analytics_service,
    mock_session,
    mock_attendance_records,
    mock_chat_messages,
    mock_reactions,
    mock_feedback
):
    """Test comprehensive analytics generation"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    def query_side_effect(collection, **kwargs):
        if collection == "session_chat":
            return {"documents": mock_chat_messages}
        elif collection == "session_reactions":
            return {"documents": mock_reactions}
        elif collection == "session_attendance":
            return {"documents": mock_attendance_records}
        elif collection == "session_feedback":
            return {"documents": mock_feedback}
        return {"documents": []}

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.side_effect = query_side_effect

    analytics_service.db = mock_db

    # Mock VOD metrics to avoid API call
    with patch.object(analytics_service, 'get_vod_metrics') as mock_vod:
        mock_vod.return_value = {"total_views": 50, "unique_viewers": 35}

        analytics = analytics_service.get_session_analytics("test-session-1")

        assert analytics["session_id"] == "test-session-1"
        assert "session_info" in analytics
        assert "attendance" in analytics
        assert "engagement" in analytics
        assert "peak_viewers" in analytics
        assert "vod" in analytics
        assert "feedback" in analytics
        assert "engagement_score" in analytics
        assert analytics["engagement_score"] >= 0
        assert analytics["engagement_score"] <= 100


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_session_analytics_session_not_found(mock_db_client, analytics_service):
    """Test analytics handles session not found"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.side_effect = ZeroDBNotFoundError("Session not found")

    analytics_service.db = mock_db

    with pytest.raises(ZeroDBNotFoundError):
        analytics_service.get_session_analytics("nonexistent-session")


# ============================================================================
# TEST: COMPARATIVE ANALYTICS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_get_comparative_analytics_success(mock_db_client, analytics_service):
    """Test comparative analytics across sessions"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    # Mock two sessions with analytics
    session1 = {
        "id": "session-1",
        "title": "Session 1",
        "session_date": datetime.utcnow().isoformat(),
        "session_status": "ended"
    }

    session2 = {
        "id": "session-2",
        "title": "Session 2",
        "session_date": datetime.utcnow().isoformat(),
        "session_status": "ended"
    }

    def get_doc_side_effect(collection, document_id):
        if document_id == "session-1":
            return session1
        elif document_id == "session-2":
            return session2
        raise ZeroDBNotFoundError("Not found")

    mock_db.get_document.side_effect = get_doc_side_effect
    mock_db.query_documents.return_value = {"documents": []}

    analytics_service.db = mock_db

    # Mock get_session_analytics to return test data
    with patch.object(analytics_service, 'get_session_analytics') as mock_analytics:
        mock_analytics.return_value = {
            "session_info": {"title": "Test", "session_date": datetime.utcnow().isoformat()},
            "attendance": {"attendance_rate": 75, "total_attended": 20},
            "engagement": {"chat_message_count": 50},
            "engagement_score": 85,
            "peak_viewers": {"peak_count": 18},
            "feedback": {"average_rating": 4.5}
        }

        comparison = analytics_service.get_comparative_analytics(["session-1", "session-2"])

        assert comparison["total_sessions"] == 2
        assert "sessions" in comparison
        assert "averages" in comparison
        assert "trends" in comparison
        assert len(comparison["sessions"]) == 2


def test_get_comparative_analytics_too_few_sessions(analytics_service):
    """Test comparative analytics requires at least 2 sessions"""
    with pytest.raises(SessionAnalyticsError, match="At least 2 sessions required"):
        analytics_service.get_comparative_analytics(["session-1"])


def test_get_comparative_analytics_too_many_sessions(analytics_service):
    """Test comparative analytics limits to 10 sessions"""
    session_ids = [f"session-{i}" for i in range(15)]

    with pytest.raises(SessionAnalyticsError, match="Maximum 10 sessions"):
        analytics_service.get_comparative_analytics(session_ids)


# ============================================================================
# TEST: CSV EXPORT
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_export_attendance_csv_success(
    mock_db_client,
    analytics_service,
    mock_session,
    mock_attendance_records
):
    """Test CSV export generation"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.return_value = {"documents": mock_attendance_records}

    analytics_service.db = mock_db

    csv_content = analytics_service.export_attendance_csv("test-session-1")

    assert isinstance(csv_content, str)
    assert len(csv_content) > 0
    assert "Session Name" in csv_content
    assert "Attendee Name" in csv_content
    assert "Email" in csv_content
    assert mock_session["title"] in csv_content


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_export_attendance_csv_utf8_bom(mock_db_client, analytics_service, mock_session):
    """Test CSV includes UTF-8 BOM for Excel compatibility"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.return_value = {"documents": []}

    analytics_service.db = mock_db

    csv_content = analytics_service.export_attendance_csv("test-session-1")

    # Check for UTF-8 BOM
    assert csv_content.startswith('\ufeff')


@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_export_attendance_csv_handles_special_characters(
    mock_db_client,
    analytics_service,
    mock_session
):
    """Test CSV properly escapes special characters"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    # Add attendee with special characters
    special_attendee = {
        "id": str(uuid4()),
        "session_id": "test-session-1",
        "user_id": str(uuid4()),
        "user_name": "O'Brien, John",
        "user_email": "john@example.com",
        "joined_at": datetime.utcnow().isoformat(),
        "left_at": datetime.utcnow().isoformat()
    }

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.return_value = {"documents": [special_attendee]}

    analytics_service.db = mock_db

    csv_content = analytics_service.export_attendance_csv("test-session-1")

    assert "O'Brien, John" in csv_content or '"O\'Brien, John"' in csv_content


# ============================================================================
# TEST: HELPER METHODS
# ============================================================================

def test_calculate_engagement_score(analytics_service):
    """Test engagement score calculation"""
    attendance = {
        "attendance_rate": 80,
        "total_registered": 20,
        "average_duration_minutes": 50
    }

    engagement = {
        "engagement_rate": 70,
        "chat_message_count": 25
    }

    peak_viewers = {
        "peak_count": 15
    }

    score = analytics_service._calculate_engagement_score(attendance, engagement, peak_viewers)

    assert 0 <= score <= 100
    assert isinstance(score, float)


def test_detect_trends(analytics_service):
    """Test trend detection"""
    comparisons = [
        {
            "session_date": "2025-01-01T10:00:00",
            "attendance_rate": 60,
            "engagement_score": 70,
            "average_rating": 4.0
        },
        {
            "session_date": "2025-01-08T10:00:00",
            "attendance_rate": 70,
            "engagement_score": 75,
            "average_rating": 4.2
        },
        {
            "session_date": "2025-01-15T10:00:00",
            "attendance_rate": 75,
            "engagement_score": 80,
            "average_rating": 4.5
        },
        {
            "session_date": "2025-01-22T10:00:00",
            "attendance_rate": 80,
            "engagement_score": 85,
            "average_rating": 4.8
        }
    ]

    trends = analytics_service._detect_trends(comparisons)

    assert "attendance_rate" in trends
    assert "engagement_score" in trends
    assert trends["attendance_rate"] in ["improving", "declining", "stable"]


def test_extract_feedback_themes(analytics_service):
    """Test feedback theme extraction"""
    comments = [
        "Great session with excellent demonstrations",
        "Excellent instructor, very clear explanations",
        "Great techniques shown today",
        "Clear and excellent teaching style"
    ]

    themes = analytics_service._extract_feedback_themes(comments)

    assert isinstance(themes, list)
    assert "excellent" in themes or "great" in themes


def test_parse_drop_off_points(analytics_service):
    """Test drop-off point detection"""
    timeseries = [
        {"timestamp": "2025-11-10T10:00:00", "viewers": 100},
        {"timestamp": "2025-11-10T10:10:00", "viewers": 95},
        {"timestamp": "2025-11-10T10:20:00", "viewers": 70},  # 26% drop
        {"timestamp": "2025-11-10T10:30:00", "viewers": 65},
        {"timestamp": "2025-11-10T10:40:00", "viewers": 40},  # 38% drop
    ]

    drop_offs = analytics_service._parse_drop_off_points(timeseries)

    assert isinstance(drop_offs, list)
    assert len(drop_offs) <= 5

    if drop_offs:
        assert "drop_percent" in drop_offs[0]
        assert drop_offs[0]["drop_percent"] > 20


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_analytics_handles_database_errors(mock_db_client, analytics_service):
    """Test analytics handles database errors gracefully"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    mock_db.get_document.side_effect = ZeroDBError("Database connection failed")

    analytics_service.db = mock_db

    with pytest.raises(SessionAnalyticsError):
        analytics_service.get_session_analytics("test-session-1")


def test_get_mock_vod_metrics(analytics_service):
    """Test mock VOD metrics structure"""
    mock_metrics = analytics_service._get_mock_vod_metrics()

    assert mock_metrics["total_views"] == 0
    assert mock_metrics["unique_viewers"] == 0
    assert "note" in mock_metrics
    assert mock_metrics["note"] == "VOD metrics unavailable"


# ============================================================================
# TEST: INTEGRATION SCENARIOS
# ============================================================================

@patch('backend.services.session_analytics_service.get_zerodb_client')
def test_full_analytics_workflow(
    mock_db_client,
    analytics_service,
    mock_session,
    mock_attendance_records,
    mock_chat_messages,
    mock_reactions,
    mock_feedback
):
    """Test complete analytics workflow from start to finish"""
    mock_db = Mock()
    mock_db_client.return_value = mock_db

    def query_side_effect(collection, **kwargs):
        if collection == "session_chat":
            return {"documents": mock_chat_messages}
        elif collection == "session_reactions":
            return {"documents": mock_reactions}
        elif collection == "session_attendance":
            return {"documents": mock_attendance_records}
        elif collection == "session_feedback":
            return {"documents": mock_feedback}
        return {"documents": []}

    mock_db.get_document.return_value = mock_session
    mock_db.query_documents.side_effect = query_side_effect

    analytics_service.db = mock_db

    # Get comprehensive analytics
    with patch.object(analytics_service, 'get_vod_metrics') as mock_vod:
        mock_vod.return_value = {"total_views": 50}

        analytics = analytics_service.get_session_analytics("test-session-1")

        # Verify all components present
        assert analytics is not None
        assert "session_info" in analytics
        assert "attendance" in analytics
        assert "engagement" in analytics

    # Get attendance stats
    attendance = analytics_service.get_attendance_stats("test-session-1")
    assert attendance["total_registered"] > 0

    # Get engagement metrics
    engagement = analytics_service.get_engagement_metrics("test-session-1")
    assert engagement["chat_message_count"] > 0

    # Get peak viewers
    peak = analytics_service.get_peak_concurrent_viewers("test-session-1")
    assert "peak_count" in peak

    # Export CSV
    csv_content = analytics_service.export_attendance_csv("test-session-1")
    assert len(csv_content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
