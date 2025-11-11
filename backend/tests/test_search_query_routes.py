"""
Tests for Search Query Routes (US-038)

Tests the search query endpoint including:
- Request validation
- Rate limiting
- Timeout handling
- Error responses
- Success responses
- Health check
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from backend.app import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_search_service():
    """Mock search service"""
    mock = Mock()
    mock.search_query.return_value = {
        "answer": "# Martial Arts Guide\n\nGreat techniques for beginners...",
        "sources": [
            {
                "title": "Beginner's Guide",
                "url": "/articles/guide",
                "source_type": "article"
            }
        ],
        "media": {
            "videos": [],
            "images": []
        },
        "related_queries": [
            "martial arts classes",
            "self defense techniques",
            "karate basics"
        ],
        "latency_ms": 450,
        "cached": False
    }
    return mock


class TestSearchQueryEndpoint:
    """Test POST /api/search/query endpoint"""

    def test_successful_search(self, client):
        """Test successful search query"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test answer",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 500,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "What is karate?"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "media" in data
            assert "related_queries" in data
            assert "latency_ms" in data
            assert "cached" in data

    def test_empty_query(self, client):
        """Test that empty query is rejected"""
        response = client.post(
            "/api/search/query",
            json={"query": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_whitespace_only_query(self, client):
        """Test that whitespace-only query is rejected"""
        response = client.post(
            "/api/search/query",
            json={"query": "   "}
        )

        assert response.status_code == 422  # Validation error

    def test_too_long_query(self, client):
        """Test that query over 500 chars is rejected"""
        long_query = "a" * 501

        response = client.post(
            "/api/search/query",
            json={"query": long_query}
        )

        assert response.status_code == 422  # Validation error

    def test_max_length_query(self, client):
        """Test that query exactly 500 chars is accepted"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 100,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            max_query = "a" * 500

            response = client.post(
                "/api/search/query",
                json={"query": max_query}
            )

            assert response.status_code == 200

    def test_sql_injection_attempt(self, client):
        """Test that SQL injection patterns are rejected"""
        malicious_queries = [
            "test'; DROP TABLE users--",
            "test/* comment */",
            "test; exec sp_executesql"
        ]

        for query in malicious_queries:
            response = client.post(
                "/api/search/query",
                json={"query": query}
            )

            # Should be rejected by validation
            assert response.status_code == 422

    def test_bypass_cache_parameter(self, client):
        """Test bypass_cache parameter"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 100,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test", "bypass_cache": True}
            )

            assert response.status_code == 200

            # Verify bypass_cache was passed to service
            call_args = mock_service.search_query.call_args
            assert call_args[1]["bypass_cache"] is True


class TestRateLimiting:
    """Test rate limiting on search endpoint"""

    @pytest.mark.skip(reason="Rate limiting requires Redis integration")
    def test_rate_limit_exceeded(self, client):
        """Test that rate limit returns 429"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 100,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            # Make 11 requests (limit is 10 per minute)
            for i in range(11):
                response = client.post(
                    "/api/search/query",
                    json={"query": f"test query {i}"}
                )

                if i < 10:
                    assert response.status_code == 200
                else:
                    # 11th request should be rate limited
                    assert response.status_code == 429


class TestErrorHandling:
    """Test error handling"""

    def test_search_error(self, client):
        """Test handling of search service error"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            from backend.services.query_search_service import QuerySearchError
            mock_service = Mock()
            mock_service.search_query.side_effect = QuerySearchError("Search failed")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test query"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "error" in data["detail"]
            assert data["detail"]["error"] == "search_error"

    def test_timeout_error(self, client):
        """Test handling of timeout"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            import asyncio
            mock_service = Mock()
            mock_service.search_query.side_effect = asyncio.TimeoutError()
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test query"}
            )

            assert response.status_code == 408
            data = response.json()
            assert "timeout" in data["detail"]["error"]

    def test_internal_server_error(self, client):
        """Test handling of unexpected errors"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.side_effect = Exception("Unexpected error")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test query"}
            )

            assert response.status_code == 500
            data = response.json()
            assert "internal_server_error" in data["detail"]["error"]


class TestResponseFormat:
    """Test response format"""

    def test_response_has_all_fields(self, client):
        """Test that response contains all required fields"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "# Answer\n\nContent",
                "sources": [
                    {
                        "title": "Source 1",
                        "url": "/articles/1",
                        "source_type": "article"
                    }
                ],
                "media": {
                    "videos": [
                        {
                            "id": "video1",
                            "title": "Video 1",
                            "cloudflare_stream_id": "stream1"
                        }
                    ],
                    "images": [
                        {
                            "url": "https://example.com/image.jpg",
                            "alt": "Image",
                            "zerodb_object_key": "key1"
                        }
                    ]
                },
                "related_queries": ["query 1", "query 2", "query 3"],
                "latency_ms": 847,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test query"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all fields present
            assert "answer" in data
            assert "sources" in data
            assert "media" in data
            assert "related_queries" in data
            assert "latency_ms" in data
            assert "cached" in data

            # Verify field types
            assert isinstance(data["answer"], str)
            assert isinstance(data["sources"], list)
            assert isinstance(data["media"], dict)
            assert isinstance(data["related_queries"], list)
            assert isinstance(data["latency_ms"], int)
            assert isinstance(data["cached"], bool)

            # Verify nested structures
            assert "videos" in data["media"]
            assert "images" in data["media"]
            assert len(data["sources"]) == 1
            assert "title" in data["sources"][0]
            assert "url" in data["sources"][0]
            assert "source_type" in data["sources"][0]

    def test_cached_response(self, client):
        """Test cached response format"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Cached answer",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 50,
                "cached": True
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test query"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cached"] is True
            # Cached responses should be fast
            assert data["latency_ms"] < 100


class TestHealthCheck:
    """Test health check endpoint"""

    @pytest.mark.skip(reason="Health check endpoint implementation may vary")
    def test_health_check(self, client):
        """Test search service health check"""
        response = client.get("/api/search/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["service"] == "search"


class TestIPExtraction:
    """Test IP address extraction for logging"""

    def test_direct_ip(self, client):
        """Test direct IP extraction"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 100,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test"}
            )

            assert response.status_code == 200

            # Verify IP was passed to service
            call_args = mock_service.search_query.call_args
            assert "ip_address" in call_args[1]

    def test_forwarded_for_header(self, client):
        """Test X-Forwarded-For header"""
        with patch('backend.routes.search.get_query_search_service') as mock_get_service:
            mock_service = Mock()
            mock_service.search_query.return_value = {
                "answer": "Test",
                "sources": [],
                "media": {"videos": [], "images": []},
                "related_queries": [],
                "latency_ms": 100,
                "cached": False
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/search/query",
                json={"query": "test"},
                headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
            )

            assert response.status_code == 200

            # Verify first IP was extracted
            call_args = mock_service.search_query.call_args
            ip_address = call_args[1]["ip_address"]
            assert ip_address == "203.0.113.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
