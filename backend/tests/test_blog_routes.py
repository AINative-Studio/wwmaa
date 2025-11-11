"""
Tests for Blog API Routes

Tests all blog API endpoints for proper functionality,
error handling, and security.

Endpoints Tested:
- GET /api/blog/posts
- GET /api/blog/posts/{slug}
- GET /api/blog/categories
- GET /api/blog/tags
- GET /api/blog/posts/related/{post_id}
- GET /api/blog/posts/by-category/{category}
- GET /api/blog/posts/by-tag/{tag}
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from backend.models.schemas import ArticleStatus


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_articles():
    """Sample article data"""
    return [
        {
            'id': str(uuid4()),
            'beehiiv_post_id': 'post_1',
            'title': 'Getting Started with Karate',
            'slug': 'getting-started-with-karate',
            'excerpt': 'Learn the basics of karate',
            'content': '<p>Karate content</p>',
            'author': {'name': 'John Doe'},
            'category': 'Beginners',
            'tags': ['karate', 'beginners'],
            'status': ArticleStatus.PUBLISHED,
            'published_at': datetime.utcnow().isoformat(),
            'view_count': 100,
            'read_time_minutes': 5,
            'seo_metadata': {}
        },
        {
            'id': str(uuid4()),
            'beehiiv_post_id': 'post_2',
            'title': 'Advanced Techniques',
            'slug': 'advanced-techniques',
            'excerpt': 'Master advanced martial arts',
            'content': '<p>Advanced content</p>',
            'author': {'name': 'Jane Smith'},
            'category': 'Advanced',
            'tags': ['advanced', 'techniques'],
            'status': ArticleStatus.PUBLISHED,
            'published_at': datetime.utcnow().isoformat(),
            'view_count': 50,
            'read_time_minutes': 10,
            'seo_metadata': {}
        }
    ]


# ============================================================================
# LIST POSTS TESTS
# ============================================================================

class TestListBlogPosts:
    """Test GET /api/blog/posts endpoint"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_success(self, mock_zerodb, client, sample_articles):
        """Test successful post listing"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_service.count_documents.return_value = 2
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'pagination' in data
        assert len(data['data']) == 2
        assert data['pagination']['total'] == 2

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_pagination(self, mock_zerodb, client, sample_articles):
        """Test post listing with pagination"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_service.count_documents.return_value = 50
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts?page=2&limit=10')

        assert response.status_code == 200
        data = response.json()
        assert data['pagination']['page'] == 2
        assert data['pagination']['limit'] == 10
        assert data['pagination']['total'] == 50
        assert data['pagination']['has_prev'] is True

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_filter_by_category(self, mock_zerodb, client, sample_articles):
        """Test filtering by category"""
        mock_service = Mock()
        mock_service.query_documents.return_value = [sample_articles[0]]
        mock_service.count_documents.return_value = 1
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts?category=Beginners')

        assert response.status_code == 200
        mock_service.query_documents.assert_called_once()

        # Check filter was applied
        call_args = mock_service.query_documents.call_args
        assert call_args[1]['filters']['category'] == 'Beginners'

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_filter_by_tag(self, mock_zerodb, client, sample_articles):
        """Test filtering by tag"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_service.count_documents.return_value = 2
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts?tag=karate')

        assert response.status_code == 200

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_search(self, mock_zerodb, client, sample_articles):
        """Test search functionality"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_service.count_documents.return_value = 2
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts?search=karate')

        assert response.status_code == 200
        data = response.json()

        # Should filter results to match search term
        assert all('karate' in post['title'].lower() or 'karate' in post.get('excerpt', '').lower()
                   for post in data['data'])

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_posts_error_handling(self, mock_zerodb, client):
        """Test error handling"""
        mock_service = Mock()
        mock_service.query_documents.side_effect = Exception('Database error')
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts')

        assert response.status_code == 500


# ============================================================================
# GET SINGLE POST TESTS
# ============================================================================

class TestGetBlogPostBySlug:
    """Test GET /api/blog/posts/{slug} endpoint"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_post_success(self, mock_zerodb, client, sample_articles):
        """Test successful post retrieval"""
        mock_service = Mock()
        mock_service.query_documents.return_value = [sample_articles[0]]
        mock_service.update_document.return_value = None
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts/getting-started-with-karate')

        assert response.status_code == 200
        data = response.json()
        assert data['slug'] == 'getting-started-with-karate'
        assert data['view_count'] == 101  # Incremented

        # Verify view count was incremented
        mock_service.update_document.assert_called_once()

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_post_not_found(self, mock_zerodb, client):
        """Test post not found"""
        mock_service = Mock()
        mock_service.query_documents.return_value = []
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts/nonexistent-slug')

        assert response.status_code == 404

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_draft_post_as_public(self, mock_zerodb, client, sample_articles):
        """Test draft post not visible to public"""
        draft_post = sample_articles[0].copy()
        draft_post['status'] = ArticleStatus.DRAFT

        mock_service = Mock()
        mock_service.query_documents.return_value = [draft_post]
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts/getting-started-with-karate')

        # Should return 404 for draft posts
        assert response.status_code == 404


# ============================================================================
# CATEGORIES TESTS
# ============================================================================

class TestListCategories:
    """Test GET /api/blog/categories endpoint"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_categories_success(self, mock_zerodb, client, sample_articles):
        """Test successful category listing"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/categories')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert len(data['data']) == 2  # Beginners and Advanced

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_categories_with_counts(self, mock_zerodb, client, sample_articles):
        """Test category counts"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/categories')

        assert response.status_code == 200
        data = response.json()

        # Each category should have count
        for category in data['data']:
            assert 'name' in category
            assert 'count' in category
            assert category['count'] > 0


# ============================================================================
# TAGS TESTS
# ============================================================================

class TestListTags:
    """Test GET /api/blog/tags endpoint"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_tags_success(self, mock_zerodb, client, sample_articles):
        """Test successful tag listing"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/tags')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert len(data['data']) >= 2  # At least karate and beginners

    @patch('backend.routes.blog.get_zerodb_service')
    def test_list_tags_sorted_by_count(self, mock_zerodb, client, sample_articles):
        """Test tags sorted by count (descending)"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/tags')

        assert response.status_code == 200
        data = response.json()

        # Verify sorted by count (descending)
        counts = [tag['count'] for tag in data['data']]
        assert counts == sorted(counts, reverse=True)


# ============================================================================
# RELATED POSTS TESTS
# ============================================================================

class TestGetRelatedPosts:
    """Test GET /api/blog/posts/related/{post_id} endpoint"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_related_posts_success(self, mock_zerodb, client, sample_articles):
        """Test successful related posts retrieval"""
        post_id = sample_articles[0]['id']

        mock_service = Mock()
        mock_service.get_document.return_value = sample_articles[0]
        mock_service.query_documents.return_value = [sample_articles[1]]
        mock_zerodb.return_value = mock_service

        response = client.get(f'/api/blog/posts/related/{post_id}')

        assert response.status_code == 200
        data = response.json()
        assert 'data' in data
        assert len(data['data']) >= 0

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_related_posts_not_found(self, mock_zerodb, client):
        """Test related posts for nonexistent post"""
        post_id = str(uuid4())

        mock_service = Mock()
        mock_service.get_document.side_effect = Exception('Not found')
        mock_zerodb.return_value = mock_service

        response = client.get(f'/api/blog/posts/related/{post_id}')

        assert response.status_code == 404

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_related_posts_limit(self, mock_zerodb, client, sample_articles):
        """Test related posts with limit"""
        post_id = sample_articles[0]['id']

        mock_service = Mock()
        mock_service.get_document.return_value = sample_articles[0]
        mock_service.query_documents.return_value = sample_articles
        mock_zerodb.return_value = mock_service

        response = client.get(f'/api/blog/posts/related/{post_id}?limit=1')

        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) <= 1


# ============================================================================
# CATEGORY/TAG FILTER ENDPOINTS TESTS
# ============================================================================

class TestCategoryTagFilters:
    """Test category and tag filter endpoints"""

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_posts_by_category(self, mock_zerodb, client, sample_articles):
        """Test GET /api/blog/posts/by-category/{category}"""
        mock_service = Mock()
        mock_service.query_documents.return_value = [sample_articles[0]]
        mock_service.count_documents.return_value = 1
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts/by-category/Beginners')

        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) >= 0

    @patch('backend.routes.blog.get_zerodb_service')
    def test_get_posts_by_tag(self, mock_zerodb, client, sample_articles):
        """Test GET /api/blog/posts/by-tag/{tag}"""
        mock_service = Mock()
        mock_service.query_documents.return_value = sample_articles
        mock_service.count_documents.return_value = 2
        mock_zerodb.return_value = mock_service

        response = client.get('/api/blog/posts/by-tag/karate')

        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) >= 0
