"""
Tests for BeeHiiv Webhook Handler

Tests webhook signature verification, event processing,
and error handling.

Events Tested:
- post.published
- post.updated
- post.deleted
"""

import pytest
from unittest.mock import Mock, patch
import json
import hmac
import hashlib
from uuid import uuid4


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def webhook_payload():
    """Sample webhook payload"""
    return {
        'event': 'post.published',
        'data': {
            'id': 'post_12345',
            'title': 'Test Post',
            'content_html': '<p>Content</p>',
            'author': {'name': 'Test Author'},
            'status': 'published'
        }
    }


@pytest.fixture
def generate_signature():
    """Function to generate valid webhook signature"""
    def _generate(payload: dict, secret: str = 'test_secret'):
        payload_str = json.dumps(payload)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    return _generate


# ============================================================================
# WEBHOOK SIGNATURE TESTS
# ============================================================================

class TestWebhookSignature:
    """Test webhook signature verification"""

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_webhook_with_valid_signature(self, mock_service, client, webhook_payload, generate_signature):
        """Test webhook with valid signature"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_sync.sync_post.return_value = Mock(id=uuid4())
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)
        signature = generate_signature(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str,
            headers={'X-BeeHiiv-Signature': signature}
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_webhook_with_invalid_signature(self, mock_service, client, webhook_payload):
        """Test webhook with invalid signature"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = False
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str,
            headers={'X-BeeHiiv-Signature': 'invalid_signature'}
        )

        assert response.status_code == 401

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_webhook_without_signature(self, mock_service, client, webhook_payload):
        """Test webhook without signature header"""
        mock_sync = Mock()
        mock_sync.sync_post.return_value = Mock(id=uuid4())
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        # Should still process (with warning logged)
        assert response.status_code == 200


# ============================================================================
# POST PUBLISHED EVENT TESTS
# ============================================================================

class TestPostPublishedEvent:
    """Test post.published event handling"""

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_post_published_success(self, mock_service, client, webhook_payload):
        """Test successful post.published event"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        article = Mock(id=uuid4())
        mock_sync.sync_post.return_value = article
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['event_type'] == 'post.published'
        assert 'article_id' in data

        # Verify sync_post was called
        mock_sync.sync_post.assert_called_once()


# ============================================================================
# POST UPDATED EVENT TESTS
# ============================================================================

class TestPostUpdatedEvent:
    """Test post.updated event handling"""

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_post_updated_success(self, mock_service, client, webhook_payload):
        """Test successful post.updated event"""
        webhook_payload['event'] = 'post.updated'

        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        article = Mock(id=uuid4())
        mock_sync.sync_post.return_value = article
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['event_type'] == 'post.updated'

        mock_sync.sync_post.assert_called_once()


# ============================================================================
# POST DELETED EVENT TESTS
# ============================================================================

class TestPostDeletedEvent:
    """Test post.deleted event handling"""

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_post_deleted_success(self, mock_service, client, webhook_payload):
        """Test successful post.deleted event"""
        webhook_payload['event'] = 'post.deleted'

        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        existing_article = Mock(id=uuid4())
        mock_sync._get_article_by_beehiiv_id.return_value = existing_article
        mock_sync.delete_post.return_value = True
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['event_type'] == 'post.deleted'

        mock_sync.delete_post.assert_called_once()

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_post_deleted_not_found(self, mock_service, client, webhook_payload):
        """Test post.deleted when post doesn't exist"""
        webhook_payload['event'] = 'post.deleted'

        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_sync._get_article_by_beehiiv_id.return_value = None
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'not_found'


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestWebhookErrorHandling:
    """Test webhook error handling"""

    def test_invalid_json_payload(self, client):
        """Test webhook with invalid JSON"""
        response = client.post(
            '/api/webhooks/beehiiv/post',
            content='invalid json'
        )

        assert response.status_code == 400

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_missing_event_type(self, mock_service, client):
        """Test webhook without event type"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_service.return_value = mock_sync

        payload = {'data': {'id': 'post_123'}}
        payload_str = json.dumps(payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 400

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_missing_post_id(self, mock_service, client):
        """Test webhook without post ID"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_service.return_value = mock_sync

        payload = {'event': 'post.published', 'data': {}}
        payload_str = json.dumps(payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 400

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_unsupported_event_type(self, mock_service, client, webhook_payload):
        """Test webhook with unsupported event type"""
        webhook_payload['event'] = 'post.draft'

        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ignored'

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_sync_error_handling(self, mock_service, client, webhook_payload):
        """Test handling of sync errors"""
        from backend.services.blog_sync_service import BlogSyncError

        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_sync.sync_post.side_effect = BlogSyncError('Sync failed')
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        # Should return 200 with error status to prevent retries
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'

    @patch('backend.routes.webhooks.beehiiv.get_blog_sync_service')
    def test_unexpected_error(self, mock_service, client, webhook_payload):
        """Test handling of unexpected errors"""
        mock_sync = Mock()
        mock_sync.verify_webhook_signature.return_value = True
        mock_sync.sync_post.side_effect = Exception('Unexpected error')
        mock_service.return_value = mock_sync

        payload_str = json.dumps(webhook_payload)

        response = client.post(
            '/api/webhooks/beehiiv/post',
            content=payload_str
        )

        assert response.status_code == 500


# ============================================================================
# HEALTH CHECK TEST
# ============================================================================

class TestWebhookHealthCheck:
    """Test webhook health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        with patch('backend.routes.webhooks.beehiiv.settings') as mock_settings:
            mock_settings.BEEHIIV_WEBHOOK_SECRET = 'secret'
            mock_settings.BEEHIIV_API_KEY = 'api_key'
            mock_settings.BEEHIIV_PUBLICATION_ID = 'pub_id'

            response = client.get('/api/webhooks/beehiiv/health')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['webhook_secret_configured'] is True
            assert data['api_key_configured'] is True
            assert data['publication_id_configured'] is True
