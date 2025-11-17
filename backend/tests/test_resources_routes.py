"""
Test Resources Routes

Comprehensive tests for the resources API endpoints including:
- List resources with role-based filtering
- Get specific resource
- Create resource (admin/instructor)
- Update resource (admin/instructor)
- Delete resource (admin only)
- File upload
- View/download tracking
- Empty state handling
- Permission checks
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock

from backend.app import app
from backend.models.schemas import (
    ResourceCategory,
    ResourceVisibility,
    ResourceStatus,
    UserRole
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_member_user():
    """Mock member user for dependency override"""
    return {
        "id": uuid4(),
        "email": "member@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_instructor_user():
    """Mock instructor user for dependency override"""
    return {
        "id": uuid4(),
        "email": "instructor@example.com",
        "role": "instructor"
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user for dependency override"""
    return {
        "id": uuid4(),
        "email": "admin@example.com",
        "role": "admin"
    }


@pytest.fixture
def client_with_member(mock_member_user):
    """TestClient with member user authentication"""
    from backend.middleware.auth_middleware import get_current_user

    async def override_current_user(credentials=None):
        return mock_member_user

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_instructor(mock_instructor_user):
    """TestClient with instructor user authentication"""
    from backend.middleware.auth_middleware import get_current_user

    async def override_current_user(credentials=None):
        return mock_instructor_user

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_admin(mock_admin_user):
    """TestClient with admin user authentication"""
    from backend.middleware.auth_middleware import get_current_user

    async def override_current_user(credentials=None):
        return mock_admin_user

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestListResources:
    """Test GET /api/resources endpoint"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_as_member(self, mock_db, client_with_member):
        """Test member can list published member-accessible resources"""
        # Mock ZeroDB response
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": str(uuid4()),
                    "data": {
                        "title": "BJJ Fundamentals",
                        "description": "Beginner guide to BJJ",
                        "category": ResourceCategory.VIDEO.value,
                        "tags": ["bjj", "beginner"],
                        "file_url": None,
                        "external_url": "https://youtube.com/example",
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": True,
                        "display_order": 1,
                        "view_count": 10,
                        "download_count": 5,
                    }
                },
                {
                    "id": str(uuid4()),
                    "data": {
                        "title": "Public Resource",
                        "description": "Public guide",
                        "category": ResourceCategory.ARTICLE.value,
                        "tags": ["public"],
                        "file_url": None,
                        "external_url": "https://wwmaa.com/article",
                        "visibility": ResourceVisibility.PUBLIC.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 10,
                        "view_count": 50,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["resources"]) == 2

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_filters_by_visibility(self, mock_db, client_with_member):
        """Test that members cannot see instructor-only resources"""
        # Mock ZeroDB response with instructor-only resource
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": str(uuid4()),
                    "data": {
                        "title": "Instructor Guide",
                        "description": "For instructors only",
                        "category": ResourceCategory.DOCUMENT.value,
                        "tags": ["instructor"],
                        "file_url": "https://storage.wwmaa.com/instructor-guide.pdf",
                        "visibility": ResourceVisibility.INSTRUCTORS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 1,
                        "view_count": 0,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        # Member should not see instructor-only resources
        assert len(data["resources"]) == 0

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_empty_state(self, mock_db, client_with_member):
        """Test empty state returns empty list, not error"""
        # Mock ZeroDB response with no resources
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": []
        }
        mock_db.return_value = mock_client

        response = client_with_member.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        assert data["resources"] == []
        assert data["total"] == 0

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_with_filters(self, mock_db, client_with_member):
        """Test filtering by category and featured status"""
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": []
        }
        mock_db.return_value = mock_client

        response = client_with_member.get(
            "/api/resources?category=video&featured_only=true"
        )

        assert response.status_code == 200
        # Verify filters were passed to ZeroDB
        call_args = mock_client.query_documents.call_args[1]
        assert call_args["filters"]["category"] == "video"
        assert call_args["filters"]["is_featured"] is True

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_pagination(self, mock_db, client_with_member):
        """Test pagination parameters"""
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": []
        }
        mock_db.return_value = mock_client

        response = client_with_member.get(
            "/api/resources?page=2&page_size=10"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_list_resources_instructor_sees_drafts(self, mock_db, client_with_instructor):
        """Test that instructors can see draft resources"""
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": str(uuid4()),
                    "data": {
                        "title": "Draft Resource",
                        "description": "Work in progress",
                        "category": ResourceCategory.VIDEO.value,
                        "tags": ["draft"],
                        "external_url": "https://youtube.com/draft",
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.DRAFT.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 1,
                        "view_count": 0,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_instructor.get("/api/resources")

        assert response.status_code == 200
        data = response.json()
        assert len(data["resources"]) == 1
        assert data["resources"][0]["status"] == "draft"


class TestGetResource:
    """Test GET /api/resources/{resource_id} endpoint"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_get_resource_success(self, mock_db, client_with_member):
        """Test getting a specific resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "title": "BJJ Fundamentals",
                        "description": "Beginner guide",
                        "category": ResourceCategory.VIDEO.value,
                        "tags": ["bjj"],
                        "external_url": "https://youtube.com/example",
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": True,
                        "display_order": 1,
                        "view_count": 10,
                        "download_count": 5,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.get(f"/api/resources/{resource_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resource_id
        assert data["title"] == "BJJ Fundamentals"

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_get_resource_not_found(self, mock_db, client_with_member):
        """Test getting non-existent resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": []
        }
        mock_db.return_value = mock_client

        response = client_with_member.get(f"/api/resources/{resource_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_get_resource_forbidden_visibility(self, mock_db, client_with_member):
        """Test member cannot access instructor-only resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "title": "Instructor Guide",
                        "description": "For instructors",
                        "category": ResourceCategory.DOCUMENT.value,
                        "tags": ["instructor"],
                        "file_url": "https://storage.wwmaa.com/guide.pdf",
                        "visibility": ResourceVisibility.INSTRUCTORS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 1,
                        "view_count": 0,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.get(f"/api/resources/{resource_id}")

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


class TestCreateResource:
    """Test POST /api/resources endpoint"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_create_resource_as_admin(self, mock_db, client_with_admin):
        """Test admin can create resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.create_document.return_value = {"id": resource_id}
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "title": "New Resource",
                        "description": "Test resource",
                        "category": ResourceCategory.VIDEO.value,
                        "tags": ["test"],
                        "external_url": "https://youtube.com/test",
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "published_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 0,
                        "view_count": 0,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_admin.post(
            "/api/resources",
            json={
                "title": "New Resource",
                "description": "Test resource",
                "category": "video",
                "tags": ["test"],
                "external_url": "https://youtube.com/test",
                "visibility": "members_only",
                "status": "published"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Resource"

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_create_resource_validation_error(self, mock_db, client_with_admin):
        """Test validation error when neither file_url nor external_url provided"""
        mock_client = MagicMock()
        mock_db.return_value = mock_client

        response = client_with_admin.post(
            "/api/resources",
            json={
                "title": "Invalid Resource",
                "description": "Missing URLs",
                "category": "video",
                "visibility": "members_only",
                "status": "draft"
            }
        )

        assert response.status_code == 400
        assert "url" in response.json()["detail"].lower()

    def test_create_resource_requires_authentication(self):
        """Test creating resource without authentication fails"""
        client = TestClient(app)
        response = client.post(
            "/api/resources",
            json={
                "title": "Test",
                "category": "video",
                "external_url": "https://youtube.com/test"
            }
        )

        assert response.status_code == 401

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_create_resource_member_forbidden(self, mock_db, client_with_member):
        """Test member cannot create resource"""
        mock_client = MagicMock()
        mock_db.return_value = mock_client

        response = client_with_member.post(
            "/api/resources",
            json={
                "title": "Test",
                "category": "video",
                "external_url": "https://youtube.com/test",
                "visibility": "members_only",
                "status": "draft"
            }
        )

        assert response.status_code == 403


class TestUpdateResource:
    """Test PUT /api/resources/{resource_id} endpoint"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_update_resource_as_admin(self, mock_db, client_with_admin):
        """Test admin can update any resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.side_effect = [
            # First call: fetch existing resource
            {
                "documents": [
                    {
                        "id": resource_id,
                        "data": {
                            "title": "Old Title",
                            "description": "Old description",
                            "category": ResourceCategory.VIDEO.value,
                            "tags": ["old"],
                            "external_url": "https://youtube.com/old",
                            "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                            "status": ResourceStatus.DRAFT.value,
                            "created_by": str(uuid4()),
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat(),
                            "is_featured": False,
                            "display_order": 0,
                            "view_count": 0,
                            "download_count": 0,
                        }
                    }
                ]
            },
            # Second call: fetch updated resource
            {
                "documents": [
                    {
                        "id": resource_id,
                        "data": {
                            "title": "Updated Title",
                            "description": "Old description",
                            "category": ResourceCategory.VIDEO.value,
                            "tags": ["old"],
                            "external_url": "https://youtube.com/old",
                            "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                            "status": ResourceStatus.PUBLISHED.value,
                            "created_by": str(uuid4()),
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat(),
                            "published_at": datetime.utcnow().isoformat(),
                            "is_featured": False,
                            "display_order": 0,
                            "view_count": 0,
                            "download_count": 0,
                        }
                    }
                ]
            }
        ]
        mock_db.return_value = mock_client

        response = client_with_admin.put(
            f"/api/resources/{resource_id}",
            json={
                "title": "Updated Title",
                "status": "published"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_update_resource_instructor_own_only(self, mock_db, client_with_instructor):
        """Test instructor can only update their own resources"""
        resource_id = str(uuid4())
        other_user_id = str(uuid4())

        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "title": "Someone else's resource",
                        "description": "Test",
                        "category": ResourceCategory.VIDEO.value,
                        "tags": [],
                        "external_url": "https://youtube.com/test",
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": other_user_id,  # Different user
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "is_featured": False,
                        "display_order": 0,
                        "view_count": 0,
                        "download_count": 0,
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_instructor.put(
            f"/api/resources/{resource_id}",
            json={"title": "Updated"}
        )

        assert response.status_code == 403


class TestDeleteResource:
    """Test DELETE /api/resources/{resource_id} endpoint"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_delete_resource_as_admin(self, mock_db, client_with_admin):
        """Test admin can delete resource"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "title": "To Delete",
                        "category": ResourceCategory.VIDEO.value,
                        "visibility": ResourceVisibility.MEMBERS_ONLY.value,
                        "status": ResourceStatus.PUBLISHED.value,
                        "created_by": str(uuid4()),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_admin.delete(
            f"/api/resources/{resource_id}"
        )

        assert response.status_code == 204

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_delete_resource_instructor_forbidden(self, mock_db, client_with_instructor):
        """Test instructor cannot delete resources"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_db.return_value = mock_client

        response = client_with_instructor.delete(
            f"/api/resources/{resource_id}"
        )

        assert response.status_code == 403


class TestTrackResourceEngagement:
    """Test resource view and download tracking endpoints"""

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_track_view(self, mock_db, client_with_member):
        """Test tracking resource view"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "view_count": 10
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.post(
            f"/api/resources/{resource_id}/track-view"
        )

        assert response.status_code == 200
        # Verify view count was incremented
        mock_client.update_document.assert_called_once()

    @patch('backend.services.zerodb_service.get_zerodb_client')
    def test_track_download(self, mock_db, client_with_member):
        """Test tracking resource download"""
        resource_id = str(uuid4())
        mock_client = MagicMock()
        mock_client.query_documents.return_value = {
            "documents": [
                {
                    "id": resource_id,
                    "data": {
                        "download_count": 5
                    }
                }
            ]
        }
        mock_db.return_value = mock_client

        response = client_with_member.post(
            f"/api/resources/{resource_id}/track-download"
        )

        assert response.status_code == 200
        # Verify download count was incremented
        mock_client.update_document.assert_called_once()
