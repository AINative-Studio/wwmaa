# Strapi Service Documentation

## Overview

The Strapi Service provides integration with Strapi CMS for fetching blog articles. It includes HTTP client functionality, response transformation, authentication, error handling with retry logic, and Redis caching.

## Features

- **Fetch Articles**: Retrieve articles from Strapi REST API
- **Response Transformation**: Convert Strapi response format to internal Article model
- **API Token Authentication**: Secure authentication with Strapi API tokens
- **Retry Logic**: Exponential backoff retry strategy for resilience
- **Redis Caching**: 5-minute TTL cache to reduce API calls
- **Connection Pooling**: Efficient HTTP connection management
- **Error Handling**: Comprehensive exception handling with custom error types

## Installation & Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Strapi CMS Configuration
STRAPI_URL=http://localhost:1337  # or http://strapi:1337 for Docker
STRAPI_API_TOKEN=your_api_token_here
```

### Docker Environment

For Docker deployments, use the service name:
```bash
STRAPI_URL=http://strapi:1337
```

### Configuration Access

```python
from backend.config import settings

# Access configuration
strapi_config = settings.get_strapi_config()
# Returns: {"strapi_url": "...", "api_token": "..."}
```

## Usage

### Basic Usage

```python
from backend.services.strapi_service import get_strapi_service

# Get service instance (singleton)
strapi = get_strapi_service()

# Fetch all articles
articles = strapi.fetch_articles(limit=50)

# Fetch article by slug
article = strapi.fetch_article_by_slug("my-article-slug")
```

### Advanced Usage

#### Custom Configuration

```python
from backend.services.strapi_service import StrapiService

# Create custom instance
strapi = StrapiService(
    strapi_url="https://custom-strapi.com",
    api_token="custom_token",
    timeout=15,
    max_retries=5
)
```

#### Disable Caching

```python
# Fetch without cache
articles = strapi.fetch_articles(use_cache=False)

# Fetch single article without cache
article = strapi.fetch_article_by_slug("slug", use_cache=False)
```

#### Cache Management

```python
# Invalidate all article cache
deleted_count = strapi.invalidate_cache()

# Invalidate specific pattern
deleted_count = strapi.invalidate_cache("strapi:articles:slug:*")
```

#### Health Check

```python
# Check Strapi connection
health = strapi.health_check()
# Returns: {"status": "healthy", "strapi_url": "...", "authenticated": True}
```

#### Context Manager

```python
# Automatic cleanup with context manager
with StrapiService() as strapi:
    articles = strapi.fetch_articles()
# Session automatically closed
```

## API Methods

### `fetch_articles(limit=50, sort="publishedAt:desc", populate="*", use_cache=True)`

Fetch multiple articles from Strapi.

**Parameters:**
- `limit` (int): Maximum number of articles (default: 50)
- `sort` (str): Sort order (default: "publishedAt:desc")
- `populate` (str): Fields to populate (default: "*")
- `use_cache` (bool): Enable Redis caching (default: True)

**Returns:** `List[Dict[str, Any]]` - List of transformed article dictionaries

**Raises:**
- `StrapiError`: If fetch fails
- `StrapiConnectionError`: If connection fails
- `StrapiAuthenticationError`: If authentication fails

**Example:**
```python
articles = strapi.fetch_articles(
    limit=20,
    sort="publishedAt:desc",
    populate="*"
)
```

### `fetch_article_by_slug(slug, populate="*", use_cache=True)`

Fetch a single article by its slug.

**Parameters:**
- `slug` (str): Article slug
- `populate` (str): Fields to populate (default: "*")
- `use_cache` (bool): Enable Redis caching (default: True)

**Returns:** `Optional[Dict[str, Any]]` - Transformed article or None if not found

**Example:**
```python
article = strapi.fetch_article_by_slug("five-tenets-of-taekwondo")
if article:
    print(f"Title: {article['title']}")
```

### `transform_strapi_to_article(strapi_article)`

Transform Strapi response format to internal Article model.

**Input Format (Strapi):**
```json
{
  "id": 1,
  "attributes": {
    "title": "Article Title",
    "excerpt": "Short description",
    "content": "Full article content",
    "slug": "article-title",
    "publishedAt": "2025-11-11T10:00:00.000Z",
    "author": "John Doe",
    "featured_image": { "url": "/uploads/image.jpg" },
    "category": "Training"
  }
}
```

**Output Format (Internal):**
```json
{
  "id": "1",
  "title": "Article Title",
  "excerpt": "Short description",
  "content": "Full article content",
  "url": "https://wwmaa.com/blog/article-title",
  "slug": "article-title",
  "published_at": "2025-11-11T10:00:00Z",
  "author": "John Doe",
  "image_url": "https://wwmaa.com/uploads/image.jpg",
  "category": "Training"
}
```

### `invalidate_cache(cache_key_pattern=None)`

Invalidate cached articles.

**Parameters:**
- `cache_key_pattern` (str, optional): Pattern to match (default: all articles)

**Returns:** `int` - Number of cache keys deleted

**Example:**
```python
# Clear all article cache
strapi.invalidate_cache()

# Clear specific slug cache
strapi.invalidate_cache("strapi:articles:slug:my-slug")
```

### `health_check()`

Perform health check on Strapi connection.

**Returns:** `Dict[str, Any]` - Health status information

**Example:**
```python
health = strapi.health_check()
if health["status"] == "healthy":
    print("Strapi connection is healthy")
```

## Error Handling

### Exception Hierarchy

```
StrapiError (base)
├── StrapiConnectionError (connection issues)
├── StrapiAuthenticationError (401/403 errors)
├── StrapiNotFoundError (404 errors)
└── StrapiValidationError (400/422 errors)
```

### Error Handling Examples

```python
from backend.services.strapi_service import (
    get_strapi_service,
    StrapiError,
    StrapiConnectionError,
    StrapiNotFoundError
)

strapi = get_strapi_service()

try:
    articles = strapi.fetch_articles()
except StrapiConnectionError as e:
    logger.error(f"Cannot connect to Strapi: {e}")
    # Handle connection error (retry, use fallback, etc.)
except StrapiNotFoundError as e:
    logger.warning(f"Resource not found: {e}")
    # Handle not found
except StrapiError as e:
    logger.error(f"Strapi error: {e}")
    # Handle general error
```

## Caching Strategy

### Cache Configuration

- **Cache Prefix**: `strapi:articles`
- **TTL**: 300 seconds (5 minutes)
- **Storage**: Redis

### Cache Keys

- List cache: `strapi:articles:list:{limit}:{sort}`
- Single article: `strapi:articles:slug:{slug}`

### Cache Behavior

1. **Cache Hit**: Return cached data immediately
2. **Cache Miss**: Fetch from Strapi, cache result, return data
3. **Cache Error**: Log warning, proceed without cache

## Performance Considerations

### Connection Pooling

The service uses connection pooling for efficient HTTP connections:
- **Pool Connections**: 10
- **Pool Max Size**: 10

### Retry Strategy

Exponential backoff retry for resilient API calls:
- **Max Retries**: 3
- **Backoff Factor**: 1 (waits 1s, 2s, 4s)
- **Retry Status Codes**: 429, 500, 502, 503, 504

### Timeout

- **Default Timeout**: 10 seconds
- **Health Check Timeout**: 5 seconds

## Integration with Blog Routes

### Example: Using in API Route

```python
from fastapi import APIRouter, HTTPException
from backend.services.strapi_service import get_strapi_service, StrapiError

router = APIRouter(prefix="/api/blog")

@router.get("/articles")
async def get_blog_articles():
    try:
        strapi = get_strapi_service()
        articles = strapi.fetch_articles(limit=50)
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
```

## Testing

### Unit Tests

```python
import pytest
from backend.services.strapi_service import StrapiService, StrapiError

def test_fetch_articles():
    strapi = StrapiService()
    articles = strapi.fetch_articles(limit=10)
    assert isinstance(articles, list)
    assert len(articles) <= 10

def test_fetch_article_by_slug():
    strapi = StrapiService()
    article = strapi.fetch_article_by_slug("test-slug")
    assert article is None or isinstance(article, dict)

def test_transform_strapi_to_article():
    strapi = StrapiService()
    strapi_data = {
        "id": 1,
        "attributes": {
            "title": "Test Article",
            "slug": "test-article",
            "excerpt": "Test excerpt",
            "content": "Test content",
            "publishedAt": "2025-11-11T10:00:00.000Z",
            "author": "John Doe",
            "category": "Testing"
        }
    }

    result = strapi.transform_strapi_to_article(strapi_data)

    assert result["id"] == "1"
    assert result["title"] == "Test Article"
    assert result["slug"] == "test-article"
    assert result["author"] == "John Doe"
```

### Integration Tests

```python
def test_strapi_integration():
    """Test actual Strapi connection (requires running Strapi instance)"""
    strapi = StrapiService()

    # Health check
    health = strapi.health_check()
    assert health["status"] == "healthy"

    # Fetch articles
    articles = strapi.fetch_articles(limit=5)
    assert isinstance(articles, list)
```

## Logging

The service uses Python's logging module. Configure logging level:

```python
import logging

# Set Strapi service log level
logging.getLogger("backend.services.strapi_service").setLevel(logging.DEBUG)
```

**Log Levels:**
- `DEBUG`: Cache hits/misses, detailed operations
- `INFO`: Service initialization, fetch operations
- `WARNING`: Missing configuration, cache errors
- `ERROR`: API errors, connection failures

## Migration from BeeHiiv

If migrating from BeeHiiv to Strapi:

1. **Update environment variables**:
   ```bash
   # Add Strapi config
   STRAPI_URL=http://localhost:1337
   STRAPI_API_TOKEN=your_token
   ```

2. **Update service imports**:
   ```python
   # Old
   from backend.services.blog_sync_service import get_blog_sync_service

   # New
   from backend.services.strapi_service import get_strapi_service
   ```

3. **Update API routes**:
   ```python
   # Old
   blog_service = get_blog_sync_service()

   # New
   strapi = get_strapi_service()
   articles = strapi.fetch_articles()
   ```

## Troubleshooting

### Connection Errors

**Problem**: `StrapiConnectionError: Failed to connect to Strapi`

**Solutions:**
1. Verify Strapi is running: `curl http://localhost:1337`
2. Check STRAPI_URL in `.env`
3. For Docker, use service name: `http://strapi:1337`

### Authentication Errors

**Problem**: `StrapiAuthenticationError: Authentication failed`

**Solutions:**
1. Verify API token in Strapi admin panel
2. Check STRAPI_API_TOKEN in `.env`
3. Ensure token has correct permissions

### Empty Results

**Problem**: `fetch_articles()` returns empty list

**Solutions:**
1. Verify articles exist in Strapi
2. Check articles are published
3. Verify API permissions allow reading articles

### Cache Issues

**Problem**: Stale data returned

**Solutions:**
1. Invalidate cache: `strapi.invalidate_cache()`
2. Disable cache temporarily: `fetch_articles(use_cache=False)`
3. Check Redis connection

## Best Practices

1. **Use Singleton**: Use `get_strapi_service()` for global instance
2. **Enable Caching**: Keep caching enabled in production
3. **Handle Errors**: Always wrap calls in try/except blocks
4. **Monitor Health**: Periodically call `health_check()`
5. **Invalidate Cache**: Clear cache when content changes
6. **Use Context Manager**: For temporary instances, use context manager
7. **Configure Timeouts**: Adjust timeouts based on network conditions
8. **Log Appropriately**: Configure logging for debugging

## Support

For issues or questions:
- Check logs: `tail -f /var/log/wwmaa/backend.log`
- Review Strapi docs: https://docs.strapi.io/dev-docs/api/rest
- Test connection: `strapi.health_check()`
