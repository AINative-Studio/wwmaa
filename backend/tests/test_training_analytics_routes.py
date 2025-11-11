"""
Tests for Training Analytics Admin Routes

Tests cover:
- Analytics endpoint authorization
- Comprehensive analytics retrieval
- Attendance statistics
- CSV export functionality
- Comparative analytics
- Instructor overview
- Engagement metrics
- Peak viewers
- Error handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes.admin import training_analytics
from backend.models.schemas import UserRole


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create test client"""
    app = FastAPI()
    app.include_router(training_analytics.router)
    return TestClient(app)


@pytest.fixture
def mock_instructor_user():
    """Mock instructor user"""
    return {
        "id": str(uuid4()),
        "email": "instructor@example.com",
        "role": UserRole.INSTRUCTOR.value,
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return {
        "id": str(uuid4()),
        "email": "admin@example.com",
        "role": UserRole.ADMIN.value,
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def mock_member_user():
    """Mock member user (insufficient permissions)"""
    return {
        "id": str(uuid4()),
        "email": "member@example.com",
        "role": UserRole.MEMBER.value,
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def mock_session():
    """Mock training session"""
    instructor_id = str(uuid4())
    return {
        "id": str(uuid4()),
        "title": "Advanced Karate Techniques",
        "instructor_id": instructor_id,
        "session_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "duration_minutes": 60,
        "session_status": "ended",
        "started_at": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
        "ended_at": (datetime.utcnow() - timedelta(hours=24)).isoformat()
    }


@pytest.fixture
def mock_analytics():
    """Mock comprehensive analytics data"""
    return {
        "session_id": "test-session-1",
        "session_info": {
            "title": "Advanced Karate Techniques",
            "instructor_id": str(uuid4()),
            "session_date": datetime.utcnow().isoformat(),
            "duration_minutes": 60,
            "session_status": "ended"
        },
        "attendance": {
            "total_registered": 25,
            "total_attended": 20,
            "attendance_rate": 80.0,
            "on_time_arrivals": 18,
            "late_arrivals": 2,
            "average_duration_minutes": 55.5
        },
        "engagement": {
            "chat_message_count": 45,
            "unique_chatters": 15,
            "questions_asked": 8,
            "reaction_count": 30,
            "reaction_breakdown": {"👍": 15, "👏": 10, "❤️": 5},
            "engagement_rate": 75.0
        },
        "peak_viewers": {
            "peak_count": 18,
            "peak_timestamp": datetime.utcnow().isoformat(),
            "timeline": []
        },
        "vod": {
            "total_views": 50,
            "unique_viewers": 35,
            "total_watch_time_minutes": 1200,
            "average_watch_time_minutes": 24,
            "completion_rate": 75.0
        },
        "feedback": {
            "total_responses": 15,
            "average_rating": 4.5,
            "rating_distribution": {5: 10, 4: 3, 3: 2}
        },
        "engagement_score": 82.5,
        "generated_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# TEST: GET SESSION ANALYTICS
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_analytics_success_as_instructor(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session,
    mock_analytics
):
    """Test instructor can get analytics for their own session"""
    # Set up mocks
    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_session_analytics.return_value = mock_analytics
    mock_analytics_service.return_value = mock_analytics_svc

    # Make request
    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/analytics")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == mock_analytics["session_id"]
    assert "attendance" in data
    assert "engagement" in data


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_analytics_success_as_admin(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_admin_user,
    mock_session,
    mock_analytics
):
    """Test admin can get analytics for any session"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_admin_user["id"]
    mock_user_obj.role = mock_admin_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_session_analytics.return_value = mock_analytics
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/analytics")

    assert response.status_code == 200


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_analytics_forbidden_for_other_instructor(
    mock_session_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test instructor cannot get analytics for another instructor's session"""
    # Different instructor
    mock_session["instructor_id"] = str(uuid4())

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/analytics")

    assert response.status_code == 403


@patch('backend.routes.admin.training_analytics.get_current_user')
def test_get_session_analytics_forbidden_for_member(mock_get_user, client, mock_member_user):
    """Test member cannot access analytics"""
    mock_user_obj = Mock()
    mock_user_obj.role = mock_member_user["role"]
    mock_get_user.return_value = mock_user_obj

    response = client.get("/api/admin/training/sessions/test-session-1/analytics")

    assert response.status_code == 403


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_analytics_session_not_found(
    mock_session_service,
    mock_get_user,
    client,
    mock_admin_user
):
    """Test 404 when session doesn't exist"""
    from backend.services.zerodb_service import ZeroDBNotFoundError

    mock_user_obj = Mock()
    mock_user_obj.id = mock_admin_user["id"]
    mock_user_obj.role = mock_admin_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.side_effect = ZeroDBNotFoundError("Not found")
    mock_session_service.return_value = mock_session_svc

    response = client.get("/api/admin/training/sessions/nonexistent/analytics")

    assert response.status_code == 404


# ============================================================================
# TEST: GET ATTENDANCE
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_attendance_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test getting attendance statistics"""
    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_attendance_stats.return_value = {
        "total_registered": 25,
        "total_attended": 20,
        "attendance_rate": 80.0
    }
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/attendance")

    assert response.status_code == 200
    data = response.json()
    assert "attendance" in data
    assert data["attendance"]["total_registered"] == 25


# ============================================================================
# TEST: EXPORT ATTENDANCE CSV
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_export_attendance_csv_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test CSV export"""
    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    csv_content = "Session Name,Attendee Name,Email\nTest Session,John Doe,john@example.com"

    mock_analytics_svc = Mock()
    mock_analytics_svc.export_attendance_csv.return_value = csv_content
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/attendance/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert csv_content in response.text


# ============================================================================
# TEST: COMPARE SESSIONS
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_compare_sessions_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user
):
    """Test comparing multiple sessions"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    session1 = {"id": "session-1", "instructor_id": mock_instructor_user["id"]}
    session2 = {"id": "session-2", "instructor_id": mock_instructor_user["id"]}

    def get_session_side_effect(session_id):
        if session_id == "session-1":
            return session1
        elif session_id == "session-2":
            return session2
        raise Exception("Not found")

    mock_session_svc = Mock()
    mock_session_svc.get_session.side_effect = get_session_side_effect
    mock_session_service.return_value = mock_session_svc

    comparison_data = {
        "sessions": [
            {
                "session_id": "session-1",
                "title": "Session 1",
                "attendance_rate": 75,
                "engagement_score": 80
            },
            {
                "session_id": "session-2",
                "title": "Session 2",
                "attendance_rate": 80,
                "engagement_score": 85
            }
        ],
        "averages": {
            "attendance_rate": 77.5,
            "engagement_score": 82.5
        },
        "trends": {
            "attendance_rate": "improving",
            "engagement_score": "improving"
        }
    }

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_comparative_analytics.return_value = comparison_data
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.post(
        "/api/admin/training/sessions/compare",
        json={"session_ids": ["session-1", "session-2"]}
    )

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "averages" in data
    assert "trends" in data


@patch('backend.routes.admin.training_analytics.get_current_user')
def test_compare_sessions_too_few_sessions(mock_get_user, client, mock_instructor_user):
    """Test comparison requires at least 2 sessions"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    response = client.post(
        "/api/admin/training/sessions/compare",
        json={"session_ids": ["session-1"]}
    )

    assert response.status_code == 422  # Validation error


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_compare_sessions_forbidden_for_others_sessions(
    mock_session_service,
    mock_get_user,
    client,
    mock_instructor_user
):
    """Test instructor cannot compare sessions they don't own"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    # Session belongs to different instructor
    session1 = {"id": "session-1", "instructor_id": str(uuid4())}

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = session1
    mock_session_service.return_value = mock_session_svc

    response = client.post(
        "/api/admin/training/sessions/compare",
        json={"session_ids": ["session-1", "session-2"]}
    )

    assert response.status_code == 403


# ============================================================================
# TEST: INSTRUCTOR OVERVIEW
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_instructor_overview_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user
):
    """Test getting instructor analytics overview"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    sessions = [
        {"id": "session-1", "title": "Session 1", "session_date": datetime.utcnow().isoformat()},
        {"id": "session-2", "title": "Session 2", "session_date": datetime.utcnow().isoformat()}
    ]

    mock_session_svc = Mock()
    mock_session_svc.list_sessions.return_value = {"documents": sessions, "total": 2}
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_session_analytics.return_value = {
        "attendance": {"attendance_rate": 80, "total_attended": 20},
        "engagement_score": 85,
        "feedback": {"average_rating": 4.5}
    }
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get("/api/admin/training/analytics/overview")

    assert response.status_code == 200
    data = response.json()
    assert "instructor_id" in data
    assert "total_sessions" in data
    assert "average_attendance_rate" in data
    assert "recent_sessions" in data


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_instructor_overview_admin_can_view_others(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_admin_user
):
    """Test admin can view any instructor's overview"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_admin_user["id"]
    mock_user_obj.role = mock_admin_user["role"]
    mock_get_user.return_value = mock_user_obj

    target_instructor_id = str(uuid4())

    mock_session_svc = Mock()
    mock_session_svc.list_sessions.return_value = {"documents": [], "total": 0}
    mock_session_service.return_value = mock_session_svc

    response = client.get(f"/api/admin/training/analytics/overview?instructor_id={target_instructor_id}")

    assert response.status_code == 200


@patch('backend.routes.admin.training_analytics.get_current_user')
def test_get_instructor_overview_instructor_cannot_view_others(
    mock_get_user,
    client,
    mock_instructor_user
):
    """Test instructor cannot view another instructor's overview"""
    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    other_instructor_id = str(uuid4())

    response = client.get(f"/api/admin/training/analytics/overview?instructor_id={other_instructor_id}")

    assert response.status_code == 403


# ============================================================================
# TEST: GET ENGAGEMENT METRICS
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_engagement_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test getting engagement metrics"""
    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    engagement_data = {
        "chat_message_count": 45,
        "unique_chatters": 15,
        "questions_asked": 8,
        "reaction_count": 30,
        "engagement_rate": 75.0
    }

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_engagement_metrics.return_value = engagement_data
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/engagement")

    assert response.status_code == 200
    data = response.json()
    assert "engagement" in data
    assert data["engagement"]["chat_message_count"] == 45


# ============================================================================
# TEST: GET PEAK VIEWERS
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_get_session_peak_viewers_success(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test getting peak concurrent viewers"""
    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    peak_data = {
        "peak_count": 18,
        "peak_timestamp": datetime.utcnow().isoformat(),
        "timeline": []
    }

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_peak_concurrent_viewers.return_value = peak_data
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/peak-viewers")

    assert response.status_code == 200
    data = response.json()
    assert "peak_viewers" in data
    assert data["peak_viewers"]["peak_count"] == 18


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_analytics_handles_service_errors(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_admin_user,
    mock_session
):
    """Test API handles analytics service errors"""
    from backend.services.session_analytics_service import SessionAnalyticsError

    mock_user_obj = Mock()
    mock_user_obj.id = mock_admin_user["id"]
    mock_user_obj.role = mock_admin_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.get_session_analytics.side_effect = SessionAnalyticsError("Analytics failed")
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/analytics")

    assert response.status_code == 500


@patch('backend.routes.admin.training_analytics.get_current_user')
@patch('backend.routes.admin.training_analytics.get_session_analytics_service')
@patch('backend.routes.admin.training_analytics.get_training_session_service')
def test_csv_export_handles_errors(
    mock_session_service,
    mock_analytics_service,
    mock_get_user,
    client,
    mock_instructor_user,
    mock_session
):
    """Test CSV export handles service errors"""
    from backend.services.session_analytics_service import SessionAnalyticsError

    mock_session["instructor_id"] = mock_instructor_user["id"]

    mock_user_obj = Mock()
    mock_user_obj.id = mock_instructor_user["id"]
    mock_user_obj.role = mock_instructor_user["role"]
    mock_get_user.return_value = mock_user_obj

    mock_session_svc = Mock()
    mock_session_svc.get_session.return_value = mock_session
    mock_session_service.return_value = mock_session_svc

    mock_analytics_svc = Mock()
    mock_analytics_svc.export_attendance_csv.side_effect = SessionAnalyticsError("Export failed")
    mock_analytics_service.return_value = mock_analytics_svc

    response = client.get(f"/api/admin/training/sessions/{mock_session['id']}/attendance/export")

    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
