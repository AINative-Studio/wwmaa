"""
Blog API Routes for WWMAA Backend

Provides public endpoints for accessing blog posts synced from BeeHiiv.

Endpoints:
- GET /api/blog/posts: List all published posts (paginated)
- GET /api/blog/posts/{slug}: Get single post by slug
- GET /api/blog/categories: List all categories
- GET /api/blog/tags: List all tags
- GET /api/blog/posts/related/{post_id}: Get related posts

Features:
- Pagination and filtering
- Search by title/content
- Category and tag filtering
- View count tracking
- Related posts by category/tags
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from backend.services.zerodb_service import get_zerodb_service
from backend.models.schemas import Article, ArticleStatus


# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/blog",
    tags=["blog"]
)


@router.get("/posts")
async def list_blog_posts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Posts per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in title and excerpt"),
    sort_by: str = Query("published_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    List all published blog posts

    Returns paginated list of blog posts with filtering and search.

    Args:
        page: Page number (starts at 1)
        limit: Posts per page (max 100)
        category: Filter by category
        tag: Filter by tag
        search: Search query for title/excerpt
        sort_by: Sort field (published_at, title, view_count)
        sort_order: Sort order (asc, desc)

    Returns:
        Paginated list of blog posts with metadata
    """
    try:
        zerodb = get_zerodb_service()

        # Build query filters
        filters = {
            'status': ArticleStatus.PUBLISHED
        }

        if category:
            filters['category'] = category

        if tag:
            filters['tags'] = {'$contains': tag}

        # Calculate offset
        offset = (page - 1) * limit

        # Fetch posts
        posts = zerodb.query_documents(
            collection='articles',
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Apply search filter if provided (post-query filtering)
        if search and posts:
            search_lower = search.lower()
            posts = [
                post for post in posts
                if search_lower in post.get('title', '').lower() or
                   search_lower in post.get('excerpt', '').lower()
            ]

        # Get total count for pagination
        total = zerodb.count_documents('articles', filters)

        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "data": posts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

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

    Increments view count on each access.

    Args:
        slug: URL-friendly post slug

    Returns:
        Blog post data

    Raises:
        HTTPException: If post not found
    """
    try:
        zerodb = get_zerodb_service()

        # Find post by slug
        posts = zerodb.query_documents(
            collection='articles',
            filters={'slug': slug},
            limit=1
        )

        if not posts:
            raise HTTPException(
                status_code=404,
                detail="Blog post not found"
            )

        post = posts[0]

        # Only show published posts
        if post.get('status') != ArticleStatus.PUBLISHED:
            raise HTTPException(
                status_code=404,
                detail="Blog post not found"
            )

        # Increment view count
        post_id = post.get('id')
        current_view_count = post.get('view_count', 0)

        zerodb.update_document(
            collection='articles',
            document_id=str(post_id),
            updates={
                'view_count': current_view_count + 1,
                'updated_at': datetime.utcnow()
            }
        )

        # Update view count in response
        post['view_count'] = current_view_count + 1

        return post

    except HTTPException:
        raise
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
        zerodb = get_zerodb_service()

        # Fetch all published posts
        posts = zerodb.query_documents(
            collection='articles',
            filters={'status': ArticleStatus.PUBLISHED},
            limit=10000  # Large limit to get all posts
        )

        # Extract and count categories
        category_counts = {}

        for post in posts:
            category = post.get('category')
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
        List of tag objects with post counts
    """
    try:
        zerodb = get_zerodb_service()

        # Fetch all published posts
        posts = zerodb.query_documents(
            collection='articles',
            filters={'status': ArticleStatus.PUBLISHED},
            limit=10000  # Large limit to get all posts
        )

        # Extract and count tags
        tag_counts = {}

        for post in posts:
            tags = post.get('tags', [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Format response
        tags = [
            {
                "name": tag,
                "slug": tag.lower().replace(' ', '-'),
                "count": count
            }
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        return {
            "data": tags,
            "total": len(tags)
        }

    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch tags"
        )


@router.get("/posts/related/{post_id}")
async def get_related_posts(
    post_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of related posts")
):
    """
    Get related blog posts

    Finds related posts based on:
    1. Same category
    2. Overlapping tags
    3. Recent posts

    Args:
        post_id: Current post UUID
        limit: Number of related posts to return

    Returns:
        List of related posts

    Raises:
        HTTPException: If post not found
    """
    try:
        zerodb = get_zerodb_service()

        # Get current post
        try:
            current_post = zerodb.get_document('articles', str(post_id))
        except:
            raise HTTPException(
                status_code=404,
                detail="Blog post not found"
            )

        category = current_post.get('category')
        tags = current_post.get('tags', [])

        # Find related posts
        related_posts = []

        # 1. Posts in same category
        if category:
            category_posts = zerodb.query_documents(
                collection='articles',
                filters={
                    'status': ArticleStatus.PUBLISHED,
                    'category': category,
                    'id': {'$ne': str(post_id)}  # Exclude current post
                },
                limit=limit,
                sort_by='published_at',
                sort_order='desc'
            )
            related_posts.extend(category_posts)

        # 2. Posts with overlapping tags (if not enough from category)
        if len(related_posts) < limit and tags:
            for tag in tags:
                tag_posts = zerodb.query_documents(
                    collection='articles',
                    filters={
                        'status': ArticleStatus.PUBLISHED,
                        'tags': {'$contains': tag},
                        'id': {'$ne': str(post_id)}
                    },
                    limit=limit - len(related_posts),
                    sort_by='published_at',
                    sort_order='desc'
                )

                # Add posts that aren't already in related_posts
                existing_ids = {p['id'] for p in related_posts}
                for post in tag_posts:
                    if post['id'] not in existing_ids and len(related_posts) < limit:
                        related_posts.append(post)
                        existing_ids.add(post['id'])

        # 3. Recent posts (if still not enough)
        if len(related_posts) < limit:
            recent_posts = zerodb.query_documents(
                collection='articles',
                filters={
                    'status': ArticleStatus.PUBLISHED,
                    'id': {'$ne': str(post_id)}
                },
                limit=limit - len(related_posts),
                sort_by='published_at',
                sort_order='desc'
            )

            existing_ids = {p['id'] for p in related_posts}
            for post in recent_posts:
                if post['id'] not in existing_ids and len(related_posts) < limit:
                    related_posts.append(post)

        # Limit to requested number
        related_posts = related_posts[:limit]

        return {
            "data": related_posts,
            "total": len(related_posts)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching related posts for {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch related posts"
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


@router.get("/posts/by-tag/{tag}")
async def get_posts_by_tag(
    tag: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get blog posts by tag

    Args:
        tag: Tag name (or slug)
        page: Page number
        limit: Posts per page

    Returns:
        Paginated list of posts with tag
    """
    return await list_blog_posts(
        page=page,
        limit=limit,
        tag=tag
    )
