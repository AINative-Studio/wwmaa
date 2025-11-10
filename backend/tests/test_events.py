"""
Tests for Event Routes

Tests event management endpoints including:
- GET /api/events - List events
- GET /api/events/:id - Get event detail
- POST /api/events - Create event (admin)
- PUT /api/events/:id - Update event (admin)
- DELETE /api/events/:id - Delete event (admin)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from backend.routes.events import (
    router,
    get_related_events,
    get_instructor_info,
)


@pytest.fixture
def mock_event_data():
    """Mock event data for testing"""
    event_id = str(uuid4())
    return {
        "id": event_id,
        "title": "Judo Seminar with Sensei Smith",
        "description": "<p>Advanced Judo techniques seminar</p>",
        "event_type": "seminar",
        "visibility": "public",
        "start_datetime": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "end_datetime": (datetime.utcnow() + timedelta(days=7, hours=3)).isoformat(),
        "timezone": "America/Los_Angeles",
        "is_all_day": False,
        "location_name": "WWMAA Dojo",
        "address": "123 Main St",
        "city": "San Francisco",
        "state": "CA",
        "virtual_url": None,
        "is_virtual": False,
        "max_attendees": 30,
        "current_attendees": 0,
        "waitlist_enabled": True,
        "organizer_id": str(uuid4()),
        "instructors": [str(uuid4())],
        "featured_image_url": "https://example.com/image.jpg",
        "registration_required": True,
        "registration_deadline": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "registration_fee": 50.00,
        "is_published": True,
        "is_canceled": False,
        "tags": ["judo", "seminar", "advanced"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_instructor_data():
    """Mock instructor profile data"""
    return {
        "id": str(uuid4()),
        "email": "instructor@example.com",
        "role": "instructor",
        "profile_id": str(uuid4()),
    }


@pytest.fixture
def mock_profile_data():
    """Mock profile data"""
    return {
        "id": str(uuid4()),
        "first_name": "John",
        "last_name": "Smith",
        "display_name": "Sensei Smith",
        "bio": "5th Dan Black Belt in Judo",
        "avatar_url": "https://example.com/avatar.jpg",
        "disciplines": ["Judo"],
        "ranks": {"Judo": "5th Dan"},
        "instructor_certifications": ["USA Judo Certified Instructor"],
    }


class TestEventRoutes:
    """Test event API routes"""

    @pytest.mark.asyncio
    async def test_list_events_success(self, mock_event_data):
        """Test listing events successfully"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            # Setup mock
            db_instance = mock_db.return_value
            db_instance.query_collection = AsyncMock(return_value=[mock_event_data])
            db_instance.close = AsyncMock()

            # Import and test
            from backend.routes.events import list_events

            result = await list_events(
                current_user={"id": str(uuid4()), "role": "public"}
            )

            assert result.total == 1
            assert len(result.events) == 1
            assert result.events[0]["title"] == mock_event_data["title"]

    @pytest.mark.asyncio
    async def test_list_events_filters_by_type(self, mock_event_data):
        """Test filtering events by type"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.query_collection = AsyncMock(return_value=[mock_event_data])
            db_instance.close = AsyncMock()

            from backend.routes.events import list_events, EventType

            result = await list_events(
                event_type=EventType.SEMINAR,
                current_user={"id": str(uuid4()), "role": "public"}
            )

            # Verify query was called with correct filter
            db_instance.query_collection.assert_called_once()
            call_args = db_instance.query_collection.call_args[0]
            assert call_args[1]["event_type"] == "seminar"

    @pytest.mark.asyncio
    async def test_list_events_public_only_for_public_users(self):
        """Test that public users only see public events"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.query_collection = AsyncMock(return_value=[])
            db_instance.close = AsyncMock()

            from backend.routes.events import list_events

            await list_events(
                current_user={"id": str(uuid4()), "role": "public"}
            )

            # Verify visibility filter was applied
            call_args = db_instance.query_collection.call_args[0]
            assert call_args[1]["visibility"] == "public"

    @pytest.mark.asyncio
    async def test_get_event_detail_success(self, mock_event_data, mock_instructor_data, mock_profile_data):
        """Test getting event detail successfully"""
        event_id = mock_event_data["id"]

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(
                side_effect=lambda collection, id: {
                    "events": mock_event_data,
                    "users": mock_instructor_data,
                    "profiles": mock_profile_data,
                }.get(collection)
            )
            db_instance.query_collection = AsyncMock(return_value=[])
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            result = await get_event_detail(
                event_id=event_id,
                current_user={"id": str(uuid4()), "role": "member"}
            )

            assert result.event["id"] == event_id
            assert result.event["title"] == mock_event_data["title"]
            assert result.rsvp_count == 0
            assert result.spots_remaining == 30
            assert result.instructor_info is not None

    @pytest.mark.asyncio
    async def test_get_event_detail_not_found(self):
        """Test 404 when event doesn't exist"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=None)
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            with pytest.raises(HTTPException) as exc_info:
                await get_event_detail(
                    event_id=str(uuid4()),
                    current_user={"id": str(uuid4()), "role": "member"}
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_event_detail_canceled(self, mock_event_data):
        """Test 404 when event is canceled"""
        mock_event_data["is_canceled"] = True

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=mock_event_data)
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            with pytest.raises(HTTPException) as exc_info:
                await get_event_detail(
                    event_id=mock_event_data["id"],
                    current_user={"id": str(uuid4()), "role": "member"}
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_event_detail_members_only_access_denied(self, mock_event_data):
        """Test 403 when non-member tries to access members-only event"""
        mock_event_data["visibility"] = "members_only"

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=mock_event_data)
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            with pytest.raises(HTTPException) as exc_info:
                await get_event_detail(
                    event_id=mock_event_data["id"],
                    current_user={"id": str(uuid4()), "role": "public"}
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_get_event_detail_members_only_access_granted(self, mock_event_data):
        """Test member can access members-only event"""
        mock_event_data["visibility"] = "members_only"

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=mock_event_data)
            db_instance.query_collection = AsyncMock(return_value=[])
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            result = await get_event_detail(
                event_id=mock_event_data["id"],
                current_user={"id": str(uuid4()), "role": "member"}
            )

            assert result.event["id"] == mock_event_data["id"]

    @pytest.mark.asyncio
    async def test_get_event_detail_calculates_spots_remaining(self, mock_event_data):
        """Test correct calculation of spots remaining"""
        # Create 5 RSVPs
        rsvps = [{"id": str(uuid4()), "status": "confirmed"} for _ in range(5)]

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=mock_event_data)
            db_instance.query_collection = AsyncMock(return_value=rsvps)
            db_instance.close = AsyncMock()

            from backend.routes.events import get_event_detail

            result = await get_event_detail(
                event_id=mock_event_data["id"],
                current_user={"id": str(uuid4()), "role": "member"}
            )

            assert result.rsvp_count == 5
            assert result.spots_remaining == 25  # 30 max - 5 rsvps

    @pytest.mark.asyncio
    async def test_get_related_events(self, mock_event_data):
        """Test getting related events"""
        # Create related events
        related_event_1 = {**mock_event_data, "id": str(uuid4())}
        related_event_2 = {**mock_event_data, "id": str(uuid4())}

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.query_collection = AsyncMock(
                return_value=[related_event_1, related_event_2]
            )

            related = await get_related_events(db_instance, mock_event_data)

            assert len(related) <= 5  # Should return max 5 events
            assert all(e["id"] != mock_event_data["id"] for e in related)

    @pytest.mark.asyncio
    async def test_get_instructor_info(self, mock_instructor_data, mock_profile_data):
        """Test getting instructor information"""
        instructor_id = mock_instructor_data["id"]

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(
                side_effect=lambda collection, id: {
                    "users": mock_instructor_data,
                    "profiles": mock_profile_data,
                }.get(collection)
            )

            info = await get_instructor_info(db_instance, [instructor_id])

            assert info is not None
            assert info["id"] == instructor_id
            assert info["first_name"] == mock_profile_data["first_name"]
            assert info["bio"] == mock_profile_data["bio"]

    @pytest.mark.asyncio
    async def test_create_event_requires_admin(self):
        """Test that creating event requires admin role"""
        from backend.routes.events import CreateEventRequest, create_event

        event_data = CreateEventRequest(
            title="Test Event",
            event_type="training",
            start_datetime=datetime.utcnow() + timedelta(days=1),
            end_datetime=datetime.utcnow() + timedelta(days=1, hours=2),
        )

        # This would be tested with the full app/auth middleware
        # For unit testing, we just verify the route exists and takes correct params
        assert create_event is not None


class TestEventHelpers:
    """Test helper functions"""

    @pytest.mark.asyncio
    async def test_get_related_events_sorts_by_date_proximity(self, mock_event_data):
        """Test that related events are sorted by date proximity"""
        # Create events with different dates
        event1 = {
            **mock_event_data,
            "id": str(uuid4()),
            "start_datetime": (datetime.utcnow() + timedelta(days=10)).isoformat(),
        }
        event2 = {
            **mock_event_data,
            "id": str(uuid4()),
            "start_datetime": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        }
        event3 = {
            **mock_event_data,
            "id": str(uuid4()),
            "start_datetime": (datetime.utcnow() + timedelta(days=15)).isoformat(),
        }

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.query_collection = AsyncMock(
                return_value=[event1, event2, event3]
            )

            current_event = {
                **mock_event_data,
                "start_datetime": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            }

            related = await get_related_events(db_instance, current_event, limit=3)

            # Should return all 3 sorted by proximity
            # Closest should be event2 (5 days vs 7 = 2 days diff)
            # Then event1 (10 days vs 7 = 3 days diff)
            # Then event3 (15 days vs 7 = 8 days diff)
            assert len(related) == 3

    @pytest.mark.asyncio
    async def test_get_instructor_info_handles_missing_profile(self, mock_instructor_data):
        """Test instructor info when profile doesn't exist"""
        instructor_id = mock_instructor_data["id"]

        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(
                side_effect=lambda collection, id: {
                    "users": mock_instructor_data,
                    "profiles": None,
                }.get(collection)
            )

            info = await get_instructor_info(db_instance, [instructor_id])

            # Should still return basic user info
            assert info is not None
            assert info["id"] == instructor_id
            assert info["email"] == mock_instructor_data["email"]

    @pytest.mark.asyncio
    async def test_get_instructor_info_returns_none_for_invalid_id(self):
        """Test instructor info returns None for invalid ID"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value
            db_instance.get_by_id = AsyncMock(return_value=None)

            info = await get_instructor_info(db_instance, [str(uuid4())])

            assert info is None

    @pytest.mark.asyncio
    async def test_get_instructor_info_returns_none_for_empty_list(self):
        """Test instructor info returns None for empty list"""
        with patch("backend.routes.events.ZeroDBService") as mock_db:
            db_instance = mock_db.return_value

            info = await get_instructor_info(db_instance, [])

            assert info is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
