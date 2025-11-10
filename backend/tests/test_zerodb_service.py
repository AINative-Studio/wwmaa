"""
Unit Tests for ZeroDB Client Wrapper

Comprehensive test suite for the ZeroDBClient class covering:
- CRUD operations
- Vector search
- Object storage operations
- Error handling
- Connection pooling
- Retry logic
"""

import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch, mock_open
import pytest
import requests

from backend.services.zerodb_service import (
    ZeroDBClient,
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBAuthenticationError,
    ZeroDBNotFoundError,
    ZeroDBValidationError,
    get_zerodb_client
)


class TestZeroDBClientInitialization:
    """Test client initialization and configuration"""

    def test_client_initialization_with_defaults(self):
        """Test client initialization with default values from settings"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_api_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"

            client = ZeroDBClient()

            assert client.api_key == "test_api_key"
            assert client.base_url == "https://api.test.com"
            assert client.timeout == 10
            assert "Authorization" in client.headers
            assert client.headers["Authorization"] == "Bearer test_api_key"

    def test_client_initialization_with_custom_values(self):
        """Test client initialization with custom values"""
        client = ZeroDBClient(
            api_key="custom_key",
            base_url="https://custom.api.com",
            timeout=20
        )

        assert client.api_key == "custom_key"
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 20

    def test_client_initialization_without_api_key(self):
        """Test client initialization fails without API key"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = ""
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"

            with pytest.raises(ZeroDBAuthenticationError, match="ZERODB_API_KEY is required"):
                ZeroDBClient()

    def test_client_initialization_without_base_url(self):
        """Test client initialization fails without base URL"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = ""

            with pytest.raises(ZeroDBConnectionError, match="ZERODB_API_BASE_URL is required"):
                ZeroDBClient()

    def test_session_creation_with_retry_logic(self):
        """Test that session is created with retry logic"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"

            client = ZeroDBClient(max_retries=5)

            assert client.session is not None
            assert hasattr(client.session, 'get_adapter')

    def test_context_manager(self):
        """Test client works as context manager"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"

            with ZeroDBClient() as client:
                assert client is not None

            # Session should be closed after exiting context


class TestZeroDBClientCRUD:
    """Test CRUD operations"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_create_document_success(self, client):
        """Test successful document creation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "doc_123",
            "data": {"name": "Test", "status": "active"},
            "created_at": "2025-01-09T00:00:00Z"
        }

        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.create_document("users", {"name": "Test", "status": "active"})

            assert result["id"] == "doc_123"
            assert result["data"]["name"] == "Test"
            client.session.post.assert_called_once()

    def test_create_document_with_custom_id(self, client):
        """Test document creation with custom ID"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"id": "custom_123"}

        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.create_document(
                "users",
                {"name": "Test"},
                document_id="custom_123"
            )

            assert result["id"] == "custom_123"
            # Verify the payload includes the custom ID
            call_args = client.session.post.call_args
            assert "id" in call_args[1]["json"]

    def test_create_document_validation_error(self, client):
        """Test document creation with validation error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Invalid data format"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'post', return_value=mock_response):
            with pytest.raises(ZeroDBValidationError, match="Invalid data format"):
                client.create_document("users", {})

    def test_get_document_success(self, client):
        """Test successful document retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "doc_123",
            "data": {"name": "Test User"},
            "created_at": "2025-01-09T00:00:00Z"
        }

        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.get_document("users", "doc_123")

            assert result["id"] == "doc_123"
            assert result["data"]["name"] == "Test User"

    def test_get_document_not_found(self, client):
        """Test document retrieval when document doesn't exist"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Document not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBNotFoundError, match="Document not found"):
                client.get_document("users", "nonexistent_id")

    def test_query_documents_success(self, client):
        """Test successful document query"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "documents": [
                {"id": "doc_1", "data": {"status": "active"}},
                {"id": "doc_2", "data": {"status": "active"}}
            ],
            "total": 2,
            "limit": 10,
            "offset": 0
        }

        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.query_documents(
                "users",
                filters={"status": "active"},
                limit=10
            )

            assert len(result["documents"]) == 2
            assert result["total"] == 2

    def test_query_documents_with_sorting(self, client):
        """Test document query with sorting"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"documents": [], "total": 0}

        with patch.object(client.session, 'post', return_value=mock_response):
            client.query_documents(
                "users",
                filters={"status": "active"},
                sort={"created_at": "desc"}
            )

            call_args = client.session.post.call_args
            payload = call_args[1]["json"]
            assert "sort" in payload
            assert payload["sort"]["created_at"] == "desc"

    def test_update_document_success(self, client):
        """Test successful document update"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "doc_123",
            "data": {"name": "Updated Name", "status": "active"},
            "updated_at": "2025-01-09T01:00:00Z"
        }

        with patch.object(client.session, 'put', return_value=mock_response):
            result = client.update_document(
                "users",
                "doc_123",
                {"name": "Updated Name"}
            )

            assert result["data"]["name"] == "Updated Name"

    def test_update_document_with_merge_false(self, client):
        """Test document update with merge=False"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"id": "doc_123"}

        with patch.object(client.session, 'put', return_value=mock_response):
            client.update_document(
                "users",
                "doc_123",
                {"name": "New Name"},
                merge=False
            )

            call_args = client.session.put.call_args
            payload = call_args[1]["json"]
            assert payload["merge"] is False

    def test_delete_document_success(self, client):
        """Test successful document deletion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"success": True, "id": "doc_123"}

        with patch.object(client.session, 'delete', return_value=mock_response):
            result = client.delete_document("users", "doc_123")

            assert result["success"] is True
            assert result["id"] == "doc_123"

    def test_delete_document_not_found(self, client):
        """Test document deletion when document doesn't exist"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Document not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'delete', return_value=mock_response):
            with pytest.raises(ZeroDBNotFoundError):
                client.delete_document("users", "nonexistent_id")


class TestZeroDBClientVectorSearch:
    """Test vector search operations"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_vector_search_success(self, client):
        """Test successful vector search"""
        query_vector = [0.1, 0.2, 0.3, 0.4]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "results": [
                {"id": "doc_1", "score": 0.95, "data": {"title": "Result 1"}},
                {"id": "doc_2", "score": 0.87, "data": {"title": "Result 2"}}
            ],
            "query_time_ms": 45
        }

        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.vector_search("content_index", query_vector, top_k=10)

            assert len(result["results"]) == 2
            assert result["results"][0]["score"] == 0.95

    def test_vector_search_with_filters(self, client):
        """Test vector search with filters"""
        query_vector = [0.1, 0.2, 0.3]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"results": []}

        with patch.object(client.session, 'post', return_value=mock_response):
            client.vector_search(
                "content_index",
                query_vector,
                filters={"category": "martial_arts"},
                top_k=5
            )

            call_args = client.session.post.call_args
            payload = call_args[1]["json"]
            assert "filters" in payload
            assert payload["filters"]["category"] == "martial_arts"

    def test_vector_search_validation_error(self, client):
        """Test vector search with invalid vector"""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Invalid vector dimensions"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'post', return_value=mock_response):
            with pytest.raises(ZeroDBValidationError, match="Invalid vector dimensions"):
                client.vector_search("content_index", [0.1, 0.2])


class TestZeroDBClientObjectStorage:
    """Test object storage operations"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_upload_object_success(self, client):
        """Test successful object upload"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_file = f.name

        try:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {
                "object_name": "test.txt",
                "url": "https://storage.test.com/test.txt",
                "size": 12
            }

            with patch.object(client.session, 'post', return_value=mock_response):
                result = client.upload_object(temp_file)

                assert result["object_name"] == "test.txt"
                assert "url" in result
        finally:
            os.unlink(temp_file)

    def test_upload_object_with_custom_name(self, client):
        """Test object upload with custom name"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_file = f.name

        try:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {"object_name": "custom_name.txt"}

            with patch.object(client.session, 'post', return_value=mock_response):
                result = client.upload_object(temp_file, object_name="custom_name.txt")

                assert result["object_name"] == "custom_name.txt"
        finally:
            os.unlink(temp_file)

    def test_upload_object_file_not_found(self, client):
        """Test object upload with non-existent file"""
        with pytest.raises(FileNotFoundError):
            client.upload_object("/nonexistent/path/file.txt")

    def test_download_object_success(self, client):
        """Test successful object download"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.content = b"File content here"

        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.download_object("test.txt")

            assert result == b"File content here"

    def test_download_object_to_file(self, client):
        """Test downloading object to file"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.content = b"File content"

        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = os.path.join(temp_dir, "downloaded.txt")

            with patch.object(client.session, 'get', return_value=mock_response):
                result = client.download_object("test.txt", save_path=save_path)

                assert result == save_path
                assert os.path.exists(save_path)
                with open(save_path, 'rb') as f:
                    assert f.read() == b"File content"

    def test_download_object_not_found(self, client):
        """Test downloading non-existent object"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Object not found"}

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBNotFoundError, match="Object not found"):
                client.download_object("nonexistent.txt")

    def test_delete_object_success(self, client):
        """Test successful object deletion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {"success": True, "object_name": "test.txt"}

        with patch.object(client.session, 'delete', return_value=mock_response):
            result = client.delete_object("test.txt")

            assert result["success"] is True

    def test_list_objects_success(self, client):
        """Test successful object listing"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "objects": [
                {"name": "file1.txt", "size": 100},
                {"name": "file2.txt", "size": 200}
            ],
            "total": 2
        }

        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.list_objects(prefix="file", limit=10)

            assert len(result["objects"]) == 2
            assert result["total"] == 2


class TestZeroDBClientErrorHandling:
    """Test error handling scenarios"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_authentication_error_401(self, client):
        """Test handling of 401 authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Invalid API key"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBAuthenticationError, match="Invalid API key"):
                client.get_document("users", "doc_123")

    def test_authentication_error_403(self, client):
        """Test handling of 403 forbidden error"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Access denied"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBAuthenticationError, match="Access denied"):
                client.get_document("users", "doc_123")

    def test_connection_error(self, client):
        """Test handling of connection error"""
        def raise_connection_error(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Connection failed")

        with patch.object(client.session, 'get', side_effect=raise_connection_error):
            with pytest.raises(ZeroDBConnectionError, match="Failed to connect"):
                client.get_document("users", "doc_123")

    def test_timeout_error(self, client):
        """Test handling of timeout error"""
        def raise_timeout_error(*args, **kwargs):
            raise requests.exceptions.Timeout("Request timed out")

        with patch.object(client.session, 'get', side_effect=raise_timeout_error):
            with pytest.raises(ZeroDBConnectionError, match="Request timed out"):
                client.get_document("users", "doc_123")

    def test_generic_http_error(self, client):
        """Test handling of generic HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBError, match="Internal server error"):
                client.get_document("users", "doc_123")

    def test_error_with_no_json_response(self, client):
        """Test handling of error with non-JSON response"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_response.text = "Server error"
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

        with patch.object(client.session, 'get', return_value=mock_response):
            with pytest.raises(ZeroDBError):
                client.get_document("users", "doc_123")


class TestZeroDBClientUtilities:
    """Test utility methods"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_build_url(self, client):
        """Test URL building"""
        url = client._build_url("collections", "users", "documents")
        assert "collections/users/documents" in url

    def test_build_url_with_trailing_slashes(self, client):
        """Test URL building handles trailing slashes"""
        url = client._build_url("collections/", "/users/", "documents/")
        assert url.count("//") == 1  # Only in https://

    def test_close_session(self, client):
        """Test session cleanup"""
        client.close()
        # After close, session should be closed (we can't easily verify this without side effects)


class TestZeroDBClientSingleton:
    """Test singleton pattern for global client"""

    def test_get_zerodb_client(self):
        """Test getting global client instance"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"

            client1 = get_zerodb_client()
            client2 = get_zerodb_client()

            # Should return the same instance
            assert client1 is client2


class TestZeroDBClientIntegration:
    """Integration-style tests for complex scenarios"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        with patch('backend.services.zerodb_service.settings') as mock_settings:
            mock_settings.ZERODB_API_KEY = "test_key"
            mock_settings.ZERODB_API_BASE_URL = "https://api.test.com"
            return ZeroDBClient()

    def test_complete_document_lifecycle(self, client):
        """Test creating, updating, and deleting a document"""
        # Create
        create_response = Mock()
        create_response.status_code = 200
        create_response.ok = True
        create_response.json.return_value = {"id": "doc_123", "data": {"name": "Test"}}

        # Update
        update_response = Mock()
        update_response.status_code = 200
        update_response.ok = True
        update_response.json.return_value = {"id": "doc_123", "data": {"name": "Updated"}}

        # Delete
        delete_response = Mock()
        delete_response.status_code = 200
        delete_response.ok = True
        delete_response.json.return_value = {"success": True}

        with patch.object(client.session, 'post', return_value=create_response):
            created = client.create_document("users", {"name": "Test"})
            assert created["id"] == "doc_123"

        with patch.object(client.session, 'put', return_value=update_response):
            updated = client.update_document("users", "doc_123", {"name": "Updated"})
            assert updated["data"]["name"] == "Updated"

        with patch.object(client.session, 'delete', return_value=delete_response):
            deleted = client.delete_object("doc_123")
            assert deleted["success"] is True

    def test_query_with_pagination(self, client):
        """Test querying with pagination"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            "documents": [{"id": f"doc_{i}"} for i in range(10)],
            "total": 100,
            "limit": 10,
            "offset": 20
        }

        with patch.object(client.session, 'post', return_value=mock_response):
            result = client.query_documents(
                "users",
                filters={"status": "active"},
                limit=10,
                offset=20
            )

            assert len(result["documents"]) == 10
            assert result["total"] == 100
            assert result["offset"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.services.zerodb_service", "--cov-report=term-missing"])
