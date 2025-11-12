"""
Strapi CMS Integration Service for WWMAA Backend

Provides integration with Strapi CMS for fetching blog articles.
Includes HTTP client, response transformation, authentication,
error handling with retry logic, and Redis caching.

Features:
- Fetch articles from Strapi REST API
- Transform Strapi response to Article model
- API token authentication
- Exponential backoff retry logic
- Redis caching with 5-minute TTL
- Connection pooling
- Comprehensive error handling

Strapi API Documentation: https://docs.strapi.io/dev-docs/api/rest
"""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.config import settings
from backend.services.instrumented_cache_service import get_cache_service

# Configure logging
logger = logging.getLogger(__name__)


class StrapiError(Exception):
    """Base exception for Strapi service errors"""
    pass


class StrapiConnectionError(StrapiError):
    """Exception raised for connection errors"""
    pass


class StrapiAuthenticationError(StrapiError):
    """Exception raised for authentication errors"""
    pass


class StrapiNotFoundError(StrapiError):
    """Exception raised when a resource is not found"""
    pass


class StrapiValidationError(StrapiError):
    """Exception raised for validation errors"""
    pass


class StrapiService:
    """
    Strapi CMS Integration Service

    Provides methods for:
    - Fetching articles from Strapi API
    - Transforming Strapi responses to Article model
    - API token authentication
    - Automatic retry with exponential backoff
    - Redis caching with 5-minute TTL
    - Connection pooling
    - Comprehensive error handling
    """

    # Cache configuration
    CACHE_KEY_PREFIX = "strapi:articles"
    CACHE_TTL = 300  # 5 minutes in seconds

    def __init__(
        self,
        strapi_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
        pool_connections: int = 10,
        pool_maxsize: int = 10
    ):
        """
        Initialize Strapi Service

        Args:
            strapi_url: Strapi API base URL (defaults to settings.STRAPI_URL)
            api_token: Strapi API token (defaults to settings.STRAPI_API_TOKEN)
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum number of retries for failed requests (default: 3)
            pool_connections: Number of connection pool connections (default: 10)
            pool_maxsize: Maximum size of connection pool (default: 10)
        """
        self.strapi_url = (strapi_url or getattr(settings, 'STRAPI_URL', 'http://localhost:1337')).rstrip('/')
        self.api_token = api_token or getattr(settings, 'STRAPI_API_TOKEN', '')
        self.timeout = timeout

        # Initialize cache service
        self.cache = get_cache_service()

        # Validate configuration
        if not self.strapi_url:
            raise StrapiError("STRAPI_URL is required")

        # Log warning if API token is missing
        if not self.api_token:
            logger.warning("STRAPI_API_TOKEN not configured. Public API access only.")

        # Configure headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Add authorization header if token provided
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

        # Configure session with connection pooling and retry logic
        self.session = self._create_session(max_retries, pool_connections, pool_maxsize)

        logger.info(f"StrapiService initialized with base_url: {self.strapi_url}")

    def _create_session(
        self,
        max_retries: int,
        pool_connections: int,
        pool_maxsize: int
    ) -> requests.Session:
        """
        Create a requests session with connection pooling and retry logic

        Args:
            max_retries: Maximum number of retries
            pool_connections: Number of connection pool connections
            pool_maxsize: Maximum size of connection pool

        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, *parts: str) -> str:
        """
        Build a full URL from base URL and path parts

        Args:
            *parts: URL path parts to join

        Returns:
            Complete URL string
        """
        path = "/".join(str(part).strip("/") for part in parts if part)
        return urljoin(self.strapi_url + "/", path)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions

        Args:
            response: Response object from requests

        Returns:
            JSON response data

        Raises:
            StrapiAuthenticationError: For 401/403 errors
            StrapiNotFoundError: For 404 errors
            StrapiValidationError: For 400/422 errors
            StrapiError: For other errors
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = response.json()
            except ValueError:
                error_data = {"detail": response.text}

            error_message = (
                error_data.get("error", {}).get("message") or
                error_data.get("detail") or
                error_data.get("message") or
                str(e)
            )

            if response.status_code in (401, 403):
                logger.error(f"Authentication error: {error_message}")
                raise StrapiAuthenticationError(f"Authentication failed: {error_message}")
            elif response.status_code == 404:
                logger.warning(f"Resource not found: {error_message}")
                raise StrapiNotFoundError(f"Resource not found: {error_message}")
            elif response.status_code in (400, 422):
                logger.error(f"Validation error: {error_message}")
                raise StrapiValidationError(f"Validation error: {error_message}")
            else:
                logger.error(f"API error: {error_message}")
                raise StrapiError(f"API error ({response.status_code}): {error_message}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise StrapiConnectionError(f"Failed to connect to Strapi: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise StrapiConnectionError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise StrapiError(f"Request failed: {e}")

    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get data from Redis cache

        Args:
            cache_key: Cache key to retrieve

        Returns:
            Cached data or None if not found or on error
        """
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_data
            logger.debug(f"Cache miss: {cache_key}")
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error for key {cache_key}: {e}")
            return None

    def _set_in_cache(self, cache_key: str, data: List[Dict[str, Any]]) -> bool:
        """
        Store data in Redis cache with TTL

        Args:
            cache_key: Cache key to store under
            data: Data to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.cache.set(cache_key, data, expiration=self.CACHE_TTL)
            if success:
                logger.debug(f"Cached data with key: {cache_key} (TTL: {self.CACHE_TTL}s)")
            return success
        except Exception as e:
            logger.warning(f"Cache storage error for key {cache_key}: {e}")
            return False

    def fetch_articles(
        self,
        limit: int = 50,
        sort: str = "publishedAt:desc",
        populate: str = "*",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from Strapi API

        Args:
            limit: Maximum number of articles to fetch (default: 50)
            sort: Sort order (default: "publishedAt:desc")
            populate: Fields to populate (default: "*")
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            List of transformed article dictionaries

        Raises:
            StrapiError: If fetch fails
        """
        # Generate cache key
        cache_key = f"{self.CACHE_KEY_PREFIX}:list:{limit}:{sort}"

        # Try cache first if enabled
        if use_cache:
            cached_articles = self._get_from_cache(cache_key)
            if cached_articles is not None:
                logger.info(f"Returning {len(cached_articles)} articles from cache")
                return cached_articles

        # Fetch from Strapi API
        try:
            url = self._build_url("api", "articles")

            params = {
                "populate": populate,
                "sort": sort,
                "pagination[limit]": limit
            }

            logger.info(f"Fetching articles from Strapi: {url}")
            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            result = self._handle_response(response)

            # Extract articles from Strapi response
            strapi_articles = result.get("data", [])
            logger.info(f"Fetched {len(strapi_articles)} articles from Strapi")

            # Transform to our Article model format
            transformed_articles = [
                self.transform_strapi_to_article(article)
                for article in strapi_articles
            ]

            # Cache the results
            if use_cache and transformed_articles:
                self._set_in_cache(cache_key, transformed_articles)

            return transformed_articles

        except StrapiError:
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise StrapiConnectionError(f"Failed to connect to Strapi: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise StrapiConnectionError(f"Request timed out: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching articles: {e}")
            raise StrapiError(f"Failed to fetch articles: {e}")

    def fetch_article_by_slug(
        self,
        slug: str,
        populate: str = "*",
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single article by slug

        Args:
            slug: Article slug
            populate: Fields to populate (default: "*")
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            Transformed article dictionary or None if not found

        Raises:
            StrapiError: If fetch fails
        """
        # Generate cache key
        cache_key = f"{self.CACHE_KEY_PREFIX}:slug:{slug}"

        # Try cache first if enabled
        if use_cache:
            cached_article = self.cache.get(cache_key)
            if cached_article:
                logger.info(f"Returning article from cache: {slug}")
                return cached_article

        # Fetch from Strapi API
        try:
            url = self._build_url("api", "articles")

            params = {
                "filters[slug][$eq]": slug,
                "populate": populate
            }

            logger.info(f"Fetching article by slug from Strapi: {slug}")
            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )

            result = self._handle_response(response)

            # Extract articles from Strapi response
            strapi_articles = result.get("data", [])

            if not strapi_articles:
                logger.warning(f"Article not found: {slug}")
                return None

            # Transform to our Article model format
            article = self.transform_strapi_to_article(strapi_articles[0])

            # Cache the result
            if use_cache:
                self.cache.set(cache_key, article, expiration=self.CACHE_TTL)

            return article

        except StrapiNotFoundError:
            return None
        except StrapiError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching article by slug {slug}: {e}")
            raise StrapiError(f"Failed to fetch article: {e}")

    def transform_strapi_to_article(self, strapi_article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Strapi article response to our Article model format

        Strapi format:
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

        Our format:
        {
          "id": "1",
          "title": "Article Title",
          "excerpt": "Short description",
          "url": "https://wwmaa.com/blog/article-title",
          "published_at": "2025-11-11T10:00:00Z",
          "author": "John Doe",
          "image_url": "https://wwmaa.com/uploads/image.jpg",
          "category": "Training"
        }

        Args:
            strapi_article: Strapi article data with id and attributes

        Returns:
            Transformed article dictionary
        """
        try:
            article_id = str(strapi_article.get("id", ""))
            attributes = strapi_article.get("attributes", {})

            # Extract basic fields
            title = attributes.get("title", "Untitled")
            excerpt = attributes.get("excerpt", "")
            content = attributes.get("content", "")
            slug = attributes.get("slug", "")
            author = attributes.get("author", "Unknown")
            category = attributes.get("category", "")

            # Parse published_at timestamp
            published_at = attributes.get("publishedAt", "")
            if published_at:
                try:
                    # Ensure ISO 8601 format with Z suffix
                    if not published_at.endswith('Z'):
                        published_at = published_at.rstrip('0').rstrip('.') + 'Z'
                except Exception as e:
                    logger.warning(f"Error parsing publishedAt: {e}")
                    published_at = datetime.utcnow().isoformat() + 'Z'

            # Build article URL
            article_url = f"https://wwmaa.com/blog/{slug}" if slug else "https://wwmaa.com/blog"

            # Extract featured image URL
            image_url = ""
            featured_image = attributes.get("featured_image", {})
            if featured_image and isinstance(featured_image, dict):
                # Handle both direct URL and nested data structure
                if "data" in featured_image:
                    image_data = featured_image.get("data", {})
                    if image_data and isinstance(image_data, dict):
                        image_attributes = image_data.get("attributes", {})
                        image_url = image_attributes.get("url", "")
                else:
                    image_url = featured_image.get("url", "")

                # Make image URL absolute if relative
                if image_url and not image_url.startswith("http"):
                    image_url = self.strapi_url + image_url

            # Build transformed article
            transformed = {
                "id": article_id,
                "title": title,
                "excerpt": excerpt,
                "content": content,
                "url": article_url,
                "slug": slug,
                "published_at": published_at,
                "author": author,
                "image_url": image_url,
                "category": category
            }

            return transformed

        except Exception as e:
            logger.error(f"Error transforming Strapi article: {e}")
            # Return minimal valid article on error
            return {
                "id": str(strapi_article.get("id", "")),
                "title": "Error loading article",
                "excerpt": "",
                "content": "",
                "url": "https://wwmaa.com/blog",
                "slug": "",
                "published_at": datetime.utcnow().isoformat() + 'Z',
                "author": "Unknown",
                "image_url": "",
                "category": ""
            }

    def invalidate_cache(self, cache_key_pattern: Optional[str] = None) -> int:
        """
        Invalidate cached articles

        Args:
            cache_key_pattern: Specific cache key pattern to invalidate
                             (default: None, invalidates all article cache)

        Returns:
            Number of cache keys deleted
        """
        try:
            pattern = cache_key_pattern or f"{self.CACHE_KEY_PREFIX}:*"
            deleted_count = self.cache.clear_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries matching: {pattern}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Strapi connection

        Returns:
            Dictionary with health status
        """
        try:
            # Try to fetch one article to verify connection
            url = self._build_url("api", "articles")
            params = {"pagination[limit]": 1}

            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=5
            )

            response.raise_for_status()

            return {
                "status": "healthy",
                "strapi_url": self.strapi_url,
                "authenticated": bool(self.api_token),
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "strapi_url": self.strapi_url,
                "authenticated": bool(self.api_token),
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }

    def close(self):
        """Close the session and clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
            logger.info("StrapiService session closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global Strapi service instance (singleton pattern)
_strapi_service_instance: Optional[StrapiService] = None


def get_strapi_service() -> StrapiService:
    """
    Get or create the global StrapiService instance

    Returns:
        StrapiService instance
    """
    global _strapi_service_instance

    if _strapi_service_instance is None:
        _strapi_service_instance = StrapiService()

    return _strapi_service_instance
