"""
Integration Test for Complete Search Pipeline

Tests the full end-to-end search functionality:
1. Query normalization
2. Cache check
3. OpenAI embedding generation
4. ZeroDB vector search
5. AI Registry answer generation
6. Media attachment
7. Related queries
8. Caching
9. Query logging

Run with: pytest backend/tests/test_search_pipeline_integration.py -v
"""

import pytest
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.services.query_search_service import QuerySearchService, QuerySearchError
from backend.services.embedding_service import EmbeddingService, EmbeddingError
from backend.services.vector_search_service import VectorSearchService, VectorSearchError
from backend.services.ai_registry_service import AIRegistryService, AIRegistryError
from backend.services.zerodb_service import ZeroDBClient, ZeroDBError


@pytest.mark.integration
class TestSearchPipelineIntegration:
    """Integration tests for complete search pipeline"""

    @pytest.fixture(autouse=True)
    def check_environment(self):
        """Verify required environment variables are set"""
        required_vars = [
            'OPENAI_API_KEY',
            'ZERODB_API_KEY',
            'ZERODB_API_BASE_URL',
            'REDIS_URL',
            'AINATIVE_API_KEY'
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            pytest.skip(f"Missing environment variables: {', '.join(missing_vars)}")

    def test_embedding_service_initialization(self):
        """Test that embedding service initializes correctly"""
        try:
            service = EmbeddingService()
            assert service is not None
            assert service.model == "text-embedding-3-small"
            assert service.cache_ttl == 86400
            print("✅ EmbeddingService initialized successfully")
        except Exception as e:
            pytest.fail(f"❌ EmbeddingService initialization failed: {e}")

    def test_embedding_generation(self):
        """Test that OpenAI embeddings can be generated"""
        try:
            service = EmbeddingService()

            # Test with a simple query
            query = "what are the best martial arts techniques for beginners?"
            embedding = service.generate_embedding(query, use_cache=False)

            # Verify embedding properties
            assert embedding is not None
            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # text-embedding-3-small dimension
            assert all(isinstance(v, float) for v in embedding)

            print(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
            print(f"   First 5 values: {embedding[:5]}")

        except EmbeddingError as e:
            pytest.fail(f"❌ Embedding generation failed: {e}")
        except Exception as e:
            pytest.fail(f"❌ Unexpected error: {e}")

    def test_zerodb_client_initialization(self):
        """Test that ZeroDB client initializes correctly"""
        try:
            client = ZeroDBClient()
            assert client is not None
            assert client.base_url
            assert client.project_id
            print("✅ ZeroDBClient initialized successfully")
            print(f"   Base URL: {client.base_url}")
            print(f"   Project ID: {client.project_id}")
        except ZeroDBError as e:
            pytest.fail(f"❌ ZeroDBClient initialization failed: {e}")

    def test_vector_search_service_initialization(self):
        """Test that vector search service initializes correctly"""
        try:
            service = VectorSearchService()
            assert service is not None
            assert service.db_client is not None
            print("✅ VectorSearchService initialized successfully")
        except Exception as e:
            pytest.fail(f"❌ VectorSearchService initialization failed: {e}")

    def test_ai_registry_service_initialization(self):
        """Test that AI Registry service initializes correctly"""
        try:
            service = AIRegistryService()
            assert service is not None
            assert service.api_key
            assert service.base_url
            print("✅ AIRegistryService initialized successfully")
            print(f"   Base URL: {service.base_url}")
            print(f"   Primary model: {service.primary_model}")
        except AIRegistryError as e:
            pytest.fail(f"❌ AIRegistryService initialization failed: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_TESTS') == 'true',
        reason="Skipping live API tests"
    )
    def test_end_to_end_search_query(self):
        """Test complete search query from end to end"""
        try:
            # Initialize search service
            service = QuerySearchService()

            # Execute search query
            query = "What are good martial arts techniques for self defense?"

            print(f"\n🔍 Testing search query: '{query}'")

            result = service.search_query(
                query=query,
                user_id=None,
                ip_address="127.0.0.1",
                bypass_cache=True  # Force fresh search
            )

            # Verify response structure
            assert result is not None
            assert 'answer' in result
            assert 'sources' in result
            assert 'media' in result
            assert 'related_queries' in result
            assert 'latency_ms' in result
            assert 'cached' in result

            # Verify answer
            assert isinstance(result['answer'], str)
            assert len(result['answer']) > 0
            print(f"\n✅ Answer generated ({len(result['answer'])} characters):")
            print(f"   {result['answer'][:200]}...")

            # Verify sources
            assert isinstance(result['sources'], list)
            print(f"\n✅ Sources returned: {len(result['sources'])} items")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"   {i}. {source.get('title', 'N/A')} ({source.get('source_type', 'N/A')})")

            # Verify media
            assert isinstance(result['media'], dict)
            assert 'videos' in result['media']
            assert 'images' in result['media']
            print(f"\n✅ Media attached:")
            print(f"   Videos: {len(result['media']['videos'])}")
            print(f"   Images: {len(result['media']['images'])}")

            # Verify related queries
            assert isinstance(result['related_queries'], list)
            print(f"\n✅ Related queries: {len(result['related_queries'])}")
            for i, rq in enumerate(result['related_queries'], 1):
                print(f"   {i}. {rq}")

            # Verify latency
            assert isinstance(result['latency_ms'], int)
            assert result['latency_ms'] > 0
            print(f"\n✅ Query completed in {result['latency_ms']}ms")

            # Verify cached flag
            assert isinstance(result['cached'], bool)
            assert result['cached'] == False  # Should be False since we bypassed cache
            print(f"✅ Cache status: {result['cached']}")

            print("\n✅ END-TO-END SEARCH TEST PASSED")

        except QuerySearchError as e:
            pytest.fail(f"❌ Search query failed: {e}")
        except Exception as e:
            pytest.fail(f"❌ Unexpected error during search: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_TESTS') == 'true',
        reason="Skipping live API tests"
    )
    def test_search_caching(self):
        """Test that search results are cached correctly"""
        try:
            service = QuerySearchService()
            query = "best martial arts for women"

            # First query - should NOT be cached
            print(f"\n🔍 First query: '{query}'")
            result1 = service.search_query(
                query=query,
                bypass_cache=False
            )
            assert result1['cached'] == False
            latency1 = result1['latency_ms']
            print(f"✅ First query completed in {latency1}ms (not cached)")

            # Second query - SHOULD be cached
            print(f"\n🔍 Second query (same): '{query}'")
            result2 = service.search_query(
                query=query,
                bypass_cache=False
            )
            assert result2['cached'] == True
            latency2 = result2['latency_ms']
            print(f"✅ Second query completed in {latency2}ms (cached)")

            # Verify cached result is faster
            assert latency2 < latency1
            print(f"✅ Cache improved latency by {latency1 - latency2}ms ({((latency1 - latency2) / latency1 * 100):.1f}%)")

            # Verify answers are identical
            assert result1['answer'] == result2['answer']
            print("✅ Cached answer matches original")

        except Exception as e:
            pytest.fail(f"❌ Caching test failed: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_TESTS') == 'true',
        reason="Skipping live API tests"
    )
    def test_search_error_handling(self):
        """Test that search handles errors gracefully"""
        try:
            service = QuerySearchService()

            # Test empty query
            with pytest.raises(QuerySearchError, match="Query cannot be empty"):
                service.search_query("")
            print("✅ Empty query error handled correctly")

            # Test whitespace-only query
            with pytest.raises(QuerySearchError, match="Query cannot be empty"):
                service.search_query("   ")
            print("✅ Whitespace-only query error handled correctly")

            # Test too-long query
            long_query = "a" * 501
            with pytest.raises(QuerySearchError, match="exceeds maximum length"):
                service.search_query(long_query)
            print("✅ Too-long query error handled correctly")

        except Exception as e:
            pytest.fail(f"❌ Error handling test failed: {e}")


@pytest.mark.integration
class TestSearchComponentsIndividually:
    """Test individual search components"""

    def test_embedding_caching(self):
        """Test that embeddings are cached"""
        try:
            service = EmbeddingService()
            query = "karate techniques for beginners"

            # First generation - should hit OpenAI API
            embedding1 = service.generate_embedding(query, use_cache=True)

            # Second generation - should use cache
            embedding2 = service.generate_embedding(query, use_cache=True)

            # Verify embeddings are identical
            assert embedding1 == embedding2
            print("✅ Embedding caching works correctly")

        except Exception as e:
            pytest.fail(f"❌ Embedding caching test failed: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_TESTS') == 'true',
        reason="Skipping live API tests"
    )
    def test_ai_registry_answer_generation(self):
        """Test AI Registry answer generation in isolation"""
        try:
            service = AIRegistryService()

            # Mock context
            context = [
                {
                    "id": "doc1",
                    "data": {
                        "title": "Karate Basics",
                        "description": "Learn fundamental karate techniques including blocks, strikes, and stances."
                    },
                    "source_collection": "articles",
                    "score": 0.95
                }
            ]

            query = "What are basic karate techniques?"

            result = service.generate_answer(
                query=query,
                context=context,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=500
            )

            # Verify response structure
            assert 'answer' in result
            assert 'model' in result
            assert 'tokens_used' in result
            assert 'latency_ms' in result

            assert len(result['answer']) > 0
            assert result['model'] == "gpt-4o-mini"
            assert result['tokens_used'] > 0
            assert result['latency_ms'] > 0

            print(f"✅ AI answer generated successfully")
            print(f"   Model: {result['model']}")
            print(f"   Tokens: {result['tokens_used']}")
            print(f"   Latency: {result['latency_ms']}ms")
            print(f"   Answer length: {len(result['answer'])} characters")

        except AIRegistryError as e:
            pytest.fail(f"❌ AI answer generation failed: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_TESTS') == 'true',
        reason="Skipping live API tests"
    )
    def test_related_queries_generation(self):
        """Test related queries generation"""
        try:
            service = AIRegistryService()

            query = "martial arts for beginners"
            related = service.generate_related_queries(query, count=3)

            assert isinstance(related, list)
            assert len(related) <= 3

            print(f"✅ Related queries generated:")
            for i, rq in enumerate(related, 1):
                print(f"   {i}. {rq}")
                assert isinstance(rq, str)
                assert len(rq) > 0

        except Exception as e:
            pytest.fail(f"❌ Related queries generation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
