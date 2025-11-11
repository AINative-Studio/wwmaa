"""
Comprehensive Test Suite for Content Indexing Service

Tests cover:
- Text chunking functionality
- Content extraction from different content types
- OpenAI embedding generation (mocked)
- Incremental indexing logic
- Error handling and retries
- Indexing statistics and status
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from typing import List, Dict, Any

from backend.services.indexing_service import (
    IndexingService,
    ContentType,
    IndexingStatus,
    get_indexing_service
)
from backend.utils.text_chunking import (
    TextChunker,
    chunk_text,
    count_tokens,
    get_text_chunker
)


# ============================================================================
# Text Chunking Tests
# ============================================================================


class TestTextChunking:
    """Test suite for text chunking utility"""

    def test_count_tokens_basic(self):
        """Test basic token counting"""
        text = "Hello, world! This is a test."
        token_count = count_tokens(text)

        assert isinstance(token_count, int)
        assert token_count > 0

    def test_count_tokens_empty(self):
        """Test token counting with empty text"""
        assert count_tokens("") == 0
        # Whitespace may still have tokens in some tokenizers
        assert count_tokens("   ") >= 0

    def test_chunk_small_text(self):
        """Test chunking text that fits in one chunk"""
        text = "This is a small piece of text."
        chunks = chunk_text(text, max_tokens=500)

        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["total_chunks"] == 1

    def test_chunk_long_text(self):
        """Test chunking long text into multiple chunks"""
        # Create a long text that will require multiple chunks
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(200)])

        chunks = chunk_text(long_text, max_tokens=100, overlap=20)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Verify chunk structure
        for i, chunk in enumerate(chunks):
            assert "text" in chunk
            assert "tokens" in chunk
            assert "chunk_index" in chunk
            assert "total_chunks" in chunk
            assert chunk["chunk_index"] == i
            assert chunk["total_chunks"] == len(chunks)
            assert chunk["tokens"] <= 100

    def test_chunk_with_metadata(self):
        """Test chunking with metadata propagation"""
        text = "This is a test text."
        metadata = {"doc_id": "123", "type": "article"}

        chunks = chunk_text(text, metadata=metadata)

        assert len(chunks) == 1
        assert chunks[0]["metadata"] == metadata

    def test_chunk_preserves_sentence_boundaries(self):
        """Test that chunking preserves sentence boundaries when possible"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunk_text(text, max_tokens=20)

        # Each chunk should contain complete sentences
        for chunk in chunks:
            chunk_text_val = chunk["text"]
            # Should not start mid-sentence (after first chunk)
            if chunk["chunk_index"] > 0:
                assert chunk_text_val[0].isupper() or chunk_text_val.startswith("  ")

    def test_text_chunker_singleton(self):
        """Test that get_text_chunker returns singleton instance"""
        chunker1 = get_text_chunker()
        chunker2 = get_text_chunker()

        assert chunker1 is chunker2


# ============================================================================
# Indexing Service Tests
# ============================================================================


class TestIndexingService:
    """Test suite for IndexingService"""

    @pytest.fixture
    def mock_zerodb(self):
        """Mock ZeroDB client"""
        with patch("backend.services.indexing_service.get_zerodb_client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client"""
        with patch("backend.services.indexing_service.OpenAI") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def indexing_service(self, mock_zerodb, mock_openai):
        """Create IndexingService instance with mocked dependencies"""
        service = IndexingService()
        return service

    def test_service_initialization(self, indexing_service):
        """Test service initialization"""
        assert indexing_service is not None
        assert indexing_service._status == IndexingStatus.IDLE
        assert indexing_service._stats["total_indexed"] == 0

    def test_get_status(self, indexing_service):
        """Test getting indexing status"""
        status = indexing_service.get_status()

        assert "status" in status
        assert "current_operation" in status
        assert "stats" in status
        assert status["status"] == IndexingStatus.IDLE.value

    def test_extract_content_text_events(self, indexing_service):
        """Test content extraction for events"""
        document = {
            "id": "event-123",
            "data": {
                "title": "Martial Arts Workshop",
                "description": "Learn advanced techniques",
                "location": "New York, NY",
                "event_date": "2025-01-15"
            }
        }

        text, metadata = indexing_service.extract_content_text(
            ContentType.EVENTS,
            document
        )

        assert "Martial Arts Workshop" in text
        assert "Learn advanced techniques" in text
        assert "Location: New York, NY" in text
        assert metadata["content_type"] == ContentType.EVENTS.value
        assert metadata["document_id"] == "event-123"
        assert metadata["title"] == "Martial Arts Workshop"

    def test_extract_content_text_articles(self, indexing_service):
        """Test content extraction for articles"""
        document = {
            "id": "article-456",
            "data": {
                "title": "The History of Karate",
                "content": "Karate is a martial art that originated in Okinawa...",
                "keywords": ["karate", "history", "martial arts"],
                "author": "Jane Doe"
            }
        }

        text, metadata = indexing_service.extract_content_text(
            ContentType.ARTICLES,
            document
        )

        assert "The History of Karate" in text
        assert "Karate is a martial art" in text
        assert "Keywords: karate, history, martial arts" in text
        assert metadata["content_type"] == ContentType.ARTICLES.value
        assert metadata["keywords"] == ["karate", "history", "martial arts"]

    def test_extract_content_text_training_videos(self, indexing_service):
        """Test content extraction for training videos"""
        document = {
            "id": "video-789",
            "data": {
                "title": "Basic Kata Tutorial",
                "description": "Learn the fundamentals",
                "transcript": "Welcome to this kata tutorial...",
                "instructor": "Master Smith"
            }
        }

        text, metadata = indexing_service.extract_content_text(
            ContentType.TRAINING_VIDEOS,
            document
        )

        assert "Basic Kata Tutorial" in text
        assert "Learn the fundamentals" in text
        assert "Welcome to this kata tutorial" in text
        assert metadata["instructor"] == "Master Smith"

    def test_extract_content_text_member_profiles(self, indexing_service):
        """Test content extraction for member profiles"""
        document = {
            "id": "member-101",
            "data": {
                "name": "John Doe",
                "bio": "5th degree black belt in Karate",
                "discipline": "Karate",
                "location": "California"
            }
        }

        text, metadata = indexing_service.extract_content_text(
            ContentType.MEMBER_PROFILES,
            document
        )

        assert "John Doe" in text
        assert "5th degree black belt" in text
        assert "Discipline: Karate" in text
        assert metadata["discipline"] == "Karate"

    def test_generate_embeddings_success(self, indexing_service, mock_openai):
        """Test successful embedding generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3]),
            Mock(embedding=[0.4, 0.5, 0.6])
        ]
        indexing_service.openai_client.embeddings.create.return_value = mock_response

        texts = ["First text", "Second text"]
        embeddings = indexing_service.generate_embeddings(texts)

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]

    def test_generate_embeddings_empty_list(self, indexing_service):
        """Test embedding generation with empty list"""
        embeddings = indexing_service.generate_embeddings([])
        assert embeddings == []

    @patch("backend.services.indexing_service.time.sleep")
    def test_generate_embeddings_retry_on_rate_limit(
        self,
        mock_sleep,
        indexing_service,
        mock_openai
    ):
        """Test retry logic on rate limit errors"""
        from openai import RateLimitError

        # First call raises rate limit, second succeeds
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]

        indexing_service.openai_client.embeddings.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=Mock(status_code=429), body=None),
            mock_response
        ]

        texts = ["Test text"]
        embeddings = indexing_service.generate_embeddings(texts, retry_count=2)

        assert len(embeddings) == 1
        assert mock_sleep.called

    def test_index_document_success(self, indexing_service, mock_zerodb, mock_openai):
        """Test successful document indexing"""
        # Setup mocks
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        indexing_service.openai_client.embeddings.create.return_value = mock_response

        mock_zerodb.create_document.return_value = {"id": "chunk-1"}
        mock_zerodb.query_documents.return_value = {"documents": []}

        document = {
            "id": "doc-1",
            "data": {
                "title": "Test Article",
                "content": "This is test content.",
                "keywords": ["test"]
            }
        }

        result = indexing_service.index_document(
            ContentType.ARTICLES,
            document
        )

        assert result["success"] is True
        assert result["document_id"] == "doc-1"
        assert result["chunks_indexed"] > 0

    def test_index_document_missing_id(self, indexing_service):
        """Test indexing document without ID"""
        document = {"data": {"title": "Test"}}

        result = indexing_service.index_document(
            ContentType.ARTICLES,
            document
        )

        assert result["success"] is False
        assert "Missing document ID" in result["error"]

    def test_index_document_no_content(self, indexing_service):
        """Test indexing document with no extractable content"""
        document = {
            "id": "doc-1",
            "data": {}
        }

        result = indexing_service.index_document(
            ContentType.ARTICLES,
            document
        )

        assert result["success"] is False

    def test_index_document_incremental_skip(self, indexing_service, mock_zerodb):
        """Test incremental indexing skips already-indexed documents"""
        # Mock existing metadata
        mock_zerodb.query_documents.return_value = {
            "documents": [{
                "data": {
                    "indexed_at": datetime.now(timezone.utc).isoformat()
                }
            }]
        }

        document = {
            "id": "doc-1",
            "data": {
                "title": "Test",
                "content": "Content",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        }

        result = indexing_service.index_document(
            ContentType.ARTICLES,
            document,
            force=False
        )

        assert result.get("skipped") is True

    def test_index_collection_success(self, indexing_service, mock_zerodb, mock_openai):
        """Test indexing entire collection"""
        # Mock documents
        mock_zerodb.query_documents.return_value = {
            "documents": [
                {
                    "id": "doc-1",
                    "data": {"title": "Article 1", "content": "Content 1", "keywords": []}
                },
                {
                    "id": "doc-2",
                    "data": {"title": "Article 2", "content": "Content 2", "keywords": []}
                }
            ]
        }

        # Mock embeddings
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        indexing_service.openai_client.embeddings.create.return_value = mock_response

        mock_zerodb.create_document.return_value = {"id": "chunk-1"}

        result = indexing_service.index_collection(
            ContentType.ARTICLES,
            incremental=False,
            limit=10
        )

        assert result["content_type"] == ContentType.ARTICLES.value
        assert result["total_documents"] == 2
        assert result["indexed"] > 0
        assert indexing_service._status == IndexingStatus.COMPLETED

    def test_get_stats(self, indexing_service, mock_zerodb):
        """Test getting indexing statistics"""
        # Mock metadata documents
        mock_zerodb.query_documents.return_value = {
            "documents": [
                {
                    "data": {
                        "content_type": "articles",
                        "chunk_count": 5,
                        "indexed_at": "2025-01-01T00:00:00Z"
                    }
                },
                {
                    "data": {
                        "content_type": "events",
                        "chunk_count": 3,
                        "indexed_at": "2025-01-02T00:00:00Z"
                    }
                }
            ]
        }

        stats = indexing_service.get_stats()

        assert "total_documents_indexed" in stats
        assert "total_chunks" in stats
        assert "by_content_type" in stats
        assert stats["total_documents_indexed"] == 2
        assert stats["total_chunks"] == 8


# ============================================================================
# Integration Tests
# ============================================================================


class TestIndexingIntegration:
    """Integration tests for indexing workflow"""

    @patch("backend.services.indexing_service.get_zerodb_client")
    @patch("backend.services.indexing_service.OpenAI")
    def test_full_indexing_workflow(self, mock_openai_class, mock_zerodb_func):
        """Test complete indexing workflow from document to stored chunks"""
        # Setup mocks
        mock_zerodb = Mock()
        mock_zerodb_func.return_value = mock_zerodb

        mock_openai = Mock()
        mock_openai_class.return_value = mock_openai

        # Mock embeddings response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai.embeddings.create.return_value = mock_response

        # Mock ZeroDB responses
        mock_zerodb.query_documents.return_value = {"documents": []}
        mock_zerodb.create_document.return_value = {"id": "chunk-1"}

        # Create service and index document
        service = IndexingService()

        document = {
            "id": "test-doc",
            "data": {
                "title": "Test Article",
                "content": "This is a test article with some content.",
                "keywords": ["test", "article"]
            }
        }

        result = service.index_document(ContentType.ARTICLES, document)

        # Verify successful indexing
        assert result["success"] is True
        assert mock_zerodb.create_document.called

        # Verify embedding was generated
        assert mock_openai.embeddings.create.called


# ============================================================================
# Singleton Tests
# ============================================================================


def test_get_indexing_service_singleton():
    """Test that get_indexing_service returns singleton instance"""
    with patch("backend.services.indexing_service.get_zerodb_client"), \
         patch("backend.services.indexing_service.OpenAI"):

        service1 = get_indexing_service()
        service2 = get_indexing_service()

        assert service1 is service2


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def indexing_service(self):
        """Create service with mocked dependencies"""
        with patch("backend.services.indexing_service.get_zerodb_client"), \
             patch("backend.services.indexing_service.OpenAI"):
            return IndexingService()

    def test_extract_content_unsupported_type(self, indexing_service):
        """Test extraction with unsupported content type"""
        document = {"id": "test", "data": {"title": "Test"}}

        # Create a fake content type (this will raise ValueError)
        with pytest.raises(ValueError):
            # Directly call with invalid string (not enum)
            indexing_service.extract_content_text("invalid_type", document)

    def test_chunking_with_very_long_sentence(self):
        """Test chunking handles very long sentences that exceed max_tokens"""
        # Create a very long sentence
        long_sentence = " ".join(["word"] * 1000) + "."

        chunks = chunk_text(long_sentence, max_tokens=100)

        # Should split even a single sentence if too long
        assert len(chunks) > 1

        # Each chunk should be within token limit
        for chunk in chunks:
            assert chunk["tokens"] <= 100
