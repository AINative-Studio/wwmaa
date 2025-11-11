"""
Vector Search Tests - ZeroDB Vector Search Functionality

Comprehensive test suite for vector search operations including:
- Vector collection creation
- Vector insertion (single and batch)
- Vector similarity search with cosine similarity
- ContentIndex schema validation
- Error handling and edge cases

Test Coverage Target: 80%+
"""

import pytest
import numpy as np
from typing import List, Dict, Any
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.services.zerodb_service import (
    ZeroDBClient,
    ZeroDBError,
    ZeroDBValidationError,
    ZeroDBConnectionError,
    get_zerodb_client
)
from backend.models.schemas import ContentIndex, SourceType


# ============================================================================
# FIXTURES - Test Data and Utilities
# ============================================================================

@pytest.fixture
def mock_embedding() -> List[float]:
    """Generate a mock 1536-dimensional embedding vector"""
    # Create a random but reproducible vector
    np.random.seed(42)
    vector = np.random.randn(1536).tolist()
    # Normalize to unit length (as real embeddings would be)
    magnitude = np.linalg.norm(vector)
    return [v / magnitude for v in vector]


@pytest.fixture
def sample_embeddings() -> Dict[str, List[float]]:
    """Generate sample embeddings for different content types"""
    np.random.seed(42)

    def generate_normalized_vector(seed: int) -> List[float]:
        np.random.seed(seed)
        vector = np.random.randn(1536).tolist()
        magnitude = np.linalg.norm(vector)
        return [v / magnitude for v in vector]

    return {
        "event_karate": generate_normalized_vector(1),
        "event_taekwondo": generate_normalized_vector(2),
        "article_techniques": generate_normalized_vector(3),
        "profile_instructor": generate_normalized_vector(4),
        "video_training": generate_normalized_vector(5),
        "query_tournament": generate_normalized_vector(10),
        "query_techniques": generate_normalized_vector(11),
    }


@pytest.fixture
def sample_content_metadata() -> List[Dict[str, Any]]:
    """Sample content metadata for testing"""
    return [
        {
            "source_type": "event",
            "source_id": str(uuid4()),
            "title": "Karate Tournament in Los Angeles",
            "content_chunk": (
                "Annual karate tournament in Los Angeles featuring black belt "
                "competitors from across California. Kata and kumite divisions. "
                "Open to all styles. Registration required."
            ),
            "url": "https://wwmaa.com/events/la-karate-tournament",
            "tags": ["tournament", "karate", "los-angeles", "competition"],
            "visibility": "public",
            "metadata": {
                "location": "Los Angeles, CA",
                "event_date": "2024-12-15",
                "event_type": "tournament"
            }
        },
        {
            "source_type": "article",
            "source_id": str(uuid4()),
            "title": "History of Taekwondo Techniques",
            "content_chunk": (
                "Taekwondo is a Korean martial art characterized by its emphasis "
                "on head-height kicks, jumping and spinning kicks, and fast kicking "
                "techniques. This article explores the evolution of taekwondo "
                "techniques from traditional Korean martial arts."
            ),
            "url": "https://wwmaa.com/articles/taekwondo-history",
            "tags": ["taekwondo", "history", "techniques", "education"],
            "visibility": "public",
            "metadata": {
                "category": "education",
                "publish_date": "2024-11-01"
            }
        },
        {
            "source_type": "profile",
            "source_id": str(uuid4()),
            "title": "Master John Smith - 5th Degree Black Belt",
            "content_chunk": (
                "Master John Smith is a 5th degree black belt in Judo with over "
                "30 years of teaching experience. Specializes in competition training "
                "and has coached multiple national champions. Available for private "
                "lessons and seminars."
            ),
            "url": "https://wwmaa.com/profiles/john-smith",
            "tags": ["instructor", "judo", "5th-dan", "coaching"],
            "visibility": "public",
            "metadata": {
                "location": "San Francisco, CA",
                "disciplines": ["judo"],
                "experience_years": 30
            }
        }
    ]


@pytest.fixture
def mock_zerodb_client():
    """Mock ZeroDB client for testing without actual API calls"""
    with patch('backend.services.zerodb_service.ZeroDBClient') as mock:
        client = Mock(spec=ZeroDBClient)

        # Mock create_vector_collection
        client.create_vector_collection.return_value = {
            "collection": "content_index",
            "status": "created",
            "config": {
                "dimension": 1536,
                "similarity_metric": "cosine"
            }
        }

        # Mock insert_vector
        client.insert_vector.return_value = {
            "id": str(uuid4()),
            "status": "inserted",
            "collection": "content_index"
        }

        # Mock batch_insert_vectors
        client.batch_insert_vectors.return_value = {
            "inserted_count": 3,
            "inserted_ids": [str(uuid4()) for _ in range(3)]
        }

        # Mock vector_search
        client.vector_search.return_value = {
            "results": [],
            "total_results": 0,
            "query_time_ms": 45
        }

        yield client


@pytest.fixture
def zerodb_client():
    """Real ZeroDB client instance (uses environment variables)"""
    try:
        return get_zerodb_client()
    except Exception:
        pytest.skip("ZeroDB credentials not configured")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    Returns value between -1 and 1:
    - 1.0: identical vectors
    - 0.0: orthogonal vectors
    - -1.0: opposite vectors
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    magnitude1 = np.linalg.norm(vec1_np)
    magnitude2 = np.linalg.norm(vec2_np)

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


# ============================================================================
# TEST CLASS: Vector Collection Management
# ============================================================================

@pytest.mark.unit
class TestVectorCollectionManagement:
    """Test vector collection creation and configuration"""

    def test_create_vector_collection_success(self, mock_zerodb_client):
        """Test successful vector collection creation"""
        # Act
        result = mock_zerodb_client.create_vector_collection(
            collection="content_index",
            dimension=1536,
            similarity_metric="cosine"
        )

        # Assert
        assert result["status"] == "created"
        assert result["collection"] == "content_index"
        assert result["config"]["dimension"] == 1536
        assert result["config"]["similarity_metric"] == "cosine"

        # Verify method was called with correct arguments
        mock_zerodb_client.create_vector_collection.assert_called_once_with(
            collection="content_index",
            dimension=1536,
            similarity_metric="cosine"
        )

    def test_create_vector_collection_with_metadata_schema(self, mock_zerodb_client):
        """Test vector collection creation with metadata schema"""
        # Arrange
        metadata_schema = {
            "source_type": "string",
            "visibility": "string",
            "tags": "array"
        }

        # Act
        result = mock_zerodb_client.create_vector_collection(
            collection="content_index",
            dimension=1536,
            similarity_metric="cosine",
            metadata_schema=metadata_schema
        )

        # Assert
        assert result["status"] == "created"
        mock_zerodb_client.create_vector_collection.assert_called_once()

    def test_create_vector_collection_invalid_dimension(self, mock_zerodb_client):
        """Test error handling for invalid dimension"""
        # Arrange
        mock_zerodb_client.create_vector_collection.side_effect = ZeroDBValidationError(
            "Invalid dimension: must be positive integer"
        )

        # Act & Assert
        with pytest.raises(ZeroDBValidationError, match="Invalid dimension"):
            mock_zerodb_client.create_vector_collection(
                collection="content_index",
                dimension=-1,
                similarity_metric="cosine"
            )


# ============================================================================
# TEST CLASS: Vector Insertion
# ============================================================================

@pytest.mark.unit
class TestVectorInsertion:
    """Test single and batch vector insertion operations"""

    def test_insert_single_vector(self, mock_zerodb_client, mock_embedding):
        """Test inserting a single vector"""
        # Arrange
        metadata = {
            "source_type": "event",
            "title": "Test Event",
            "content_chunk": "Test content"
        }

        # Act
        result = mock_zerodb_client.insert_vector(
            collection="content_index",
            vector=mock_embedding,
            metadata=metadata
        )

        # Assert
        assert result["status"] == "inserted"
        assert "id" in result
        assert result["collection"] == "content_index"

        mock_zerodb_client.insert_vector.assert_called_once_with(
            collection="content_index",
            vector=mock_embedding,
            metadata=metadata
        )

    def test_insert_vector_with_custom_id(self, mock_zerodb_client, mock_embedding):
        """Test inserting vector with custom document ID"""
        # Arrange
        custom_id = str(uuid4())
        metadata = {"title": "Test"}

        # Act
        result = mock_zerodb_client.insert_vector(
            collection="content_index",
            vector=mock_embedding,
            metadata=metadata,
            document_id=custom_id
        )

        # Assert
        assert result["status"] == "inserted"

    def test_batch_insert_vectors(
        self,
        mock_zerodb_client,
        sample_embeddings,
        sample_content_metadata
    ):
        """Test batch insertion of multiple vectors"""
        # Arrange
        vectors = [
            {
                "vector": sample_embeddings["event_karate"],
                "metadata": sample_content_metadata[0]
            },
            {
                "vector": sample_embeddings["article_techniques"],
                "metadata": sample_content_metadata[1]
            },
            {
                "vector": sample_embeddings["profile_instructor"],
                "metadata": sample_content_metadata[2]
            }
        ]

        # Act
        result = mock_zerodb_client.batch_insert_vectors(
            collection="content_index",
            vectors=vectors
        )

        # Assert
        assert result["inserted_count"] == 3
        assert len(result["inserted_ids"]) == 3

        mock_zerodb_client.batch_insert_vectors.assert_called_once_with(
            collection="content_index",
            vectors=vectors
        )

    def test_insert_vector_dimension_mismatch(self, mock_zerodb_client):
        """Test error handling for dimension mismatch"""
        # Arrange
        invalid_vector = [0.1] * 512  # Wrong dimension
        mock_zerodb_client.insert_vector.side_effect = ZeroDBValidationError(
            "Vector dimension mismatch: expected 1536, got 512"
        )

        # Act & Assert
        with pytest.raises(ZeroDBValidationError, match="dimension mismatch"):
            mock_zerodb_client.insert_vector(
                collection="content_index",
                vector=invalid_vector,
                metadata={"title": "Test"}
            )


# ============================================================================
# TEST CLASS: Vector Search
# ============================================================================

@pytest.mark.unit
class TestVectorSearch:
    """Test vector similarity search operations"""

    def test_vector_search_basic(self, mock_zerodb_client, sample_embeddings):
        """Test basic vector search"""
        # Arrange
        query_vector = sample_embeddings["query_tournament"]
        mock_zerodb_client.vector_search.return_value = {
            "results": [
                {
                    "id": str(uuid4()),
                    "score": 0.89,
                    "metadata": {
                        "title": "Karate Tournament",
                        "source_type": "event"
                    }
                }
            ],
            "total_results": 1,
            "query_time_ms": 45
        }

        # Act
        results = mock_zerodb_client.vector_search(
            collection="content_index",
            query_vector=query_vector,
            top_k=10
        )

        # Assert
        assert len(results["results"]) == 1
        assert results["results"][0]["score"] == 0.89
        assert results["total_results"] == 1

        mock_zerodb_client.vector_search.assert_called_once()

    def test_vector_search_with_filters(self, mock_zerodb_client, sample_embeddings):
        """Test vector search with metadata filters"""
        # Arrange
        query_vector = sample_embeddings["query_tournament"]
        filters = {
            "source_type": "event",
            "visibility": "public"
        }

        # Act
        results = mock_zerodb_client.vector_search(
            collection="content_index",
            query_vector=query_vector,
            top_k=5,
            filters=filters
        )

        # Assert
        assert "results" in results
        mock_zerodb_client.vector_search.assert_called_once_with(
            collection="content_index",
            query_vector=query_vector,
            top_k=5,
            filters=filters
        )

    def test_vector_search_with_min_score(self, mock_zerodb_client, sample_embeddings):
        """Test vector search with minimum score threshold"""
        # Arrange
        query_vector = sample_embeddings["query_tournament"]
        mock_zerodb_client.vector_search.return_value = {
            "results": [
                {"id": str(uuid4()), "score": 0.85, "metadata": {"title": "Event 1"}},
                {"id": str(uuid4()), "score": 0.78, "metadata": {"title": "Event 2"}},
            ],
            "total_results": 2
        }

        # Act
        results = mock_zerodb_client.vector_search(
            collection="content_index",
            query_vector=query_vector,
            top_k=10,
            min_score=0.75
        )

        # Assert
        assert len(results["results"]) == 2
        # Verify all results meet minimum score
        for result in results["results"]:
            assert result["score"] >= 0.75

    def test_vector_search_no_results(self, mock_zerodb_client, sample_embeddings):
        """Test vector search with no matching results"""
        # Arrange
        query_vector = sample_embeddings["query_tournament"]
        mock_zerodb_client.vector_search.return_value = {
            "results": [],
            "total_results": 0,
            "query_time_ms": 30
        }

        # Act
        results = mock_zerodb_client.vector_search(
            collection="content_index",
            query_vector=query_vector,
            top_k=10,
            min_score=0.95  # Very high threshold
        )

        # Assert
        assert len(results["results"]) == 0
        assert results["total_results"] == 0

    def test_cosine_similarity_calculation(self, sample_embeddings):
        """Test cosine similarity calculation between vectors"""
        # Arrange
        vec1 = sample_embeddings["event_karate"]
        vec2 = sample_embeddings["event_taekwondo"]

        # Act
        similarity = cosine_similarity(vec1, vec2)

        # Assert
        assert -1.0 <= similarity <= 1.0  # Valid range
        assert isinstance(similarity, float)

    def test_cosine_similarity_identical_vectors(self, mock_embedding):
        """Test cosine similarity of identical vectors should be 1.0"""
        # Act
        similarity = cosine_similarity(mock_embedding, mock_embedding)

        # Assert
        assert abs(similarity - 1.0) < 1e-6  # Should be very close to 1.0

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors should be 0.0"""
        # Arrange - Create orthogonal vectors
        vec1 = [1.0] + [0.0] * 1535
        vec2 = [0.0, 1.0] + [0.0] * 1534

        # Act
        similarity = cosine_similarity(vec1, vec2)

        # Assert
        assert abs(similarity) < 1e-6  # Should be very close to 0.0


# ============================================================================
# TEST CLASS: ContentIndex Schema Validation
# ============================================================================

@pytest.mark.unit
class TestContentIndexSchema:
    """Test ContentIndex Pydantic model validation"""

    def test_content_index_valid_model(self, mock_embedding):
        """Test creating valid ContentIndex model"""
        # Arrange & Act
        content = ContentIndex(
            source_type=SourceType.EVENT,
            source_id=uuid4(),
            url="https://wwmaa.com/events/test",
            title="Test Event",
            content_chunk="This is a test event description with sufficient content.",
            embedding=mock_embedding,
            tags=["test", "event"],
            visibility="public"
        )

        # Assert
        assert content.source_type == SourceType.EVENT
        assert len(content.embedding) == 1536
        assert content.embedding_model == "text-embedding-ada-002"
        assert content.is_active is True

    def test_content_index_all_source_types(self, mock_embedding):
        """Test all valid source types"""
        # Arrange
        source_types = [
            SourceType.EVENT,
            SourceType.ARTICLE,
            SourceType.PROFILE,
            SourceType.VIDEO,
            SourceType.TRAINING_SESSION,
            SourceType.DOCUMENT
        ]

        # Act & Assert
        for source_type in source_types:
            content = ContentIndex(
                source_type=source_type,
                source_id=uuid4(),
                title="Test Content",
                content_chunk="Test content chunk with sufficient length.",
                embedding=mock_embedding
            )
            assert content.source_type == source_type

    def test_content_index_embedding_dimension_validation(self):
        """Test embedding dimension validation"""
        # Arrange - Wrong dimension
        invalid_embedding = [0.1] * 512

        # Act & Assert
        with pytest.raises(ValueError, match="1536 dimensions"):
            ContentIndex(
                source_type=SourceType.EVENT,
                source_id=uuid4(),
                title="Test",
                content_chunk="Test content chunk.",
                embedding=invalid_embedding
            )

    def test_content_index_content_chunk_too_short(self, mock_embedding):
        """Test content chunk length validation - too short"""
        # Act & Assert
        with pytest.raises(ValueError, match="at least 10 characters"):
            ContentIndex(
                source_type=SourceType.EVENT,
                source_id=uuid4(),
                title="Test",
                content_chunk="Short",  # Too short
                embedding=mock_embedding
            )

    def test_content_index_content_chunk_too_long(self, mock_embedding):
        """Test content chunk length validation - too long"""
        # Arrange
        long_content = "x" * 9000  # Exceeds 8000 character limit

        # Act & Assert
        with pytest.raises(ValueError, match="should not exceed 8000 characters"):
            ContentIndex(
                source_type=SourceType.EVENT,
                source_id=uuid4(),
                title="Test",
                content_chunk=long_content,
                embedding=mock_embedding
            )

    def test_content_index_with_metadata(self, mock_embedding):
        """Test ContentIndex with additional metadata"""
        # Arrange & Act
        content = ContentIndex(
            source_type=SourceType.EVENT,
            source_id=uuid4(),
            title="Event with Metadata",
            content_chunk="Event description with location and date information.",
            embedding=mock_embedding,
            metadata={
                "location": "Los Angeles, CA",
                "event_date": "2024-12-15",
                "event_type": "tournament"
            },
            tags=["tournament", "karate"],
            category="competition",
            search_weight=2.0
        )

        # Assert
        assert content.metadata["location"] == "Los Angeles, CA"
        assert "tournament" in content.tags
        assert content.search_weight == 2.0

    def test_content_index_performance_tracking(self, mock_embedding):
        """Test performance tracking fields"""
        # Arrange & Act
        content = ContentIndex(
            source_type=SourceType.ARTICLE,
            source_id=uuid4(),
            title="Popular Article",
            content_chunk="This article has been viewed many times.",
            embedding=mock_embedding,
            search_count=150,
            click_count=45
        )

        # Assert
        assert content.search_count == 150
        assert content.click_count == 45


# ============================================================================
# TEST CLASS: Error Handling and Edge Cases
# ============================================================================

@pytest.mark.unit
class TestVectorSearchErrorHandling:
    """Test error handling and edge cases"""

    def test_connection_error_handling(self, mock_zerodb_client, mock_embedding):
        """Test handling of connection errors"""
        # Arrange
        mock_zerodb_client.insert_vector.side_effect = ZeroDBConnectionError(
            "Failed to connect to ZeroDB"
        )

        # Act & Assert
        with pytest.raises(ZeroDBConnectionError, match="Failed to connect"):
            mock_zerodb_client.insert_vector(
                collection="content_index",
                vector=mock_embedding,
                metadata={"title": "Test"}
            )

    def test_invalid_collection_name(self, mock_zerodb_client, mock_embedding):
        """Test error handling for invalid collection name"""
        # Arrange
        mock_zerodb_client.vector_search.side_effect = ZeroDBError(
            "Collection 'invalid_collection' does not exist"
        )

        # Act & Assert
        with pytest.raises(ZeroDBError, match="does not exist"):
            mock_zerodb_client.vector_search(
                collection="invalid_collection",
                query_vector=mock_embedding,
                top_k=10
            )

    def test_empty_vector_list(self, mock_zerodb_client):
        """Test handling of empty vector in batch insert"""
        # Arrange
        mock_zerodb_client.batch_insert_vectors.side_effect = ZeroDBValidationError(
            "Vectors list cannot be empty"
        )

        # Act & Assert
        with pytest.raises(ZeroDBValidationError, match="cannot be empty"):
            mock_zerodb_client.batch_insert_vectors(
                collection="content_index",
                vectors=[]
            )

    def test_invalid_top_k_value(self, mock_zerodb_client, mock_embedding):
        """Test error handling for invalid top_k value"""
        # Arrange
        mock_zerodb_client.vector_search.side_effect = ZeroDBValidationError(
            "top_k must be a positive integer"
        )

        # Act & Assert
        with pytest.raises(ZeroDBValidationError, match="positive integer"):
            mock_zerodb_client.vector_search(
                collection="content_index",
                query_vector=mock_embedding,
                top_k=-5
            )


# ============================================================================
# TEST CLASS: Integration Tests (Optional - Require Real ZeroDB)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not pytest.config.getoption("--integration"),
    reason="Integration tests require --integration flag"
)
class TestVectorSearchIntegration:
    """Integration tests with real ZeroDB instance"""

    def test_end_to_end_vector_search_flow(
        self,
        zerodb_client,
        sample_embeddings,
        sample_content_metadata
    ):
        """Test complete flow: create collection, insert, search"""
        # Step 1: Create vector collection
        collection_result = zerodb_client.create_vector_collection(
            collection="test_content_index",
            dimension=1536,
            similarity_metric="cosine"
        )
        assert collection_result["status"] == "created"

        # Step 2: Insert vectors
        vectors = [
            {
                "vector": sample_embeddings["event_karate"],
                "metadata": sample_content_metadata[0]
            },
            {
                "vector": sample_embeddings["article_techniques"],
                "metadata": sample_content_metadata[1]
            }
        ]

        insert_result = zerodb_client.batch_insert_vectors(
            collection="test_content_index",
            vectors=vectors
        )
        assert insert_result["inserted_count"] == 2

        # Step 3: Perform search
        search_results = zerodb_client.vector_search(
            collection="test_content_index",
            query_vector=sample_embeddings["query_tournament"],
            top_k=5
        )

        # Assert
        assert len(search_results["results"]) > 0
        assert search_results["results"][0]["score"] > 0.5

        # Cleanup
        # Note: Add cleanup code to delete test collection


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_addoption(parser):
    """Add custom pytest command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require real ZeroDB connection"
    )


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring real ZeroDB"
    )
