"""
Blog API Routes for WWMAA Backend

Provides public endpoints for accessing blog posts from Strapi CMS.

NOTE: This system uses Strapi CMS for blog content management.
Articles are fetched directly from Strapi API with caching support.

Endpoints:
- GET /api/blog: Simple list of articles (frontend homepage)
- GET /api/blog/posts: List all published posts (paginated)
- GET /api/blog/posts/{slug}: Get single post by slug
- GET /api/blog/categories: List all categories
- GET /api/blog/tags: List all tags

Features:
- Pagination and filtering
- Category filtering
- Redis caching (5-minute TTL)
- Automatic fallback to sample data if Strapi is unavailable
- Graceful error handling
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from backend.services.strapi_service import get_strapi_service, StrapiError


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/blog",
    tags=["blog"]
)


@router.get("")
async def get_blog_articles(
    limit: int = Query(10, ge=1, le=100, description="Number of articles to fetch"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get blog articles (simple endpoint for frontend)

    Returns a simple array of blog articles matching the frontend Article interface.
    Fetches articles from Strapi CMS with Redis caching (5-minute TTL).

    Args:
        limit: Maximum number of articles to return (default: 10, max: 100)
        offset: Pagination offset (default: 0)
        category: Filter by category (optional)

    Returns:
        List of article objects with id, title, url, excerpt, published_at, author, image_url, and category
    """
    try:
        logger.info(f"Fetching blog articles: limit={limit}, offset={offset}, category={category}")

        strapi = get_strapi_service()

        # Fetch articles from Strapi (with caching)
        articles = strapi.fetch_articles(
            limit=limit + offset,  # Fetch more to handle offset
            sort="publishedAt:desc",
            use_cache=True
        )

        # Apply category filter if provided
        if category:
            articles = [
                article for article in articles
                if article.get('category', '').lower() == category.lower()
            ]

        # Apply pagination offset
        if offset > 0:
            articles = articles[offset:]

        # Limit results
        articles = articles[:limit]

        # If no articles found, return sample data as fallback
        if not articles:
            logger.warning("No articles found in Strapi, returning sample data")
            return [
                {
                    "id": "art_001",
                    "title": "The Five Tenets of Taekwondo: Building Character Through Martial Arts",
                    "excerpt": "Explore how the core principles of courtesy, integrity, perseverance, self-control, and indomitable spirit shape martial artists and everyday life.",
                    "url": "https://www.wwmaa.org/blog/five-tenets-taekwondo",
                    "published_at": "2025-10-15T10:00:00Z",
                    "author": "WWMAA Team",
                    "image_url": "",
                    "category": "Training"
                },
                {
                    "id": "art_002",
                    "title": "Breaking Barriers: Women in Martial Arts Leadership",
                    "excerpt": "Celebrating the journey of women who have shattered glass ceilings to become influential leaders, instructors, and champions in martial arts.",
                    "url": "https://www.wwmaa.org/blog/women-martial-arts-leadership",
                    "published_at": "2025-10-22T14:30:00Z",
                    "author": "WWMAA Team",
                    "image_url": "",
                    "category": "Leadership"
                },
                {
                    "id": "art_003",
                    "title": "Kata vs. Kumite: Understanding the Balance in Karate Training",
                    "excerpt": "Learn why mastering both forms practice (kata) and sparring (kumite) is essential for developing complete martial arts skills.",
                    "url": "https://www.wwmaa.org/blog/kata-vs-kumite-balance",
                    "published_at": "2025-10-28T09:15:00Z",
                    "author": "WWMAA Team",
                    "image_url": "",
                    "category": "Training"
                },
                {
                    "id": "art_004",
                    "title": "Self-Defense Strategies Every Woman Should Know",
                    "excerpt": "Practical, effective self-defense techniques and awareness strategies designed specifically for women's safety and empowerment.",
                    "url": "https://www.wwmaa.org/blog/self-defense-women",
                    "published_at": "2025-11-05T16:45:00Z",
                    "author": "WWMAA Team",
                    "image_url": "",
                    "category": "Self-Defense"
                },
                {
                    "id": "art_005",
                    "title": "The Mental Game: Building Confidence Through Martial Arts",
                    "excerpt": "Discover how consistent martial arts training builds mental resilience, confidence, and emotional regulation that extends beyond the dojo.",
                    "url": "https://www.wwmaa.org/blog/mental-game-confidence",
                    "published_at": "2025-11-10T11:20:00Z",
                    "author": "WWMAA Team",
                    "image_url": "",
                    "category": "Mental Health"
                }
            ]

        logger.info(f"Returning {len(articles)} blog articles from Strapi")
        return articles

    except StrapiError as e:
        logger.error(f"Strapi service error: {e}", exc_info=True)
        # Return empty array on Strapi error for graceful degradation
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching blog articles: {e}", exc_info=True)
        # Return empty array on any error for graceful degradation
        return []


@router.get("/posts")
async def list_blog_posts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Posts per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query("publishedAt", description="Sort field (publishedAt, title)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    List all published blog posts

    Returns paginated list of blog posts with filtering.

    Args:
        page: Page number (starts at 1)
        limit: Posts per page (max 100)
        category: Filter by category
        sort_by: Sort field (publishedAt, title)
        sort_order: Sort order (asc, desc)

    Returns:
        Paginated list of blog posts with metadata
    """
    try:
        logger.info(f"Listing blog posts: page={page}, limit={limit}, category={category}")

        strapi = get_strapi_service()

        # Build sort parameter for Strapi
        strapi_sort = f"{sort_by}:{sort_order}"

        # Calculate offset
        offset = (page - 1) * limit

        # Fetch articles from Strapi (fetch more for pagination)
        # Since Strapi doesn't support offset directly, we fetch a larger batch
        fetch_limit = min(offset + limit, 100)

        articles = strapi.fetch_articles(
            limit=fetch_limit,
            sort=strapi_sort,
            use_cache=True
        )

        # Apply category filter if provided
        if category:
            articles = [
                article for article in articles
                if article.get('category', '').lower() == category.lower()
            ]

        # Get total count (before pagination)
        total = len(articles)

        # Apply pagination
        paginated_articles = articles[offset:offset + limit]

        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "data": paginated_articles,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

    except StrapiError as e:
        logger.error(f"Strapi service error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch blog posts from CMS"
        )
    except Exception as e:
        logger.error(f"Error listing blog posts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch blog posts"
        )


@router.get("/posts/{slug}")
async def get_blog_post_by_slug(slug: str):
    """
    Get a single blog post by slug

    Args:
        slug: URL-friendly post slug

    Returns:
        Blog post data

    Raises:
        HTTPException: If post not found
    """
    try:
        logger.info(f"Fetching blog post by slug: {slug}")

        strapi = get_strapi_service()

        # Fetch article by slug from Strapi (with caching)
        article = strapi.fetch_article_by_slug(slug, use_cache=True)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="Blog post not found"
            )

        return article

    except HTTPException:
        raise
    except StrapiError as e:
        logger.error(f"Strapi service error fetching post {slug}: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch blog post from CMS"
        )
    except Exception as e:
        logger.error(f"Error fetching blog post {slug}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch blog post"
        )


@router.get("/categories")
async def list_blog_categories():
    """
    List all blog post categories

    Returns unique categories from all published posts.

    Returns:
        List of category objects with post counts
    """
    try:
        logger.info("Fetching blog categories")

        strapi = get_strapi_service()

        # Fetch all articles to extract categories
        articles = strapi.fetch_articles(limit=100, use_cache=True)

        # Extract and count categories
        category_counts = {}

        for article in articles:
            category = article.get('category')
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1

        # Format response
        categories = [
            {
                "name": category,
                "slug": category.lower().replace(' ', '-'),
                "count": count
            }
            for category, count in sorted(category_counts.items())
        ]

        return {
            "data": categories,
            "total": len(categories)
        }

    except StrapiError as e:
        logger.error(f"Strapi service error: {e}")
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch categories from CMS"
        )
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch categories"
        )


@router.get("/tags")
async def list_blog_tags():
    """
    List all blog post tags

    Returns unique tags from all published posts.

    Returns:
        List of tag objects with post counts (empty for now as Strapi doesn't have tags field)
    """
    try:
        logger.info("Fetching blog tags")

        # Note: Current Strapi schema doesn't include tags
        # This endpoint returns empty array for backward compatibility
        # Add tags support in Strapi schema and update this endpoint when needed

        return {
            "data": [],
            "total": 0
        }

    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch tags"
        )


@router.get("/posts/by-category/{category}")
async def get_posts_by_category(
    category: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get blog posts by category

    Args:
        category: Category name (or slug)
        page: Page number
        limit: Posts per page

    Returns:
        Paginated list of posts in category
    """
    return await list_blog_posts(
        page=page,
        limit=limit,
        category=category
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for blog service

    Returns:
        Health status and Strapi connection info
    """
    try:
        strapi = get_strapi_service()
        health_status = strapi.health_check()

        return {
            "service": "blog",
            "status": "healthy" if health_status.get("status") == "healthy" else "degraded",
            "strapi": health_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "service": "blog",
            "status": "unhealthy",
            "error": str(e)
        }
