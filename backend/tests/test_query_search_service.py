"""
Tests for Query Search Service (US-038)

Tests the full 11-step query processing pipeline including:
- Query normalization
- Caching
- Embedding generation
- Vector search
- AI answer generation
- Media attachment
- Query logging
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from backend.services.query_search_service import (
    QuerySearchService,
    QuerySearchError,
    get_query_search_service
)


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for caching"""
    mock = Mock()
    mock.ping.return_value = True
    mock.get.return_value = None  # Cache miss by default
    mock.setex.return_value = True
    return mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = Mock()
    # Return a 1536-dimensional vector (text-embedding-3-small)
    mock.generate_embedding.return_value = [0.1] * 1536
    return mock


@pytest.fixture
def mock_vector_search_service():
    """Mock vector search service"""
    mock = Mock()
    mock.search_martial_arts_content.return_value = [
        {
            "id": "doc1",
            "data": {
                "title": "Beginner Karate Techniques",
                "description": "Learn basic karate techniques",
                "video_id": "video123"
            },
            "source_collection": "articles",
            "score": 0.95
        },
        {
            "id": "doc2",
            "data": {
                "title": "Advanced Judo Throws",
                "description": "Master judo throwing techniques",
                "image_url": "https://example.com/image.jpg"
            },
            "source_collection": "techniques",
            "score": 0.87
        }
    ]
    return mock


@pytest.fixture
def mock_ai_registry_service():
    """Mock AI Registry service"""
    mock = Mock()
    mock.generate_answer.return_value = {
        "answer": "# Martial Arts for Beginners\n\nHere are some great techniques...",
        "model": "gpt-4o-mini",
        "tokens_used": 150,
        "latency_ms": 300
    }
    mock.generate_related_queries.return_value = [
        "best martial arts for self defense",
        "martial arts classes near me",
        "how to start learning martial arts"
    ]
    return mock


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client"""
    mock = Mock()
    mock.create_document.return_value = {"id": "query123", "success": True}
    return mock


@pytest.fixture
def search_service(
    mock_redis_client,
    mock_embedding_service,
    mock_vector_search_service,
    mock_ai_registry_service,
    mock_zerodb_client
):
    """Create search service with mocked dependencies"""
    with patch('backend.services.query_search_service.redis.from_url', return_value=mock_redis_client), \
         patch('backend.services.query_search_service.get_embedding_service', return_value=mock_embedding_service), \
         patch('backend.services.query_search_service.get_vector_search_service', return_value=mock_vector_search_service), \
         patch('backend.services.query_search_service.get_ai_registry_service', return_value=mock_ai_registry_service), \
         patch('backend.services.query_search_service.get_zerodb_client', return_value=mock_zerodb_client):

        service = QuerySearchService()
        return service


class TestQueryNormalization:
    """Test query normalization and validation"""

    def test_normalize_valid_query(self, search_service):
        """Test normalizing a valid query"""
        query = "  What is KARATE?  "
        normalized = search_service._normalize_query(query)
        assert normalized == "what is karate?"

    def test_normalize_empty_query(self, search_service):
        """Test that empty queries raise error"""
        with pytest.raises(QuerySearchError, match="Query cannot be empty"):
            search_service._normalize_query("")

    def test_normalize_whitespace_only_query(self, search_service):
        """Test that whitespace-only queries raise error"""
        with pytest.raises(QuerySearchError, match="Query cannot be empty"):
            search_service._normalize_query("   ")

    def test_normalize_too_long_query(self, search_service):
        """Test that queries over 500 chars raise error"""
        long_query = "a" * 501
        with pytest.raises(QuerySearchError, match="exceeds maximum length"):
            search_service._normalize_query(long_query)

    def test_normalize_max_length_query(self, search_service):
        """Test that queries exactly 500 chars are accepted"""
        max_query = "a" * 500
        normalized = search_service._normalize_query(max_query)
        assert len(normalized) == 500


class TestCaching:
    """Test caching functionality"""

    def test_cache_key_generation(self, search_service):
        """Test cache key generation"""
        query = "test query"
        key = search_service._generate_cache_key(query)
        assert key.startswith("search:query:")
        assert len(key) > 20  # Hash should be long

    def test_cache_hit(self, search_service, mock_redis_client):
        """Test cache hit returns cached result"""
        import json

        cached_result = {
            "answer": "Cached answer",
            "sources": [],
            "media": {"videos": [], "images": []},
            "related_queries": [],
            "latency_ms": 100,
            "cached": False
        }
        mock_redis_client.get.return_value = json.dumps(cached_result)

        result = search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        assert result["cached"] is True
        assert result["answer"] == "Cached answer"

    def test_cache_miss_proceeds_with_search(self, search_service, mock_redis_client):
        """Test cache miss continues with full search"""
        mock_redis_client.get.return_value = None

        result = search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        assert result["cached"] is False
        # Verify embedding was generated
        search_service.embedding_service.generate_embedding.assert_called_once()

    def test_bypass_cache(self, search_service, mock_redis_client):
        """Test bypassing cache"""
        result = search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1",
            bypass_cache=True
        )

        # Cache should not be checked
        mock_redis_client.get.assert_not_called()
        # Cache should not be set
        mock_redis_client.setex.assert_not_called()


class TestSearchPipeline:
    """Test full search pipeline"""

    def test_successful_search(self, search_service):
        """Test successful search execution"""
        result = search_service.search_query(
            query="What are the best martial arts for beginners?",
            user_id="user123",
            ip_address="192.168.1.1"
        )

        # Verify response structure
        assert "answer" in result
        assert "sources" in result
        assert "media" in result
        assert "related_queries" in result
        assert "latency_ms" in result
        assert "cached" in result

        # Verify answer
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

        # Verify sources
        assert len(result["sources"]) == 2
        assert result["sources"][0]["title"] == "Beginner Karate Techniques"
        assert result["sources"][0]["url"] == "/articles/doc1"
        assert result["sources"][0]["source_type"] == "article"

        # Verify media
        assert len(result["media"]["videos"]) == 1
        assert result["media"]["videos"][0]["id"] == "video123"
        assert len(result["media"]["images"]) == 1

        # Verify related queries
        assert len(result["related_queries"]) == 3

        # Verify not cached
        assert result["cached"] is False

    def test_embedding_generation(self, search_service, mock_embedding_service):
        """Test embedding generation step"""
        search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        # Verify embedding was generated
        mock_embedding_service.generate_embedding.assert_called_once()
        call_args = mock_embedding_service.generate_embedding.call_args
        assert call_args[1]["text"] == "test query"
        assert call_args[1]["use_cache"] is True

    def test_vector_search_execution(self, search_service, mock_vector_search_service):
        """Test vector search step"""
        search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        # Verify vector search was called
        mock_vector_search_service.search_martial_arts_content.assert_called_once()
        call_args = mock_vector_search_service.search_martial_arts_content.call_args
        assert len(call_args[1]["query_vector"]) == 1536
        assert call_args[1]["top_k"] == 10

    def test_ai_answer_generation(self, search_service, mock_ai_registry_service):
        """Test AI answer generation step"""
        search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        # Verify AI answer was generated
        mock_ai_registry_service.generate_answer.assert_called_once()
        call_args = mock_ai_registry_service.generate_answer.call_args
        assert call_args[1]["query"] == "test query"  # Original query, not normalized
        assert len(call_args[1]["context"]) == 2

    def test_query_logging(self, search_service, mock_zerodb_client):
        """Test query logging step"""
        search_service.search_query(
            query="test query",
            user_id="user123",
            ip_address="192.168.1.1"
        )

        # Verify query was logged
        mock_zerodb_client.create_document.assert_called_once()
        call_args = mock_zerodb_client.create_document.call_args
        assert call_args[1]["collection"] == "search_queries"
        log_data = call_args[1]["data"]
        assert log_data["query"] == "test query"
        assert log_data["user_id"] == "user123"
        assert log_data["ip_hash"] is not None
        assert log_data["success"] is True
        assert log_data["error"] is None


class TestMediaAttachment:
    """Test media attachment logic"""

    def test_attach_videos(self, search_service):
        """Test video attachment"""
        search_results = [
            {
                "data": {
                    "title": "Test Video",
                    "cloudflare_stream_id": "stream123"
                }
            }
        ]

        media = search_service._attach_media(search_results)

        assert len(media["videos"]) == 1
        assert media["videos"][0]["id"] == "stream123"
        assert media["videos"][0]["cloudflare_stream_id"] == "stream123"

    def test_attach_images(self, search_service):
        """Test image attachment"""
        search_results = [
            {
                "data": {
                    "title": "Test Image",
                    "image_url": "https://example.com/image.jpg",
                    "zerodb_object_key": "key123"
                }
            }
        ]

        media = search_service._attach_media(search_results)

        assert len(media["images"]) == 1
        assert media["images"][0]["url"] == "https://example.com/image.jpg"
        assert media["images"][0]["zerodb_object_key"] == "key123"

    def test_media_limit(self, search_service):
        """Test media is limited to 5 items"""
        search_results = [
            {"data": {"cloudflare_stream_id": f"video{i}"}}
            for i in range(10)
        ]

        media = search_service._attach_media(search_results)

        assert len(media["videos"]) == 5  # Limited to 5


class TestErrorHandling:
    """Test error handling"""

    def test_embedding_error(self, search_service, mock_embedding_service):
        """Test handling of embedding generation error"""
        from backend.services.embedding_service import EmbeddingError
        mock_embedding_service.generate_embedding.side_effect = EmbeddingError("API error")

        with pytest.raises(QuerySearchError, match="Failed to generate query embedding"):
            search_service.search_query(
                query="test query",
                user_id=None,
                ip_address="127.0.0.1"
            )

    def test_vector_search_error(self, search_service, mock_vector_search_service):
        """Test handling of vector search error"""
        from backend.services.vector_search_service import VectorSearchError
        mock_vector_search_service.search_martial_arts_content.side_effect = VectorSearchError("Search failed")

        with pytest.raises(QuerySearchError, match="Vector search failed"):
            search_service.search_query(
                query="test query",
                user_id=None,
                ip_address="127.0.0.1"
            )

    def test_ai_error_fallback(self, search_service, mock_ai_registry_service):
        """Test fallback answer when AI fails"""
        from backend.services.ai_registry_service import AIRegistryError
        mock_ai_registry_service.generate_answer.side_effect = AIRegistryError("AI error")

        result = search_service.search_query(
            query="test query",
            user_id=None,
            ip_address="127.0.0.1"
        )

        # Should return fallback answer
        assert "Here are some relevant resources" in result["answer"]

    def test_error_logging(self, search_service, mock_embedding_service, mock_zerodb_client):
        """Test that errors are logged"""
        from backend.services.embedding_service import EmbeddingError
        mock_embedding_service.generate_embedding.side_effect = EmbeddingError("API error")

        try:
            search_service.search_query(
                query="test query",
                user_id=None,
                ip_address="127.0.0.1"
            )
        except QuerySearchError:
            pass

        # Verify error was logged
        mock_zerodb_client.create_document.assert_called_once()
        log_data = mock_zerodb_client.create_document.call_args[1]["data"]
        assert log_data["success"] is False
        assert log_data["error"] is not None


class TestFallbackAnswer:
    """Test fallback answer generation"""

    def test_fallback_with_results(self, search_service):
        """Test fallback answer with search results"""
        search_results = [
            {
                "data": {
                    "title": "Resource 1",
                    "description": "Description 1"
                }
            },
            {
                "data": {
                    "title": "Resource 2",
                    "description": "Description 2"
                }
            }
        ]

        answer = search_service._generate_fallback_answer(search_results)

        assert "Resource 1" in answer
        assert "Resource 2" in answer
        assert "Description 1" in answer

    def test_fallback_without_results(self, search_service):
        """Test fallback answer with no search results"""
        answer = search_service._generate_fallback_answer([])

        assert "couldn't find any relevant information" in answer


class TestSingletonPattern:
    """Test singleton pattern"""

    def test_get_query_search_service_singleton(self):
        """Test that get_query_search_service returns same instance"""
        with patch('backend.services.query_search_service.redis.from_url'):
            service1 = get_query_search_service()
            service2 = get_query_search_service()

            assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
