# Strapi CMS Backend Integration Guide

**Project**: WWMAA Backend Integration with Strapi
**Date**: November 11, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Backend Service Implementation](#backend-service-implementation)
4. [API Route Implementation](#api-route-implementation)
5. [Caching Strategy](#caching-strategy)
6. [Webhook Integration](#webhook-integration)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Deployment Checklist](#deployment-checklist)

---

## Overview

This guide details how to integrate Strapi CMS with the WWMAA FastAPI backend to serve dynamic content while maintaining performance and reliability.

### Integration Benefits

- Decouple content management from backend logic
- Enable non-technical team members to manage content
- Centralized content storage with versioning
- API-first architecture for flexible frontend consumption
- Built-in media management and optimization

### Integration Approach

```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│   Frontend  │───1───▶│   Backend   │───2───▶│   Strapi    │
│  (Next.js)  │        │  (FastAPI)  │        │    CMS      │
└─────────────┘        └─────────────┘        └─────────────┘
                              │                       │
                              │                       │
                              ▼                       ▼
                        ┌──────────┐          ┌──────────┐
                        │  Redis   │          │PostgreSQL│
                        │  Cache   │          │ Database │
                        └──────────┘          └──────────┘
```

**Flow**:
1. Frontend requests content from Backend API
2. Backend checks Redis cache
3. If cache miss, Backend fetches from Strapi
4. Backend caches response in Redis
5. Backend returns content to Frontend

---

## Architecture Patterns

### Pattern 1: Backend Proxy (Recommended)

**When to Use**: For most content types where you need caching, authentication, or data transformation.

**Pros**:
- Centralized caching in Redis
- Single authentication point
- Transform/enrich content before sending to frontend
- Rate limiting and abuse prevention
- Consistent error handling

**Cons**:
- Additional latency (mitigated by caching)
- Backend must be deployed for content to work

**Implementation**: Backend proxies all Strapi requests through FastAPI endpoints.

### Pattern 2: Direct Frontend Access

**When to Use**: For public, frequently accessed content that needs to be extremely fast.

**Pros**:
- Lower latency (one less hop)
- Reduced backend load
- Simpler architecture for public content

**Cons**:
- No centralized caching
- Exposing Strapi URL to clients
- Client-side API token management (use public role)

**Implementation**: Frontend calls Strapi API directly using public API tokens.

### Pattern 3: Hybrid Approach (Best for WWMAA)

- **Private/Dynamic Content**: Use Backend Proxy (user-specific data)
- **Public/Static Content**: Allow direct frontend access with CDN caching
- **Real-time Content**: Use webhooks to invalidate cache

---

## Backend Service Implementation

### Step 1: Add Dependencies

Update `/Users/aideveloper/Desktop/wwmaa/backend/requirements.txt`:

```txt
# Add these to existing requirements
httpx==0.25.2  # Already present for async HTTP
redis==5.0.1   # Already present for caching
```

### Step 2: Update Configuration

Edit `/Users/aideveloper/Desktop/wwmaa/backend/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # ... existing settings ...

    # Strapi CMS Configuration
    STRAPI_API_URL: str = "http://localhost:1337"
    STRAPI_API_TOKEN: str = ""
    STRAPI_CACHE_TTL: int = 300  # 5 minutes default cache
    STRAPI_TIMEOUT: int = 10  # Request timeout in seconds

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Step 3: Create Strapi Service

Create `/Users/aideveloper/Desktop/wwmaa/backend/services/strapi_service.py`:

```python
"""
Strapi CMS Integration Service

Handles all communication with Strapi CMS including:
- Content fetching with caching
- Error handling and retries
- Response transformation
"""

import httpx
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from redis import Redis
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class StrapiService:
    """Service for interacting with Strapi CMS"""

    def __init__(self):
        self.base_url = settings.STRAPI_API_URL.rstrip('/')
        self.api_token = settings.STRAPI_API_TOKEN
        self.timeout = settings.STRAPI_TIMEOUT
        self.cache_ttl = settings.STRAPI_CACHE_TTL

        # HTTP headers for Strapi API
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        # Redis cache client
        try:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.redis = None

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from Redis cache"""
        if not self.redis:
            return None

        try:
            cached = self.redis.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT: {cache_key}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: {cache_key}")
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")

        return None

    async def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """Store data in Redis cache"""
        if not self.redis:
            return

        try:
            ttl = ttl or self.cache_ttl
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache storage error: {e}")

    def _invalidate_cache(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        if not self.redis:
            return

        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Strapi with caching"""

        # Check cache first
        if cache_key:
            cached = await self._get_from_cache(cache_key)
            if cached:
                return cached

        # Make request to Strapi
        url = f"{self.base_url}/api/{endpoint}"
        logger.info(f"Fetching from Strapi: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params or {}
                )
                response.raise_for_status()
                data = response.json()

                # Cache successful response
                if cache_key:
                    await self._set_cache(cache_key, data, cache_ttl)

                return data

        except httpx.HTTPStatusError as e:
            logger.error(f"Strapi HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Strapi request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching from Strapi: {e}")
            raise

    # ===== Blog Posts =====

    async def get_blog_posts(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = "publishedAt:desc",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch paginated blog posts from Strapi"""

        cache_key = f"strapi:blog_posts:{page}:{page_size}:{sort}"
        if filters:
            cache_key += f":{json.dumps(filters, sort_keys=True)}"

        params = {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort": sort,
            "populate": "*"  # Populate all relations
        }

        # Add filters if provided
        if filters:
            for key, value in filters.items():
                params[f"filters[{key}]"] = value

        return await self._make_request(
            "blog-posts",
            params=params,
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

    async def get_blog_post_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch single blog post by slug"""

        cache_key = f"strapi:blog_post:{slug}"

        params = {
            "filters[slug][$eq]": slug,
            "populate": "*"
        }

        data = await self._make_request(
            "blog-posts",
            params=params,
            cache_key=cache_key,
            cache_ttl=600  # 10 minutes
        )

        # Return first result or None
        return data["data"][0] if data.get("data") else None

    async def get_blog_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single blog post by ID"""

        cache_key = f"strapi:blog_post:id:{post_id}"

        data = await self._make_request(
            f"blog-posts/{post_id}",
            params={"populate": "*"},
            cache_key=cache_key,
            cache_ttl=600  # 10 minutes
        )

        return data.get("data")

    def invalidate_blog_cache(self, slug: Optional[str] = None):
        """Invalidate blog post cache"""
        if slug:
            self._invalidate_cache(f"strapi:blog_post:{slug}")
        else:
            self._invalidate_cache("strapi:blog_*")

    # ===== Events =====

    async def get_events(
        self,
        upcoming_only: bool = True,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch events from Strapi"""

        cache_key = f"strapi:events:{upcoming_only}:{page}:{page_size}:{category}"

        params = {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort": "startDate:asc",
            "populate": "*"
        }

        # Filter for upcoming events only
        if upcoming_only:
            now = datetime.utcnow().isoformat()
            params["filters[startDate][$gte]"] = now

        # Filter by category
        if category:
            params["filters[category][$eq]"] = category

        return await self._make_request(
            "events",
            params=params,
            cache_key=cache_key,
            cache_ttl=180  # 3 minutes (events are time-sensitive)
        )

    async def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single event by ID"""

        cache_key = f"strapi:event:id:{event_id}"

        data = await self._make_request(
            f"events/{event_id}",
            params={"populate": "*"},
            cache_key=cache_key,
            cache_ttl=300  # 5 minutes
        )

        return data.get("data")

    def invalidate_events_cache(self):
        """Invalidate all events cache"""
        self._invalidate_cache("strapi:events:*")
        self._invalidate_cache("strapi:event:*")

    # ===== Educational Resources =====

    async def get_resources(
        self,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Fetch educational resources from Strapi"""

        cache_key = f"strapi:resources:{category}:{page}:{page_size}"

        params = {
            "pagination[page]": page,
            "pagination[pageSize]": page_size,
            "sort": "createdAt:desc",
            "populate": "*"
        }

        if category:
            params["filters[category][$eq]"] = category

        return await self._make_request(
            "resources",
            params=params,
            cache_key=cache_key,
            cache_ttl=600  # 10 minutes
        )


# Singleton instance
strapi_service = StrapiService()
```

---

## API Route Implementation

Create `/Users/aideveloper/Desktop/wwmaa/backend/routes/content.py`:

```python
"""
Content API Routes

Proxies requests to Strapi CMS with caching and error handling
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from backend.services.strapi_service import strapi_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content"])


# ===== Blog Posts =====

@router.get("/blog-posts")
async def get_blog_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort: str = Query("publishedAt:desc", description="Sort order")
):
    """
    Get all published blog posts

    - **page**: Page number (starts at 1)
    - **page_size**: Number of posts per page (max 100)
    - **sort**: Sort order (e.g., 'publishedAt:desc', 'title:asc')

    Returns paginated blog posts with metadata
    """
    try:
        return await strapi_service.get_blog_posts(
            page=page,
            page_size=page_size,
            sort=sort
        )
    except Exception as e:
        logger.error(f"Error fetching blog posts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch blog posts"
        )


@router.get("/blog-posts/{slug}")
async def get_blog_post(slug: str = Path(..., description="Blog post slug")):
    """
    Get single blog post by slug

    - **slug**: Unique slug identifier (e.g., 'my-first-post')

    Returns full blog post with all relations populated
    """
    try:
        post = await strapi_service.get_blog_post_by_slug(slug)

        if not post:
            raise HTTPException(
                status_code=404,
                detail=f"Blog post with slug '{slug}' not found"
            )

        return post

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching blog post: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch blog post"
        )


# ===== Events =====

@router.get("/events")
async def get_events(
    upcoming_only: bool = Query(True, description="Show only upcoming events"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get all events

    - **upcoming_only**: If true, only return future events
    - **page**: Page number (starts at 1)
    - **page_size**: Number of events per page (max 100)
    - **category**: Filter by event category (Workshop, Networking, Conference)

    Returns paginated events sorted by start date
    """
    try:
        return await strapi_service.get_events(
            upcoming_only=upcoming_only,
            page=page,
            page_size=page_size,
            category=category
        )
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch events"
        )


@router.get("/events/{event_id}")
async def get_event(event_id: int = Path(..., ge=1, description="Event ID")):
    """
    Get single event by ID

    - **event_id**: Unique event identifier

    Returns full event details with all relations
    """
    try:
        event = await strapi_service.get_event_by_id(event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"Event with ID {event_id} not found"
            )

        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch event"
        )


# ===== Educational Resources =====

@router.get("/resources")
async def get_resources(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get educational resources

    - **category**: Filter by resource category
    - **page**: Page number (starts at 1)
    - **page_size**: Number of resources per page (max 100)

    Returns paginated resources sorted by creation date
    """
    try:
        return await strapi_service.get_resources(
            category=category,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error fetching resources: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch resources"
        )


# ===== Cache Management (Admin only) =====

@router.post("/cache/invalidate")
async def invalidate_cache(
    content_type: str = Query(..., description="Content type to invalidate"),
    slug: Optional[str] = Query(None, description="Specific item slug")
):
    """
    Invalidate content cache (Admin only)

    - **content_type**: Type of content (blog, events, resources)
    - **slug**: Optional specific item slug to invalidate

    Use this after updating content in Strapi admin panel
    """
    # TODO: Add admin authentication check
    # if not is_admin(request.user):
    #     raise HTTPException(status_code=403, detail="Admin access required")

    try:
        if content_type == "blog":
            strapi_service.invalidate_blog_cache(slug)
        elif content_type == "events":
            strapi_service.invalidate_events_cache()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown content type: {content_type}"
            )

        return {
            "status": "success",
            "message": f"Cache invalidated for {content_type}" +
                      (f" (slug: {slug})" if slug else "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )
```

### Register Router in Main App

Edit `/Users/aideveloper/Desktop/wwmaa/backend/app.py`:

```python
# ... existing imports ...
from backend.routes import content

# ... existing code ...

# Register content routes
app.include_router(content.router)
```

---

## Caching Strategy

### Cache Keys Structure

```
strapi:blog_posts:{page}:{page_size}:{sort}
strapi:blog_post:{slug}
strapi:blog_post:id:{id}
strapi:events:{upcoming}:{page}:{page_size}:{category}
strapi:event:id:{id}
strapi:resources:{category}:{page}:{page_size}
```

### TTL Recommendations

| Content Type | TTL | Reasoning |
|--------------|-----|-----------|
| Blog Post List | 5 min | Frequently updated, but not real-time |
| Single Blog Post | 10 min | Rarely updated after publishing |
| Events List | 3 min | Time-sensitive, need fresh data |
| Single Event | 5 min | Details change less frequently |
| Resources | 10 min | Static educational content |

### Cache Invalidation Strategies

#### 1. Manual Invalidation (Current)

Admin calls `/api/content/cache/invalidate` after updating content in Strapi.

**Pros**: Simple, explicit control
**Cons**: Requires manual action, easy to forget

#### 2. Webhook-Based Invalidation (Recommended)

Strapi sends webhook to backend when content is updated.

**Implementation**:

Create `/Users/aideveloper/Desktop/wwmaa/backend/routes/webhooks.py`:

```python
from fastapi import APIRouter, Request, HTTPException, Header
from backend.services.strapi_service import strapi_service
import hmac
import hashlib

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

def verify_strapi_webhook(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature from Strapi"""
    computed = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)

@router.post("/strapi/content-updated")
async def strapi_content_updated(
    request: Request,
    x_strapi_signature: str = Header(None)
):
    """Handle Strapi content update webhooks"""

    # Verify webhook signature
    body = await request.body()
    if not verify_strapi_webhook(body, x_strapi_signature, settings.STRAPI_WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse webhook payload
    data = await request.json()
    content_type = data.get("model")
    entry = data.get("entry")

    # Invalidate relevant cache
    if content_type == "blog-post":
        slug = entry.get("slug")
        strapi_service.invalidate_blog_cache(slug)
    elif content_type == "event":
        strapi_service.invalidate_events_cache()

    return {"status": "success", "invalidated": content_type}
```

#### 3. TTL-Based Invalidation (Automatic)

Cache expires after TTL, ensuring fresh data without manual intervention.

**Currently Implemented**: Yes, with configurable TTLs per content type.

---

## Webhook Integration

### Configure Strapi Webhooks

1. In Strapi admin panel, go to **Settings** → **Webhooks**
2. Click **Create new webhook**
3. Configure:
   - **Name**: Content Cache Invalidation
   - **URL**: `https://your-backend.railway.app/api/webhooks/strapi/content-updated`
   - **Events**: Select `entry.create`, `entry.update`, `entry.delete`
   - **Headers**: Add `x-strapi-signature` (generated secret)
4. Save webhook

### Add Webhook Secret to Backend

In Railway backend service variables:

```env
STRAPI_WEBHOOK_SECRET=<generate-random-secret>
```

Generate secret:
```bash
openssl rand -base64 32
```

---

## Error Handling

### HTTP Error Responses

| Status Code | Meaning | Example |
|-------------|---------|---------|
| 200 | Success | Content retrieved successfully |
| 404 | Not Found | Blog post with slug doesn't exist |
| 500 | Server Error | Strapi service unavailable |
| 503 | Service Unavailable | Strapi timeout or connection error |

### Retry Logic

For transient errors (network issues, timeouts), implement retry with exponential backoff:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str):
    """Fetch with automatic retry on failure"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

---

## Testing

### Unit Tests

Create `/Users/aideveloper/Desktop/wwmaa/backend/tests/test_strapi_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from backend.services.strapi_service import strapi_service

@pytest.mark.asyncio
async def test_get_blog_posts():
    """Test fetching blog posts from Strapi"""

    mock_response = {
        "data": [
            {
                "id": 1,
                "attributes": {
                    "title": "Test Post",
                    "slug": "test-post",
                    "content": "Test content"
                }
            }
        ],
        "meta": {
            "pagination": {
                "page": 1,
                "pageSize": 10,
                "total": 1
            }
        }
    }

    with patch.object(strapi_service, '_make_request', return_value=mock_response):
        result = await strapi_service.get_blog_posts()

    assert result == mock_response
    assert len(result["data"]) == 1
    assert result["data"][0]["attributes"]["title"] == "Test Post"

@pytest.mark.asyncio
async def test_get_blog_post_not_found():
    """Test fetching non-existent blog post"""

    mock_response = {"data": []}

    with patch.object(strapi_service, '_make_request', return_value=mock_response):
        result = await strapi_service.get_blog_post_by_slug("nonexistent")

    assert result is None
```

### Integration Tests

Create `/Users/aideveloper/Desktop/wwmaa/backend/tests/test_content_routes.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_get_blog_posts_endpoint():
    """Test blog posts API endpoint"""
    response = client.get("/api/content/blog-posts")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data

def test_get_blog_post_by_slug():
    """Test single blog post endpoint"""
    response = client.get("/api/content/blog-posts/test-slug")
    assert response.status_code in [200, 404]

def test_get_events_endpoint():
    """Test events API endpoint"""
    response = client.get("/api/content/events?upcoming_only=true")
    assert response.status_code == 200
```

---

## Deployment Checklist

### Backend Configuration

- [ ] Add `STRAPI_API_URL` to Railway backend variables
- [ ] Add `STRAPI_API_TOKEN` (generated from Strapi admin panel)
- [ ] Add `STRAPI_WEBHOOK_SECRET` (for webhook verification)
- [ ] Verify Redis connection for caching
- [ ] Update `requirements.txt` with httpx and redis

### Strapi Configuration

- [ ] Deploy Strapi to Railway (see STRAPI-RAILWAY-DEPLOYMENT.md)
- [ ] Create API token in Strapi admin panel
- [ ] Configure webhooks for cache invalidation
- [ ] Set up CORS to allow backend domain

### Testing

- [ ] Test `/api/content/blog-posts` endpoint
- [ ] Test `/api/content/events` endpoint
- [ ] Verify caching works (check Redis)
- [ ] Test cache invalidation (manual or webhook)
- [ ] Load test with 100+ concurrent requests

### Monitoring

- [ ] Set up logging for Strapi requests
- [ ] Monitor cache hit/miss rates
- [ ] Alert on Strapi API errors
- [ ] Track response times (should be <200ms with cache)

---

## Next Steps

1. ✅ Implement Strapi service in backend
2. ✅ Create content API routes
3. ✅ Add caching layer with Redis
4. ⏳ Set up webhook integration
5. ⏳ Deploy and test in production
6. ⏳ Update frontend to consume content API
7. ⏳ Train team on Strapi admin panel

---

**Last Updated**: November 11, 2025
