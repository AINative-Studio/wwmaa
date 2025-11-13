"""
Strapi Service Usage Examples

This file demonstrates various ways to use the Strapi service
for fetching blog articles from Strapi CMS.
"""

import logging
from typing import List, Dict, Any

from backend.services.strapi_service import (
    get_strapi_service,
    StrapiService,
    StrapiError,
    StrapiConnectionError,
    StrapiNotFoundError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Basic usage: fetch articles using singleton instance"""
    print("\n=== Example 1: Basic Usage ===")

    # Get service instance (singleton)
    strapi = get_strapi_service()

    try:
        # Fetch all articles (with caching)
        articles = strapi.fetch_articles(limit=10)

        print(f"Fetched {len(articles)} articles")
        for article in articles[:3]:  # Show first 3
            print(f"- {article['title']} (published: {article['published_at']})")

    except StrapiError as e:
        logger.error(f"Failed to fetch articles: {e}")


def example_fetch_by_slug():
    """Fetch a single article by slug"""
    print("\n=== Example 2: Fetch by Slug ===")

    strapi = get_strapi_service()

    try:
        # Fetch specific article
        slug = "five-tenets-taekwondo"
        article = strapi.fetch_article_by_slug(slug)

        if article:
            print(f"Found article: {article['title']}")
            print(f"Author: {article['author']}")
            print(f"Category: {article['category']}")
            print(f"URL: {article['url']}")
        else:
            print(f"Article with slug '{slug}' not found")

    except StrapiError as e:
        logger.error(f"Failed to fetch article: {e}")


def example_without_cache():
    """Fetch articles without using cache"""
    print("\n=== Example 3: Fetch Without Cache ===")

    strapi = get_strapi_service()

    try:
        # Bypass cache to get fresh data
        articles = strapi.fetch_articles(limit=5, use_cache=False)

        print(f"Fetched {len(articles)} articles (fresh from API)")

    except StrapiError as e:
        logger.error(f"Failed to fetch articles: {e}")


def example_custom_configuration():
    """Create service instance with custom configuration"""
    print("\n=== Example 4: Custom Configuration ===")

    try:
        # Create custom instance (not singleton)
        strapi = StrapiService(
            strapi_url="http://localhost:1337",
            api_token="custom_token_here",
            timeout=15,
            max_retries=5
        )

        articles = strapi.fetch_articles(limit=5)
        print(f"Fetched {len(articles)} articles with custom config")

        # Clean up
        strapi.close()

    except StrapiError as e:
        logger.error(f"Failed with custom config: {e}")


def example_error_handling():
    """Comprehensive error handling"""
    print("\n=== Example 5: Error Handling ===")

    strapi = get_strapi_service()

    try:
        articles = strapi.fetch_articles()
        print(f"Successfully fetched {len(articles)} articles")

    except StrapiConnectionError as e:
        logger.error(f"Connection error: {e}")
        # Handle connection errors (retry, use fallback data, etc.)

    except StrapiNotFoundError as e:
        logger.warning(f"Resource not found: {e}")
        # Handle not found

    except StrapiError as e:
        logger.error(f"General Strapi error: {e}")
        # Handle other errors


def example_cache_management():
    """Cache invalidation and management"""
    print("\n=== Example 6: Cache Management ===")

    strapi = get_strapi_service()

    try:
        # Fetch with cache
        articles = strapi.fetch_articles(limit=5)
        print(f"First fetch: {len(articles)} articles (may use cache)")

        # Invalidate cache
        deleted_count = strapi.invalidate_cache()
        print(f"Invalidated {deleted_count} cache entries")

        # Fetch again (will hit API)
        articles = strapi.fetch_articles(limit=5)
        print(f"Second fetch: {len(articles)} articles (fresh from API)")

    except StrapiError as e:
        logger.error(f"Cache management error: {e}")


def example_health_check():
    """Check Strapi service health"""
    print("\n=== Example 7: Health Check ===")

    strapi = get_strapi_service()

    try:
        health = strapi.health_check()

        print(f"Status: {health['status']}")
        print(f"Strapi URL: {health['strapi_url']}")
        print(f"Authenticated: {health['authenticated']}")
        print(f"Timestamp: {health['timestamp']}")

        if health['status'] == 'healthy':
            print("Strapi connection is healthy!")
        else:
            print(f"Strapi connection is unhealthy: {health.get('error')}")

    except Exception as e:
        logger.error(f"Health check failed: {e}")


def example_context_manager():
    """Use service with context manager for automatic cleanup"""
    print("\n=== Example 8: Context Manager ===")

    try:
        with StrapiService() as strapi:
            articles = strapi.fetch_articles(limit=5)
            print(f"Fetched {len(articles)} articles")
            # Session automatically closed when exiting context

    except StrapiError as e:
        logger.error(f"Context manager error: {e}")


def example_article_transformation():
    """Demonstrate article transformation"""
    print("\n=== Example 9: Article Transformation ===")

    # Example Strapi response
    strapi_article = {
        "id": 1,
        "attributes": {
            "title": "The Five Tenets of Taekwondo",
            "excerpt": "Exploring core principles of martial arts",
            "content": "Full article content here...",
            "slug": "five-tenets-taekwondo",
            "publishedAt": "2025-11-11T10:00:00.000Z",
            "author": "Master Kim",
            "featured_image": {
                "data": {
                    "attributes": {
                        "url": "/uploads/taekwondo.jpg"
                    }
                }
            },
            "category": "Training"
        }
    }

    strapi = get_strapi_service()
    transformed = strapi.transform_strapi_to_article(strapi_article)

    print("Transformed article:")
    print(f"- ID: {transformed['id']}")
    print(f"- Title: {transformed['title']}")
    print(f"- Slug: {transformed['slug']}")
    print(f"- URL: {transformed['url']}")
    print(f"- Author: {transformed['author']}")
    print(f"- Category: {transformed['category']}")
    print(f"- Published: {transformed['published_at']}")
    print(f"- Image URL: {transformed['image_url']}")


def example_api_route_integration():
    """Example of using Strapi service in FastAPI route"""
    print("\n=== Example 10: API Route Integration ===")

    # This is pseudo-code showing FastAPI integration
    print("FastAPI Route Example:")
    print("""
    from fastapi import APIRouter, HTTPException
    from backend.services.strapi_service import get_strapi_service, StrapiError

    router = APIRouter(prefix="/api/blog")

    @router.get("/articles")
    async def get_blog_articles(limit: int = 50):
        try:
            strapi = get_strapi_service()
            articles = strapi.fetch_articles(limit=limit)
            return {"data": articles, "count": len(articles)}
        except StrapiError as e:
            logger.error(f"Failed to fetch articles: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch articles")

    @router.get("/articles/{slug}")
    async def get_blog_article(slug: str):
        try:
            strapi = get_strapi_service()
            article = strapi.fetch_article_by_slug(slug)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            return article
        except StrapiError as e:
            logger.error(f"Failed to fetch article: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch article")
    """)


def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("STRAPI SERVICE USAGE EXAMPLES")
    print("=" * 60)

    examples = [
        example_basic_usage,
        example_fetch_by_slug,
        example_without_cache,
        example_custom_configuration,
        example_error_handling,
        example_cache_management,
        example_health_check,
        example_context_manager,
        example_article_transformation,
        example_api_route_integration
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            logger.error(f"Example failed: {e}")

    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    run_all_examples()
