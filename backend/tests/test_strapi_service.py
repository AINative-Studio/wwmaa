"""
Unit Tests for Strapi Service

Tests the Strapi CMS integration service including:
- Article fetching
- Response transformation
- Error handling
- Caching behavior
- Authentication
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

from backend.services.strapi_service import (
    StrapiService,
    get_strapi_service,
    StrapiError,
    StrapiConnectionError,
    StrapiAuthenticationError,
    StrapiNotFoundError,
    StrapiValidationError
)


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    with patch('backend.services.strapi_service.get_cache_service') as mock:
        cache = MagicMock()
        cache.get.return_value = None  # Default: cache miss
        cache.set.return_value = True
        cache.clear_pattern.return_value = 5
        mock.return_value = cache
        yield cache


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('backend.services.strapi_service.settings') as mock:
        mock.STRAPI_URL = "http://localhost:1337"
        mock.STRAPI_API_TOKEN = "test_token"
        yield mock


@pytest.fixture
def strapi_service(mock_cache_service, mock_settings):
    """Create StrapiService instance with mocked dependencies"""
    service = StrapiService(
        strapi_url="http://localhost:1337",
        api_token="test_token"
    )
    service.cache = mock_cache_service
    return service


@pytest.fixture
def sample_strapi_response():
    """Sample Strapi API response"""
    return {
        "data": [
            {
                "id": 1,
                "attributes": {
                    "title": "Test Article",
                    "excerpt": "Test excerpt",
                    "content": "Test content",
                    "slug": "test-article",
                    "publishedAt": "2025-11-11T10:00:00.000Z",
                    "author": "Test Author",
                    "featured_image": {
                        "data": {
                            "attributes": {
                                "url": "/uploads/test.jpg"
                            }
                        }
                    },
                    "category": "Testing"
                }
            }
        ],
        "meta": {
            "pagination": {
                "page": 1,
                "pageSize": 50,
                "pageCount": 1,
                "total": 1
            }
        }
    }


@pytest.fixture
def sample_strapi_article():
    """Sample single Strapi article"""
    return {
        "id": 1,
        "attributes": {
            "title": "Test Article",
            "excerpt": "Test excerpt",
            "content": "Test content",
            "slug": "test-article",
            "publishedAt": "2025-11-11T10:00:00.000Z",
            "author": "Test Author",
            "featured_image": {
                "data": {
                    "attributes": {
                        "url": "/uploads/test.jpg"
                    }
                }
            },
            "category": "Testing"
        }
    }


class TestStrapiServiceInitialization:
    """Test service initialization"""

    def test_initialization_with_defaults(self, mock_cache_service, mock_settings):
        """Test service initializes with default settings"""
        service = StrapiService()

        assert service.strapi_url == "http://localhost:1337"
        assert service.api_token == "test_token"
        assert service.timeout == 10
        assert "Authorization" in service.headers
        assert service.headers["Authorization"] == "Bearer test_token"

    def test_initialization_with_custom_values(self, mock_cache_service):
        """Test service initializes with custom values"""
        service = StrapiService(
            strapi_url="http://custom:1337",
            api_token="custom_token",
            timeout=15,
            max_retries=5
        )

        assert service.strapi_url == "http://custom:1337"
        assert service.api_token == "custom_token"
        assert service.timeout == 15

    def test_initialization_without_token(self, mock_cache_service):
        """Test service initializes without API token"""
        service = StrapiService(
            strapi_url="http://localhost:1337",
            api_token=""
        )

        assert "Authorization" not in service.headers or service.headers["Authorization"] == "Bearer "

    def test_url_normalization(self, mock_cache_service):
        """Test URL is normalized (trailing slash removed)"""
        service = StrapiService(
            strapi_url="http://localhost:1337/",
            api_token="token"
        )

        assert service.strapi_url == "http://localhost:1337"


class TestFetchArticles:
    """Test fetch_articles method"""

    def test_fetch_articles_success(self, strapi_service, sample_strapi_response, mock_cache_service):
        """Test successful article fetch"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = sample_strapi_response
        mock_response.raise_for_status = Mock()

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            articles = strapi_service.fetch_articles(limit=10)

            assert len(articles) == 1
            assert articles[0]["title"] == "Test Article"
            assert articles[0]["slug"] == "test-article"

    def test_fetch_articles_from_cache(self, strapi_service, mock_cache_service):
        """Test articles fetched from cache"""
        cached_data = [{"id": "1", "title": "Cached Article"}]
        mock_cache_service.get.return_value = cached_data

        articles = strapi_service.fetch_articles()

        assert articles == cached_data
        mock_cache_service.get.assert_called_once()

    def test_fetch_articles_cache_disabled(self, strapi_service, sample_strapi_response, mock_cache_service):
        """Test fetch without cache"""
        mock_response = Mock()
        mock_response.json.return_value = sample_strapi_response
        mock_response.raise_for_status = Mock()

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            articles = strapi_service.fetch_articles(use_cache=False)

            # Cache should not be checked
            mock_cache_service.get.assert_not_called()

    def test_fetch_articles_connection_error(self, strapi_service):
        """Test connection error handling"""
        with patch.object(strapi_service.session, 'get', side_effect=requests.ConnectionError("Connection failed")):
            with pytest.raises(StrapiConnectionError):
                strapi_service.fetch_articles()

    def test_fetch_articles_timeout(self, strapi_service):
        """Test timeout error handling"""
        with patch.object(strapi_service.session, 'get', side_effect=requests.Timeout("Timeout")):
            with pytest.raises(StrapiConnectionError):
                strapi_service.fetch_articles()

    def test_fetch_articles_http_error_401(self, strapi_service):
        """Test 401 authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_response.json.return_value = {"error": {"message": "Unauthorized"}}

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            with pytest.raises(StrapiAuthenticationError):
                strapi_service.fetch_articles()

    def test_fetch_articles_http_error_404(self, strapi_service):
        """Test 404 not found error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_response.json.return_value = {"error": {"message": "Not found"}}

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            with pytest.raises(StrapiNotFoundError):
                strapi_service.fetch_articles()

    def test_fetch_articles_http_error_400(self, strapi_service):
        """Test 400 validation error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_response.json.return_value = {"error": {"message": "Bad request"}}

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            with pytest.raises(StrapiValidationError):
                strapi_service.fetch_articles()


class TestFetchArticleBySlug:
    """Test fetch_article_by_slug method"""

    def test_fetch_by_slug_success(self, strapi_service, sample_strapi_response):
        """Test successful fetch by slug"""
        mock_response = Mock()
        mock_response.json.return_value = sample_strapi_response
        mock_response.raise_for_status = Mock()

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            article = strapi_service.fetch_article_by_slug("test-article")

            assert article is not None
            assert article["title"] == "Test Article"
            assert article["slug"] == "test-article"

    def test_fetch_by_slug_not_found(self, strapi_service):
        """Test article not found"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            article = strapi_service.fetch_article_by_slug("nonexistent")

            assert article is None

    def test_fetch_by_slug_from_cache(self, strapi_service, mock_cache_service):
        """Test fetch by slug from cache"""
        cached_article = {"id": "1", "title": "Cached Article", "slug": "test"}
        mock_cache_service.get.return_value = cached_article

        article = strapi_service.fetch_article_by_slug("test")

        assert article == cached_article


class TestTransformStrapiToArticle:
    """Test transform_strapi_to_article method"""

    def test_transform_basic_article(self, strapi_service, sample_strapi_article):
        """Test basic article transformation"""
        transformed = strapi_service.transform_strapi_to_article(sample_strapi_article)

        assert transformed["id"] == "1"
        assert transformed["title"] == "Test Article"
        assert transformed["slug"] == "test-article"
        assert transformed["excerpt"] == "Test excerpt"
        assert transformed["author"] == "Test Author"
        assert transformed["category"] == "Testing"

    def test_transform_url_generation(self, strapi_service, sample_strapi_article):
        """Test URL generation"""
        transformed = strapi_service.transform_strapi_to_article(sample_strapi_article)

        assert transformed["url"] == "https://wwmaa.com/blog/test-article"

    def test_transform_image_url(self, strapi_service, sample_strapi_article):
        """Test image URL transformation"""
        transformed = strapi_service.transform_strapi_to_article(sample_strapi_article)

        assert transformed["image_url"] == "http://localhost:1337/uploads/test.jpg"

    def test_transform_missing_image(self, strapi_service):
        """Test transformation with missing image"""
        article = {
            "id": 1,
            "attributes": {
                "title": "Test",
                "slug": "test",
                "publishedAt": "2025-11-11T10:00:00.000Z",
                "author": "Author"
            }
        }

        transformed = strapi_service.transform_strapi_to_article(article)

        assert transformed["image_url"] == ""

    def test_transform_published_at_format(self, strapi_service, sample_strapi_article):
        """Test publishedAt timestamp format"""
        transformed = strapi_service.transform_strapi_to_article(sample_strapi_article)

        assert transformed["published_at"].endswith("Z")
        assert "2025-11-11" in transformed["published_at"]

    def test_transform_with_missing_fields(self, strapi_service):
        """Test transformation with missing optional fields"""
        article = {
            "id": 1,
            "attributes": {
                "title": "Minimal Article",
                "slug": "minimal"
            }
        }

        transformed = strapi_service.transform_strapi_to_article(article)

        assert transformed["id"] == "1"
        assert transformed["title"] == "Minimal Article"
        assert transformed["excerpt"] == ""
        assert transformed["category"] == ""

    def test_transform_error_handling(self, strapi_service):
        """Test transformation error handling"""
        invalid_article = {"id": 1}  # Missing attributes

        transformed = strapi_service.transform_strapi_to_article(invalid_article)

        # Should return minimal valid article
        assert "id" in transformed
        assert "title" in transformed


class TestCacheManagement:
    """Test cache management methods"""

    def test_invalidate_cache_all(self, strapi_service, mock_cache_service):
        """Test invalidating all article cache"""
        mock_cache_service.clear_pattern.return_value = 10

        deleted_count = strapi_service.invalidate_cache()

        assert deleted_count == 10
        mock_cache_service.clear_pattern.assert_called_once()

    def test_invalidate_cache_pattern(self, strapi_service, mock_cache_service):
        """Test invalidating specific cache pattern"""
        mock_cache_service.clear_pattern.return_value = 3

        deleted_count = strapi_service.invalidate_cache("strapi:articles:slug:*")

        assert deleted_count == 3


class TestHealthCheck:
    """Test health check method"""

    def test_health_check_success(self, strapi_service):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()

        with patch.object(strapi_service.session, 'get', return_value=mock_response):
            health = strapi_service.health_check()

            assert health["status"] == "healthy"
            assert health["strapi_url"] == "http://localhost:1337"
            assert health["authenticated"] is True

    def test_health_check_failure(self, strapi_service):
        """Test failed health check"""
        with patch.object(strapi_service.session, 'get', side_effect=requests.ConnectionError("Failed")):
            health = strapi_service.health_check()

            assert health["status"] == "unhealthy"
            assert "error" in health


class TestUtilityMethods:
    """Test utility methods"""

    def test_build_url(self, strapi_service):
        """Test URL building"""
        url = strapi_service._build_url("api", "articles")
        assert url == "http://localhost:1337/api/articles"

    def test_build_url_with_trailing_slashes(self, strapi_service):
        """Test URL building with trailing slashes"""
        url = strapi_service._build_url("/api/", "/articles/")
        assert url == "http://localhost:1337/api/articles"


class TestContextManager:
    """Test context manager functionality"""

    def test_context_manager(self, mock_cache_service, mock_settings):
        """Test using service as context manager"""
        with StrapiService() as service:
            assert isinstance(service, StrapiService)

        # Session should be closed after context exit


class TestSingleton:
    """Test singleton pattern"""

    def test_get_strapi_service_singleton(self, mock_cache_service, mock_settings):
        """Test get_strapi_service returns singleton"""
        service1 = get_strapi_service()
        service2 = get_strapi_service()

        assert service1 is service2


@pytest.mark.integration
class TestIntegration:
    """Integration tests (require running Strapi instance)"""

    @pytest.mark.skip(reason="Requires running Strapi instance")
    def test_real_strapi_connection(self):
        """Test actual Strapi connection"""
        service = StrapiService(
            strapi_url="http://localhost:1337",
            api_token="real_token_here"
        )

        health = service.health_check()
        assert health["status"] == "healthy"

    @pytest.mark.skip(reason="Requires running Strapi instance")
    def test_real_fetch_articles(self):
        """Test fetching real articles"""
        service = StrapiService(
            strapi_url="http://localhost:1337",
            api_token="real_token_here"
        )

        articles = service.fetch_articles(limit=5)
        assert isinstance(articles, list)
