"""
Comprehensive Tests for Blog Sync Service

Tests all functionality of the BeeHiiv blog synchronization service.

Test Coverage:
- Webhook signature verification
- Post syncing (create/update/delete)
- Image download and storage
- Slug generation and deduplication
- SEO metadata extraction
- HTML sanitization
- Read time calculation
- Full sync functionality
- Error handling

Target: 80%+ code coverage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
import hashlib
import hmac
import json

from backend.services.blog_sync_service import (
    BlogSyncService,
    BlogSyncError,
    BeeHiivAPIError,
    ImageDownloadError
)
from backend.models.schemas import (
    Article,
    ArticleAuthor,
    ArticleSEOMetadata,
    ArticleStatus
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def blog_sync_service():
    """Create BlogSyncService instance with mocked dependencies"""
    with patch('backend.services.blog_sync_service.get_zerodb_client'):
        service = BlogSyncService()
        service.beehiiv_api_key = 'test_api_key'
        service.beehiiv_publication_id = 'test_pub_id'
        service.beehiiv_webhook_secret = 'test_secret'
        return service


@pytest.fixture
def sample_beehiiv_post():
    """Sample BeeHiiv post data"""
    return {
        'id': 'post_12345',
        'title': 'Getting Started with Martial Arts',
        'content_html': '<p>This is a <strong>great</strong> article about martial arts.</p>',
        'excerpt': 'A beginner\'s guide to martial arts',
        'author': {
            'name': 'John Doe',
            'email': 'john@example.com',
            'avatar_url': 'https://example.com/avatar.jpg'
        },
        'published_at': '2025-11-10T12:00:00Z',
        'status': 'published',
        'thumbnail_url': 'https://example.com/image.jpg',
        'web_url': 'https://beehiiv.com/post/getting-started',
        'categories': ['Beginners'],
        'tags': ['martial-arts', 'training', 'beginners']
    }


@pytest.fixture
def sample_article_data():
    """Sample Article model data"""
    return {
        'beehiiv_post_id': 'post_12345',
        'beehiiv_url': 'https://beehiiv.com/post/getting-started',
        'title': 'Getting Started with Martial Arts',
        'slug': 'getting-started-with-martial-arts',
        'excerpt': 'A beginner\'s guide to martial arts',
        'content': '<p>This is a <strong>great</strong> article about martial arts.</p>',
        'content_format': 'html',
        'author': ArticleAuthor(
            name='John Doe',
            email='john@example.com',
            avatar_url='https://example.com/avatar.jpg'
        ),
        'category': 'Beginners',
        'tags': ['martial-arts', 'training', 'beginners'],
        'status': ArticleStatus.PUBLISHED,
        'published_at': datetime(2025, 11, 10, 12, 0, 0),
        'view_count': 0,
        'read_time_minutes': 1,
        'seo_metadata': ArticleSEOMetadata(),
        'last_synced_at': datetime.utcnow(),
        'sync_source': 'beehiiv'
    }


# ============================================================================
# WEBHOOK SIGNATURE VERIFICATION TESTS
# ============================================================================

class TestWebhookSignatureVerification:
    """Test webhook signature verification"""

    def test_verify_valid_signature(self, blog_sync_service):
        """Test verification of valid webhook signature"""
        payload = b'{"event": "post.published", "data": {"id": "123"}}'

        # Generate valid signature
        signature = hmac.new(
            blog_sync_service.beehiiv_webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert blog_sync_service.verify_webhook_signature(payload, signature) is True

    def test_verify_invalid_signature(self, blog_sync_service):
        """Test rejection of invalid webhook signature"""
        payload = b'{"event": "post.published", "data": {"id": "123"}}'
        invalid_signature = 'invalid_signature_12345'

        assert blog_sync_service.verify_webhook_signature(payload, invalid_signature) is False

    def test_verify_signature_no_secret_configured(self, blog_sync_service):
        """Test signature verification when secret not configured"""
        blog_sync_service.beehiiv_webhook_secret = None
        payload = b'{"event": "post.published"}'

        # Should return True (skip verification) with warning
        assert blog_sync_service.verify_webhook_signature(payload, 'any_signature') is True

    def test_verify_signature_error_handling(self, blog_sync_service):
        """Test signature verification error handling"""
        payload = b'test'

        # Pass invalid signature format to trigger exception
        with patch('hmac.new', side_effect=Exception('HMAC error')):
            assert blog_sync_service.verify_webhook_signature(payload, 'sig') is False


# ============================================================================
# SLUG GENERATION TESTS
# ============================================================================

class TestSlugGeneration:
    """Test slug generation and deduplication"""

    def test_generate_slug_basic(self, blog_sync_service):
        """Test basic slug generation"""
        title = "Getting Started with Martial Arts"
        slug = blog_sync_service._generate_slug(title)

        assert slug == "getting-started-with-martial-arts"

    def test_generate_slug_special_characters(self, blog_sync_service):
        """Test slug generation with special characters"""
        title = "Beginner's Guide: Top 10 Martial Arts!"
        slug = blog_sync_service._generate_slug(title)

        assert slug == "beginners-guide-top-10-martial-arts"

    def test_generate_slug_unicode(self, blog_sync_service):
        """Test slug generation with unicode characters"""
        title = "Karate: 空手の基本"
        slug = blog_sync_service._generate_slug(title)

        # Should strip unicode, keep ASCII
        assert slug == "karate"

    def test_generate_slug_max_length(self, blog_sync_service):
        """Test slug length limitation"""
        title = "A" * 300  # Very long title
        slug = blog_sync_service._generate_slug(title)

        assert len(slug) <= 200

    def test_generate_slug_empty_title(self, blog_sync_service):
        """Test slug generation with empty title"""
        title = ""
        slug = blog_sync_service._generate_slug(title)

        assert slug == "untitled-post"

    def test_ensure_unique_slug_no_conflict(self, blog_sync_service):
        """Test slug uniqueness when no conflict exists"""
        blog_sync_service.zerodb.query_documents = Mock(return_value=[])

        slug = blog_sync_service._ensure_unique_slug("test-slug")

        assert slug == "test-slug"

    def test_ensure_unique_slug_with_conflict(self, blog_sync_service):
        """Test slug uniqueness with existing slug"""
        # First call returns existing, second call returns empty
        blog_sync_service.zerodb.query_documents = Mock(
            side_effect=[
                [{'slug': 'test-slug'}],  # Original exists
                [{'slug': 'test-slug-1'}],  # -1 exists
                []  # -2 doesn't exist
            ]
        )

        slug = blog_sync_service._ensure_unique_slug("test-slug")

        assert slug == "test-slug-2"


# ============================================================================
# HTML SANITIZATION TESTS
# ============================================================================

class TestHTMLSanitization:
    """Test HTML content sanitization"""

    def test_sanitize_safe_html(self, blog_sync_service):
        """Test sanitization of safe HTML"""
        html = '<p>Safe <strong>content</strong></p>'

        with patch('bleach.clean', return_value=html):
            sanitized = blog_sync_service._sanitize_html(html)
            assert sanitized == html

    def test_sanitize_malicious_script(self, blog_sync_service):
        """Test removal of malicious scripts"""
        html = '<p>Content</p><script>alert("XSS")</script>'
        expected = '<p>Content</p>'

        with patch('bleach.clean', return_value=expected):
            sanitized = blog_sync_service._sanitize_html(html)
            assert 'script' not in sanitized.lower()

    def test_sanitize_bleach_not_installed(self, blog_sync_service):
        """Test sanitization fallback when bleach not installed"""
        html = '<p>Content</p>'

        with patch('builtins.__import__', side_effect=ImportError):
            sanitized = blog_sync_service._sanitize_html(html)
            # Should return original when bleach not available
            assert sanitized == html


# ============================================================================
# READ TIME CALCULATION TESTS
# ============================================================================

class TestReadTimeCalculation:
    """Test read time calculation"""

    def test_calculate_read_time_short_article(self, blog_sync_service):
        """Test read time for short article"""
        content = ' '.join(['word'] * 100)  # 100 words
        read_time = blog_sync_service._calculate_read_time(content)

        # Should be minimum 1 minute
        assert read_time == 1

    def test_calculate_read_time_medium_article(self, blog_sync_service):
        """Test read time for medium article"""
        content = ' '.join(['word'] * 600)  # 600 words (3 minutes at 200 wpm)
        read_time = blog_sync_service._calculate_read_time(content)

        assert read_time == 3

    def test_calculate_read_time_html_content(self, blog_sync_service):
        """Test read time calculation strips HTML"""
        content = '<p>' + ' '.join(['word'] * 200) + '</p><div>More content</div>'
        read_time = blog_sync_service._calculate_read_time(content)

        # Should count only text, not HTML tags
        assert read_time >= 1


# ============================================================================
# EXCERPT GENERATION TESTS
# ============================================================================

class TestExcerptGeneration:
    """Test excerpt generation from content"""

    def test_generate_excerpt_short_content(self, blog_sync_service):
        """Test excerpt from short content"""
        content = "This is a short article."
        excerpt = blog_sync_service._generate_excerpt(content)

        assert excerpt == "This is a short article."

    def test_generate_excerpt_long_content(self, blog_sync_service):
        """Test excerpt truncation for long content"""
        content = ' '.join(['word'] * 200)  # Very long content
        excerpt = blog_sync_service._generate_excerpt(content, max_length=100)

        assert len(excerpt) <= 103  # 100 + '...'
        assert excerpt.endswith('...')

    def test_generate_excerpt_html_content(self, blog_sync_service):
        """Test excerpt generation strips HTML"""
        content = '<p>This is <strong>important</strong> content.</p>'
        excerpt = blog_sync_service._generate_excerpt(content)

        assert '<p>' not in excerpt
        assert '<strong>' not in excerpt
        assert 'important' in excerpt


# ============================================================================
# SEO METADATA EXTRACTION TESTS
# ============================================================================

class TestSEOMetadataExtraction:
    """Test SEO metadata extraction"""

    def test_extract_seo_metadata_complete(self, blog_sync_service, sample_beehiiv_post):
        """Test extraction with complete metadata"""
        sample_beehiiv_post['meta_title'] = 'Custom Meta Title'
        sample_beehiiv_post['meta_description'] = 'Custom description'
        sample_beehiiv_post['og_title'] = 'OG Title'

        seo = blog_sync_service._extract_seo_metadata(
            sample_beehiiv_post,
            'Default Title'
        )

        assert seo.meta_title == 'Custom Meta Title'
        assert seo.meta_description == 'Custom description'
        assert seo.og_title == 'OG Title'
        assert seo.twitter_card == 'summary_large_image'
        assert len(seo.keywords) > 0

    def test_extract_seo_metadata_defaults(self, blog_sync_service, sample_beehiiv_post):
        """Test extraction with default values"""
        title = 'Test Title'

        seo = blog_sync_service._extract_seo_metadata(sample_beehiiv_post, title)

        # Should use defaults when specific fields not provided
        assert seo.meta_title == title
        assert seo.og_title == title
        assert seo.canonical_url == sample_beehiiv_post['web_url']


# ============================================================================
# POST TRANSFORMATION TESTS
# ============================================================================

class TestPostTransformation:
    """Test BeeHiiv post to Article transformation"""

    def test_transform_beehiiv_to_article(self, blog_sync_service, sample_beehiiv_post):
        """Test complete transformation"""
        with patch.object(blog_sync_service, '_sanitize_html', return_value='<p>Clean content</p>'):
            with patch.object(blog_sync_service, '_generate_slug', return_value='test-slug'):
                with patch.object(blog_sync_service, '_calculate_read_time', return_value=5):
                    with patch.object(blog_sync_service, '_download_and_store_image', return_value='https://stored.com/image.jpg'):
                        with patch.object(blog_sync_service, '_generate_thumbnail', return_value='https://stored.com/thumb.jpg'):
                            article_data = blog_sync_service.transform_beehiiv_to_article(sample_beehiiv_post)

        assert article_data['beehiiv_post_id'] == 'post_12345'
        assert article_data['title'] == 'Getting Started with Martial Arts'
        assert article_data['slug'] == 'test-slug'
        assert article_data['status'] == ArticleStatus.PUBLISHED
        assert article_data['read_time_minutes'] == 5
        assert isinstance(article_data['author'], ArticleAuthor)
        assert isinstance(article_data['seo_metadata'], ArticleSEOMetadata)

    def test_transform_draft_post(self, blog_sync_service, sample_beehiiv_post):
        """Test transformation of draft post"""
        sample_beehiiv_post['status'] = 'draft'

        with patch.object(blog_sync_service, '_sanitize_html', return_value='content'):
            with patch.object(blog_sync_service, '_generate_slug', return_value='slug'):
                with patch.object(blog_sync_service, '_calculate_read_time', return_value=1):
                    article_data = blog_sync_service.transform_beehiiv_to_article(sample_beehiiv_post)

        assert article_data['status'] == ArticleStatus.DRAFT
        assert article_data['published_at'] is None


# ============================================================================
# POST SYNC TESTS
# ============================================================================

class TestPostSync:
    """Test post synchronization"""

    def test_sync_new_post(self, blog_sync_service, sample_beehiiv_post):
        """Test syncing a new post"""
        blog_sync_service.zerodb.query_documents = Mock(return_value=[])
        blog_sync_service.zerodb.create_document = Mock(return_value={'id': str(uuid4())})

        with patch.object(blog_sync_service, 'transform_beehiiv_to_article') as mock_transform:
            mock_transform.return_value = {
                'beehiiv_post_id': 'post_12345',
                'title': 'Test Post',
                'slug': 'test-post',
                'content': '<p>Content</p>',
                'author': ArticleAuthor(name='Test Author'),
                'seo_metadata': ArticleSEOMetadata(),
                'status': ArticleStatus.PUBLISHED
            }

            with patch.object(blog_sync_service, '_ensure_unique_slug', return_value='test-post'):
                article = blog_sync_service.sync_post(sample_beehiiv_post)

        assert blog_sync_service.zerodb.create_document.called

    def test_sync_existing_post_update(self, blog_sync_service, sample_beehiiv_post):
        """Test updating an existing post"""
        existing_article = Mock(id=uuid4())
        blog_sync_service._get_article_by_beehiiv_id = Mock(return_value=existing_article)

        with patch.object(blog_sync_service, 'transform_beehiiv_to_article') as mock_transform:
            with patch.object(blog_sync_service, 'update_post') as mock_update:
                mock_transform.return_value = {'title': 'Updated Title'}
                mock_update.return_value = Mock(id=existing_article.id)

                article = blog_sync_service.sync_post(sample_beehiiv_post)

                mock_update.assert_called_once()

    def test_sync_post_missing_id(self, blog_sync_service):
        """Test sync fails without post ID"""
        with pytest.raises(BlogSyncError, match="Missing post ID"):
            blog_sync_service.sync_post({})

    def test_sync_post_error_handling(self, blog_sync_service, sample_beehiiv_post):
        """Test sync error handling"""
        blog_sync_service._get_article_by_beehiiv_id = Mock(
            side_effect=Exception('Database error')
        )

        with pytest.raises(BlogSyncError):
            blog_sync_service.sync_post(sample_beehiiv_post)


# ============================================================================
# UPDATE POST TESTS
# ============================================================================

class TestUpdatePost:
    """Test post update functionality"""

    def test_update_post_success(self, blog_sync_service):
        """Test successful post update"""
        article_id = uuid4()
        updates = {'title': 'Updated Title', 'content': 'Updated content'}

        blog_sync_service.zerodb.update_document = Mock()
        blog_sync_service.zerodb.get_document = Mock(return_value={
            'id': str(article_id),
            'beehiiv_post_id': 'post_123',
            'title': 'Updated Title',
            'slug': 'test',
            'content': 'Updated content',
            'author': {'name': 'Test'},
            'seo_metadata': {},
            'status': 'published'
        })

        with patch('backend.services.blog_sync_service.Article'):
            article = blog_sync_service.update_post(article_id, updates)

            blog_sync_service.zerodb.update_document.assert_called_once()

    def test_update_post_removes_protected_fields(self, blog_sync_service):
        """Test that protected fields are not updated"""
        article_id = uuid4()
        updates = {'id': 'new_id', 'created_at': datetime.utcnow(), 'title': 'New Title'}

        blog_sync_service.zerodb.update_document = Mock()
        blog_sync_service.zerodb.get_document = Mock(return_value={
            'id': str(article_id),
            'beehiiv_post_id': 'post_123',
            'title': 'New Title',
            'slug': 'test',
            'content': 'content',
            'author': {'name': 'Test'},
            'seo_metadata': {},
            'status': 'published'
        })

        with patch('backend.services.blog_sync_service.Article'):
            blog_sync_service.update_post(article_id, updates)

            # Verify protected fields were removed
            call_args = blog_sync_service.zerodb.update_document.call_args[0][2]
            assert 'id' not in call_args
            assert 'created_at' not in call_args


# ============================================================================
# DELETE POST TESTS
# ============================================================================

class TestDeletePost:
    """Test post deletion (archiving)"""

    def test_delete_post_success(self, blog_sync_service):
        """Test successful post deletion"""
        article_id = uuid4()
        blog_sync_service.zerodb.update_document = Mock()

        result = blog_sync_service.delete_post(article_id)

        assert result is True
        blog_sync_service.zerodb.update_document.assert_called_once()

        # Verify it's a soft delete (status = archived)
        call_args = blog_sync_service.zerodb.update_document.call_args[0][2]
        assert call_args['status'] == ArticleStatus.ARCHIVED

    def test_delete_post_error(self, blog_sync_service):
        """Test delete post error handling"""
        article_id = uuid4()
        blog_sync_service.zerodb.update_document = Mock(
            side_effect=Exception('Database error')
        )

        result = blog_sync_service.delete_post(article_id)

        assert result is False


# ============================================================================
# FULL SYNC TESTS
# ============================================================================

class TestFullSync:
    """Test full synchronization"""

    def test_sync_all_posts_success(self, blog_sync_service, sample_beehiiv_post):
        """Test successful full sync"""
        posts = [sample_beehiiv_post, {**sample_beehiiv_post, 'id': 'post_67890'}]

        blog_sync_service._fetch_all_posts_from_beehiiv = Mock(return_value=posts)
        blog_sync_service.sync_post = Mock(return_value=Mock(id=uuid4()))

        articles = blog_sync_service.sync_all_posts()

        assert len(articles) == 2
        assert blog_sync_service.sync_post.call_count == 2

    def test_sync_all_posts_with_limit(self, blog_sync_service):
        """Test full sync with limit"""
        blog_sync_service._fetch_all_posts_from_beehiiv = Mock(return_value=[])

        blog_sync_service.sync_all_posts(limit=10)

        blog_sync_service._fetch_all_posts_from_beehiiv.assert_called_once_with(limit=10)

    def test_sync_all_posts_partial_failure(self, blog_sync_service, sample_beehiiv_post):
        """Test full sync with some posts failing"""
        posts = [
            sample_beehiiv_post,
            {**sample_beehiiv_post, 'id': 'post_67890'}
        ]

        blog_sync_service._fetch_all_posts_from_beehiiv = Mock(return_value=posts)

        # First succeeds, second fails
        blog_sync_service.sync_post = Mock(
            side_effect=[Mock(id=uuid4()), Exception('Sync failed')]
        )

        articles = blog_sync_service.sync_all_posts()

        # Should return only successful sync
        assert len(articles) == 1


# ============================================================================
# BEEHIIV API TESTS
# ============================================================================

class TestBeeHiivAPI:
    """Test BeeHiiv API interactions"""

    def test_fetch_post_from_beehiiv_success(self, blog_sync_service):
        """Test successful post fetch from BeeHiiv"""
        post_data = {'id': 'post_123', 'title': 'Test Post'}

        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {'data': post_data}
            mock_get.return_value.raise_for_status = Mock()

            result = blog_sync_service.fetch_post_from_beehiiv('post_123')

            assert result == post_data

    def test_fetch_post_from_beehiiv_api_error(self, blog_sync_service):
        """Test API error handling"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.raise_for_status.side_effect = Exception('API error')

            with pytest.raises(BeeHiivAPIError):
                blog_sync_service.fetch_post_from_beehiiv('post_123')

    def test_fetch_all_posts_pagination(self, blog_sync_service):
        """Test pagination in fetch all posts"""
        page1_data = {
            'data': [{'id': '1'}, {'id': '2'}],
            'has_more': True
        }
        page2_data = {
            'data': [{'id': '3'}],
            'has_more': False
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.json.side_effect = [page1_data, page2_data]
            mock_get.return_value.raise_for_status = Mock()

            posts = blog_sync_service._fetch_all_posts_from_beehiiv()

            assert len(posts) == 3
            assert mock_get.call_count == 2


# ============================================================================
# IMAGE HANDLING TESTS
# ============================================================================

class TestImageHandling:
    """Test image download and storage"""

    def test_download_and_store_image_success(self, blog_sync_service):
        """Test successful image download"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'fake_image_data'
            mock_get.return_value.headers = {'content-type': 'image/jpeg'}
            mock_get.return_value.raise_for_status = Mock()

            blog_sync_service.zerodb.upload_object = Mock(
                return_value='https://stored.com/image.jpg'
            )

            url = blog_sync_service._download_and_store_image(
                'https://example.com/image.jpg',
                'blog/test'
            )

            assert url == 'https://stored.com/image.jpg'

    def test_download_image_failure(self, blog_sync_service):
        """Test image download failure"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Network error')

            with pytest.raises(ImageDownloadError):
                blog_sync_service._download_and_store_image(
                    'https://example.com/image.jpg',
                    'blog/test'
                )

    def test_generate_thumbnail_success(self, blog_sync_service):
        """Test thumbnail generation"""
        from PIL import Image
        from io import BytesIO

        # Create fake image
        img = Image.new('RGB', (800, 600), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        with patch('requests.get') as mock_get:
            mock_get.return_value.content = img_bytes.getvalue()
            mock_get.return_value.raise_for_status = Mock()

            blog_sync_service.zerodb.upload_object = Mock(
                return_value='https://stored.com/thumb.jpg'
            )

            url = blog_sync_service._generate_thumbnail(
                'https://example.com/image.jpg',
                'blog/thumb'
            )

            assert url == 'https://stored.com/thumb.jpg'

    def test_generate_thumbnail_fallback(self, blog_sync_service):
        """Test thumbnail generation fallback on error"""
        with patch('requests.get', side_effect=Exception('Error')):
            url = blog_sync_service._generate_thumbnail(
                'https://example.com/image.jpg',
                'blog/thumb'
            )

            # Should return original URL as fallback
            assert url == 'https://example.com/image.jpg'


# ============================================================================
# SERVICE SINGLETON TEST
# ============================================================================

def test_get_blog_sync_service_singleton():
    """Test service singleton pattern"""
    from backend.services.blog_sync_service import get_blog_sync_service

    with patch('backend.services.blog_sync_service.get_zerodb_client'):
        service1 = get_blog_sync_service()
        service2 = get_blog_sync_service()

        assert service1 is service2
