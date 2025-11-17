#!/usr/bin/env python3
"""
Search Pipeline Diagnostic Script

Tests each component of the search pipeline to identify issues.
Run with: python scripts/test_search_pipeline.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_section(text):
    """Print a formatted section"""
    print(f"\n{'─'*80}")
    print(f"  {text}")
    print(f"{'─'*80}\n")

def check_environment():
    """Check required environment variables"""
    print_section("1. Environment Variables Check")

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API for embeddings',
        'ZERODB_API_KEY': 'ZeroDB API for vector search and storage',
        'ZERODB_API_BASE_URL': 'ZeroDB API endpoint',
        'ZERODB_PROJECT_ID': 'ZeroDB project ID',
        'REDIS_URL': 'Redis for caching',
        'AINATIVE_API_KEY': 'AINative AI Registry for LLM answers',
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask API keys
            if 'KEY' in var or 'PASSWORD' in var:
                masked = value[:8] + '...' if len(value) > 8 else '***'
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            all_set = False

    return all_set

def test_embedding_service():
    """Test embedding service"""
    print_section("2. Embedding Service Test (OpenAI)")

    try:
        from backend.services.embedding_service import EmbeddingService

        service = EmbeddingService()
        print(f"✅ EmbeddingService initialized")
        print(f"   Model: {service.model}")
        print(f"   Cache TTL: {service.cache_ttl}s")

        # Test embedding generation
        test_query = "martial arts techniques for beginners"
        print(f"\n   Generating embedding for: '{test_query}'")

        embedding = service.generate_embedding(test_query, use_cache=False)

        print(f"✅ Embedding generated successfully")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Data type: {type(embedding[0])}")

        return True

    except Exception as e:
        print(f"❌ Embedding service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zerodb_client():
    """Test ZeroDB client"""
    print_section("3. ZeroDB Client Test")

    try:
        from backend.services.zerodb_service import ZeroDBClient

        client = ZeroDBClient()
        print(f"✅ ZeroDBClient initialized")
        print(f"   Base URL: {client.base_url}")
        print(f"   Project ID: {client.project_id}")

        # Test listing tables
        try:
            tables = client.list_tables()
            print(f"✅ ZeroDB connection verified")
            print(f"   Tables in project: {len(tables.get('tables', []))}")
            if tables.get('tables'):
                for table in tables['tables'][:5]:
                    print(f"     - {table.get('table_name', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Could not list tables: {e}")

        return True

    except Exception as e:
        print(f"❌ ZeroDB client failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_search_service():
    """Test vector search service"""
    print_section("4. Vector Search Service Test")

    try:
        from backend.services.vector_search_service import VectorSearchService

        service = VectorSearchService()
        print(f"✅ VectorSearchService initialized")

        # Note: We can't test actual vector search without seeded data
        print("   ℹ️  Vector search requires seeded data in ZeroDB collections")
        print("   Collections needed: events, articles, profiles, techniques")

        return True

    except Exception as e:
        print(f"❌ Vector search service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_registry_service():
    """Test AI Registry service"""
    print_section("5. AI Registry Service Test (AINative)")

    try:
        from backend.services.ai_registry_service import AIRegistryService

        service = AIRegistryService()
        print(f"✅ AIRegistryService initialized")
        print(f"   Base URL: {service.base_url}")
        print(f"   Primary model: {service.primary_model}")
        print(f"   Fallback model: {service.fallback_model}")

        # Test answer generation with mock context
        print(f"\n   Testing answer generation...")
        context = [
            {
                "id": "test1",
                "data": {
                    "title": "Karate Fundamentals",
                    "description": "Learn basic karate stances, blocks, and strikes for beginners."
                },
                "source_collection": "articles",
                "score": 0.95
            }
        ]

        result = service.generate_answer(
            query="What are basic karate techniques?",
            context=context,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=200
        )

        print(f"✅ Answer generated successfully")
        print(f"   Model used: {result['model']}")
        print(f"   Tokens used: {result['tokens_used']}")
        print(f"   Latency: {result['latency_ms']}ms")
        print(f"   Answer length: {len(result['answer'])} chars")
        print(f"\n   Answer preview:")
        print(f"   {result['answer'][:200]}...")

        # Test related queries
        print(f"\n   Testing related queries generation...")
        related = service.generate_related_queries(
            query="martial arts for beginners",
            count=3
        )

        print(f"✅ Related queries generated: {len(related)}")
        for i, rq in enumerate(related, 1):
            print(f"     {i}. {rq}")

        return True

    except Exception as e:
        print(f"❌ AI Registry service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_search_service():
    """Test complete query search service"""
    print_section("6. Complete Query Search Pipeline Test")

    try:
        from backend.services.query_search_service import QuerySearchService

        service = QuerySearchService()
        print(f"✅ QuerySearchService initialized")
        print(f"   Cache TTL: {service.cache_ttl}s")
        print(f"   Top K results: {service.top_k_results}")

        # Test with a real query
        test_query = "What are effective self defense techniques?"
        print(f"\n   Testing search query: '{test_query}'")

        result = service.search_query(
            query=test_query,
            user_id=None,
            ip_address="127.0.0.1",
            bypass_cache=True
        )

        print(f"✅ Search query completed successfully")
        print(f"\n   Response structure:")
        print(f"     - Answer: {len(result['answer'])} characters")
        print(f"     - Sources: {len(result['sources'])} items")
        print(f"     - Videos: {len(result['media']['videos'])}")
        print(f"     - Images: {len(result['media']['images'])}")
        print(f"     - Related queries: {len(result['related_queries'])}")
        print(f"     - Latency: {result['latency_ms']}ms")
        print(f"     - Cached: {result['cached']}")

        print(f"\n   Answer preview:")
        print(f"   {result['answer'][:300]}...")

        if result['sources']:
            print(f"\n   Sources:")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"     {i}. {source['title']} ({source['source_type']})")

        if result['related_queries']:
            print(f"\n   Related queries:")
            for i, rq in enumerate(result['related_queries'], 1):
                print(f"     {i}. {rq}")

        return True

    except Exception as e:
        print(f"❌ Query search service failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print_header("Search Pipeline Diagnostic Tool")

    results = {
        'Environment Variables': check_environment(),
        'Embedding Service': test_embedding_service(),
        'ZeroDB Client': test_zerodb_client(),
        'Vector Search Service': test_vector_search_service(),
        'AI Registry Service': test_ai_registry_service(),
        'Query Search Service': test_query_search_service()
    }

    # Print summary
    print_header("Diagnostic Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n{'='*80}")
    print(f"  OVERALL: {passed}/{total} tests passed")
    print(f"{'='*80}\n")

    if passed == total:
        print("🎉 All tests passed! Search pipeline is fully functional.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
