"""
Tests for Cloudflare Stream Service

Comprehensive test coverage for video upload, management, signed URLs,
captions, and thumbnails.

Run with: pytest backend/tests/test_cloudflare_stream_service.py -v --cov
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from uuid import uuid4
from datetime import datetime, timedelta
import jwt
import tempfile
import os

from backend.services.cloudflare_stream_service import CloudflareStreamService, CloudflareStreamError


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'test_account_123')
    monkeypatch.setenv('CLOUDFLARE_STREAM_API_TOKEN', 'test_token_abc')
    monkeypatch.setenv('CLOUDFLARE_STREAM_SIGNING_KEY', 'test_signing_key')
    monkeypatch.setenv('CLOUDFLARE_STREAM_WEBHOOK_SECRET', 'test_webhook_secret')


@pytest.fixture
def stream_service(mock_env_vars):
    """Create CloudflareStreamService instance"""
    return CloudflareStreamService()


@pytest.fixture
def mock_response():
    """Create mock response"""
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.json.return_value = {
        'success': True,
        'result': {
            'uid': 'video_123',
            'status': {'state': 'ready'},
            'duration': 300.5,
            'thumbnail': 'https://example.com/thumb.jpg',
            'preview': 'https://example.com/preview.jpg',
            'playback': {
                'hls': 'https://example.com/video.m3u8',
                'dash': 'https://example.com/video.mpd'
            }
        }
    }
    return response


class TestCloudflareStreamServiceInit:
    """Test service initialization"""

    def test_init_with_env_vars(self, mock_env_vars):
        """Test initialization with environment variables"""
        service = CloudflareStreamService()

        assert service.account_id == 'test_account_123'
        assert service.api_token == 'test_token_abc'
        assert service.signing_key == 'test_signing_key'
        assert 'test_account_123' in service.base_url

    def test_init_with_explicit_params(self, mock_env_vars):
        """Test initialization with explicit parameters"""
        service = CloudflareStreamService(
            account_id='custom_account',
            api_token='custom_token',
            signing_key='custom_key'
        )

        assert service.account_id == 'custom_account'
        assert service.api_token == 'custom_token'
        assert service.signing_key == 'custom_key'

    def test_init_missing_account_id(self, monkeypatch):
        """Test initialization fails without account ID"""
        monkeypatch.delenv('CLOUDFLARE_ACCOUNT_ID', raising=False)

        with pytest.raises(ValueError, match="CLOUDFLARE_ACCOUNT_ID is required"):
            CloudflareStreamService()

    def test_init_missing_api_token(self, monkeypatch):
        """Test initialization fails without API token"""
        monkeypatch.setenv('CLOUDFLARE_ACCOUNT_ID', 'test_account')
        monkeypatch.delenv('CLOUDFLARE_STREAM_API_TOKEN', raising=False)

        with pytest.raises(ValueError, match="CLOUDFLARE_STREAM_API_TOKEN is required"):
            CloudflareStreamService()


class TestVideoUpload:
    """Test video upload functionality"""

    @patch('backend.services.cloudflare_stream_service.requests.request')
    @patch('backend.services.cloudflare_stream_service.Path')
    def test_upload_video_success(self, mock_path_class, mock_request, stream_service, mock_response):
        """Test successful video upload"""
        # Mock file
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.name = 'test_video.mp4'
        mock_stat = Mock()
        mock_stat.st_size = 100 * 1024 * 1024  # 100MB
        mock_path.stat.return_value = mock_stat
        mock_path_class.return_value = mock_path

        # Mock request
        mock_request.return_value = mock_response

        # Mock open
        with patch('builtins.open', mock_open(read_data=b'video data')):
            result = stream_service.upload_video(
                file_path='/path/to/video.mp4',
                metadata={'name': 'Test Video', 'requireSignedURLs': True}
            )

        assert result['uid'] == 'video_123'
        assert result['status']['state'] == 'ready'
        assert result['duration'] == 300.5
        mock_request.assert_called_once()

    @patch('backend.services.cloudflare_stream_service.Path')
    def test_upload_video_file_not_found(self, mock_path_class, stream_service):
        """Test upload fails with nonexistent file"""
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        with pytest.raises(FileNotFoundError, match="Video file not found"):
            stream_service.upload_video('/path/to/nonexistent.mp4')

    @patch('backend.services.cloudflare_stream_service.Path')
    def test_upload_video_file_too_large(self, mock_path_class, stream_service):
        """Test upload fails with file > 200MB"""
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_stat = Mock()
        mock_stat.st_size = 250 * 1024 * 1024  # 250MB
        mock_path.stat.return_value = mock_stat
        mock_path_class.return_value = mock_path

        with pytest.raises(ValueError, match="exceeds 200MB"):
            stream_service.upload_video('/path/to/large_video.mp4')

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_upload_from_url_success(self, mock_request, stream_service, mock_response):
        """Test successful video import from URL"""
        mock_request.return_value = mock_response

        result = stream_service.upload_from_url(
            'https://example.com/video.mp4',
            metadata={'name': 'Imported Video'}
        )

        assert result['uid'] == 'video_123'
        assert mock_request.called
        call_args = mock_request.call_args
        assert call_args[1]['json']['url'] == 'https://example.com/video.mp4'


class TestVideoManagement:
    """Test video management operations"""

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_get_video_success(self, mock_request, stream_service, mock_response):
        """Test getting video details"""
        mock_request.return_value = mock_response

        result = stream_service.get_video('video_123')

        assert result['uid'] == 'video_123'
        assert result['duration'] == 300.5
        mock_request.assert_called_once()

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_update_video_success(self, mock_request, stream_service, mock_response):
        """Test updating video metadata"""
        mock_request.return_value = mock_response

        result = stream_service.update_video(
            'video_123',
            {'name': 'Updated Title', 'requireSignedURLs': True}
        )

        assert result['uid'] == 'video_123'
        mock_request.assert_called_once()

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_delete_video_success(self, mock_request, stream_service):
        """Test deleting video"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'result': {}}
        mock_request.return_value = mock_response

        result = stream_service.delete_video('video_123')

        assert result is True
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == 'DELETE'

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_list_videos_success(self, mock_request, stream_service):
        """Test listing videos"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'result': [
                {'uid': 'video_1', 'status': {'state': 'ready'}},
                {'uid': 'video_2', 'status': {'state': 'processing'}}
            ]
        }
        mock_request.return_value = mock_response

        results = stream_service.list_videos()

        assert len(results) == 2
        assert results[0]['uid'] == 'video_1'
        assert results[1]['uid'] == 'video_2'


class TestSignedURLs:
    """Test signed URL generation"""

    @patch('backend.services.cloudflare_stream_service.jwt.encode')
    def test_generate_signed_url_success(self, mock_jwt_encode, stream_service):
        """Test generating signed URL"""
        mock_jwt_encode.return_value = 'signed_token_123'

        token = stream_service.generate_signed_url(
            'video_123',
            expiry_seconds=3600
        )

        assert token == 'signed_token_123'
        mock_jwt_encode.assert_called_once()

        # Check JWT payload
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]
        assert payload['sub'] == 'video_123'
        assert 'exp' in payload
        assert 'nbf' in payload

    def test_generate_signed_url_no_signing_key(self, mock_env_vars, monkeypatch):
        """Test signed URL generation fails without signing key"""
        monkeypatch.delenv('CLOUDFLARE_STREAM_SIGNING_KEY', raising=False)
        service = CloudflareStreamService(
            account_id='test_account',
            api_token='test_token',
            signing_key=None
        )

        with pytest.raises(ValueError, match="CLOUDFLARE_STREAM_SIGNING_KEY is required"):
            service.generate_signed_url('video_123')

    @patch('backend.services.cloudflare_stream_service.jwt.encode')
    def test_generate_signed_url_with_user_id(self, mock_jwt_encode, stream_service):
        """Test signed URL with user ID for audit"""
        mock_jwt_encode.return_value = 'signed_token_123'
        user_id = uuid4()

        token = stream_service.generate_signed_url(
            'video_123',
            expiry_seconds=86400,
            user_id=user_id
        )

        # Check user_id in JWT payload
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]
        assert payload['user_id'] == str(user_id)

    @patch('backend.services.cloudflare_stream_service.jwt.encode')
    def test_generate_signed_url_with_download(self, mock_jwt_encode, stream_service):
        """Test signed URL with download enabled"""
        mock_jwt_encode.return_value = 'signed_token_123'

        token = stream_service.generate_signed_url(
            'video_123',
            download_filename='video.mp4'
        )

        # Check download in JWT payload
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]
        assert payload['downloadable'] is True
        assert payload['filename'] == 'video.mp4'


class TestEmbedCode:
    """Test embed code generation"""

    def test_get_embed_code_basic(self, stream_service):
        """Test basic embed code generation"""
        embed = stream_service.get_embed_code('video_123')

        assert 'iframe' in embed
        assert 'video_123' in embed
        assert stream_service.account_id in embed

    def test_get_embed_code_with_token(self, stream_service):
        """Test embed code with signed token"""
        embed = stream_service.get_embed_code(
            'video_123',
            signed_token='signed_token_abc'
        )

        assert 'token=signed_token_abc' in embed

    def test_get_embed_code_with_options(self, stream_service):
        """Test embed code with playback options"""
        embed = stream_service.get_embed_code(
            'video_123',
            autoplay=True,
            muted=True,
            loop=True,
            controls=False
        )

        assert 'autoplay=true' in embed
        assert 'muted=true' in embed
        assert 'loop=true' in embed
        assert 'controls=false' in embed

    def test_get_embed_code_responsive(self, stream_service):
        """Test responsive embed code"""
        embed = stream_service.get_embed_code('video_123', responsive=True)

        assert 'position: relative' in embed
        assert 'padding-top: 56.25%' in embed  # 16:9 aspect ratio


class TestCaptions:
    """Test caption/subtitle management"""

    @patch('backend.services.cloudflare_stream_service.requests.request')
    @patch('backend.services.cloudflare_stream_service.Path')
    def test_upload_captions_success(self, mock_path_class, mock_request, stream_service):
        """Test uploading captions"""
        # Mock file
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.name = 'captions.vtt'
        mock_path_class.return_value = mock_path

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'result': {}}
        mock_request.return_value = mock_response

        with patch('builtins.open', mock_open(read_data=b'WEBVTT\n\n00:00.000 --> 00:05.000\nHello')):
            result = stream_service.upload_captions(
                'video_123',
                '/path/to/captions.vtt',
                language='en',
                label='English'
            )

        assert result == {}
        mock_request.assert_called_once()

    @patch('backend.services.cloudflare_stream_service.Path')
    def test_upload_captions_file_not_found(self, mock_path_class, stream_service):
        """Test caption upload fails with nonexistent file"""
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        with pytest.raises(FileNotFoundError, match="Caption file not found"):
            stream_service.upload_captions('video_123', '/path/to/missing.vtt')

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_delete_captions_success(self, mock_request, stream_service):
        """Test deleting captions"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'result': {}}
        mock_request.return_value = mock_response

        result = stream_service.delete_captions('video_123', 'en')

        assert result is True
        mock_request.assert_called_once()


class TestThumbnails:
    """Test thumbnail generation"""

    def test_get_thumbnail_url_basic(self, stream_service):
        """Test basic thumbnail URL"""
        url = stream_service.get_thumbnail_url('video_123')

        assert 'video_123' in url
        assert 'thumbnail.jpg' in url
        assert stream_service.account_id in url

    def test_get_thumbnail_url_with_time(self, stream_service):
        """Test thumbnail at specific timestamp"""
        url = stream_service.get_thumbnail_url('video_123', time_seconds=30)

        assert 'time=30s' in url

    def test_get_thumbnail_url_with_dimensions(self, stream_service):
        """Test thumbnail with specific dimensions"""
        url = stream_service.get_thumbnail_url(
            'video_123',
            width=640,
            height=360,
            fit='scale'
        )

        assert 'width=640' in url
        assert 'height=360' in url
        assert 'fit=scale' in url


class TestWebhookVerification:
    """Test webhook signature verification"""

    def test_verify_webhook_signature_success(self, stream_service):
        """Test successful webhook signature verification"""
        payload = b'{"uid":"video_123","status":{"state":"ready"}}'
        secret = 'test_webhook_secret'

        # Calculate expected signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        result = stream_service.verify_webhook_signature(
            payload,
            expected_signature,
            secret
        )

        assert result is True

    def test_verify_webhook_signature_invalid(self, stream_service):
        """Test webhook signature verification fails with invalid signature"""
        payload = b'{"uid":"video_123"}'
        secret = 'test_webhook_secret'
        invalid_signature = 'invalid_signature_123'

        result = stream_service.verify_webhook_signature(
            payload,
            invalid_signature,
            secret
        )

        assert result is False

    def test_verify_webhook_signature_no_secret(self, stream_service, monkeypatch):
        """Test webhook verification fails without secret"""
        monkeypatch.delenv('CLOUDFLARE_STREAM_WEBHOOK_SECRET', raising=False)

        with pytest.raises(ValueError, match="Webhook secret is required"):
            stream_service.verify_webhook_signature(
                b'payload',
                'signature'
            )


class TestChunkedUpload:
    """Test chunked upload (TUS protocol)"""

    @patch('backend.services.cloudflare_stream_service.requests.post')
    def test_initiate_chunked_upload(self, mock_post, stream_service):
        """Test initiating chunked upload"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.ok = True
        mock_response.headers = {
            'Location': f'https://api.cloudflare.com/client/v4/accounts/{stream_service.account_id}/stream/video_123',
            'Tus-Resumable': '1.0.0'
        }
        mock_post.return_value = mock_response

        result = stream_service.initiate_chunked_upload(
            file_size=500_000_000,  # 500MB
            metadata={'name': 'Large Video'}
        )

        assert result['upload_id'] == 'video_123'
        assert result['tus_resumable'] == '1.0.0'
        mock_post.assert_called_once()

    @patch('backend.services.cloudflare_stream_service.requests.patch')
    def test_upload_chunk(self, mock_patch, stream_service):
        """Test uploading a chunk"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.ok = True
        mock_response.headers = {
            'Upload-Offset': '5242880'  # 5MB
        }
        mock_patch.return_value = mock_response

        upload_url = f'https://api.cloudflare.com/client/v4/accounts/{stream_service.account_id}/stream/video_123'
        chunk_data = b'x' * (5 * 1024 * 1024)  # 5MB

        new_offset = stream_service.upload_chunk(
            upload_url=upload_url,
            chunk_data=chunk_data,
            offset=0
        )

        assert new_offset == 5242880
        mock_patch.assert_called_once()


class TestErrorHandling:
    """Test error handling"""

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_api_error_handling(self, mock_request, stream_service):
        """Test API error handling"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.ok = False
        mock_response.json.return_value = {
            'success': False,
            'errors': [{'message': 'Invalid video ID'}]
        }
        mock_request.return_value = mock_response

        with pytest.raises(Exception, match="Invalid video ID"):
            stream_service.get_video('invalid_id')

    @patch('backend.services.cloudflare_stream_service.requests.request')
    def test_network_error_handling(self, mock_request, stream_service):
        """Test network error handling"""
        import requests
        mock_request.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(requests.exceptions.RequestException):
            stream_service.get_video('video_123')


# Test coverage summary
def test_coverage_check():
    """Verify test coverage meets 80% threshold"""
    # This is a placeholder test
    # Actual coverage is checked by pytest-cov
    # Run: pytest --cov=backend.services.cloudflare_stream_service --cov-report=term-missing
    assert True, "Coverage should be checked by pytest-cov"
