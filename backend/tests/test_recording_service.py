"""
Tests for Recording Service (US-046)

Tests recording lifecycle including:
- Recording initiation and start
- Recording finalization and stop
- VOD attachment from webhooks
- Signed URL generation
- Error handling and retries
- Chat export functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from backend.services.recording_service import (
    RecordingService,
    RecordingServiceError,
    RecordingStartError,
    RecordingStopError
)
from backend.models.schemas import RecordingStatus


class TestRecordingService:
    """Test suite for RecordingService"""

    @pytest.fixture
    def recording_service(self):
        """Create RecordingService instance with mocked dependencies"""
        with patch('backend.services.recording_service.get_cloudflare_calls_service') as mock_calls, \
             patch('backend.services.recording_service.get_cloudflare_stream_service') as mock_stream, \
             patch('backend.services.recording_service.get_zerodb_service') as mock_db:
            
            service = RecordingService()
            service.calls_service = Mock()
            service.stream_service = Mock()
            service.db_service = Mock()
            
            return service

    @pytest.fixture
    def mock_session_data(self):
        """Mock training session data"""
        return {
            "id": str(uuid4()),
            "title": "Test Training Session",
            "cloudflare_room_id": "room_123",
            "recording_enabled": True,
            "recording_id": None,
            "recording_status": RecordingStatus.NOT_RECORDED.value
        }

    def test_initiate_recording_success(self, recording_service, mock_session_data):
        """Test successful recording initiation"""
        session_id = mock_session_data["id"]
        
        # Mock database response
        recording_service.db_service.get_document.return_value = mock_session_data
        
        # Mock successful recording start
        recording_service.calls_service.start_recording.return_value = {
            "recording_id": "rec_456",
            "room_id": "room_123",
            "status": "recording",
            "started_at": datetime.utcnow().isoformat()
        }
        
        recording_service.db_service.update_document.return_value = {"success": True}
        
        # Execute
        result = recording_service.initiate_recording(session_id)
        
        # Assert
        assert result["recording_id"] == "rec_456"
        assert result["status"] == RecordingStatus.RECORDING.value
        assert "started_at" in result
        
        # Verify database was updated
        recording_service.db_service.update_document.assert_called_once()
        update_call_args = recording_service.db_service.update_document.call_args
        assert update_call_args[0][0] == "training_sessions"
        assert update_call_args[0][1] == session_id
        assert update_call_args[0][2]["recording_status"] == RecordingStatus.RECORDING.value

    def test_initiate_recording_disabled(self, recording_service, mock_session_data):
        """Test recording initiation when recording is disabled"""
        session_id = mock_session_data["id"]
        mock_session_data["recording_enabled"] = False
        
        recording_service.db_service.get_document.return_value = mock_session_data
        
        result = recording_service.initiate_recording(session_id)
        
        assert result["recording_enabled"] is False
        assert "message" in result
        recording_service.calls_service.start_recording.assert_not_called()

    def test_initiate_recording_retry_on_failure(self, recording_service, mock_session_data):
        """Test automatic retry on recording start failure"""
        session_id = mock_session_data["id"]
        
        recording_service.db_service.get_document.return_value = mock_session_data
        
        # First two calls fail, third succeeds
        recording_service.calls_service.start_recording.side_effect = [
            Exception("Network error"),
            Exception("Temporary failure"),
            {
                "recording_id": "rec_456",
                "room_id": "room_123",
                "status": "recording",
                "started_at": datetime.utcnow().isoformat()
            }
        ]
        
        recording_service.db_service.update_document.return_value = {"success": True}
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = recording_service.initiate_recording(session_id)
        
        assert result["recording_id"] == "rec_456"
        assert recording_service.calls_service.start_recording.call_count == 3

    def test_initiate_recording_max_retries_exceeded(self, recording_service, mock_session_data):
        """Test failure after maximum retries"""
        session_id = mock_session_data["id"]
        
        recording_service.db_service.get_document.return_value = mock_session_data
        recording_service.calls_service.start_recording.side_effect = Exception("Persistent failure")
        recording_service.db_service.update_document.return_value = {"success": True}
        
        with patch('time.sleep'):
            with pytest.raises(RecordingStartError) as exc_info:
                recording_service.initiate_recording(session_id)
        
        assert "Failed to start recording after 3 attempts" in str(exc_info.value)
        assert recording_service.calls_service.start_recording.call_count == 3
        
        # Verify failure was recorded in database
        update_calls = recording_service.db_service.update_document.call_args_list
        failure_call = update_calls[-1]
        assert failure_call[0][2]["recording_status"] == RecordingStatus.FAILED.value

    def test_finalize_recording_success(self, recording_service, mock_session_data):
        """Test successful recording finalization"""
        session_id = mock_session_data["id"]
        mock_session_data["recording_id"] = "rec_456"
        
        recording_service.db_service.get_document.return_value = mock_session_data
        recording_service.calls_service.stop_recording.return_value = {
            "recording_id": "rec_456",
            "room_id": "room_123",
            "status": "processing",
            "ended_at": datetime.utcnow().isoformat(),
            "duration_seconds": 3600
        }
        recording_service.db_service.update_document.return_value = {"success": True}
        
        result = recording_service.finalize_recording(session_id)
        
        assert result["recording_id"] == "rec_456"
        assert result["status"] == RecordingStatus.PROCESSING.value
        assert result["duration_seconds"] == 3600

    def test_finalize_recording_no_active_recording(self, recording_service, mock_session_data):
        """Test finalization when no active recording exists"""
        session_id = mock_session_data["id"]
        mock_session_data["recording_id"] = None
        
        recording_service.db_service.get_document.return_value = mock_session_data
        
        with pytest.raises(RecordingStopError) as exc_info:
            recording_service.finalize_recording(session_id)
        
        assert "No active recording found" in str(exc_info.value)

    def test_attach_recording_success(self, recording_service):
        """Test successful recording attachment from webhook"""
        session_id = uuid4()
        stream_id = "stream_789"
        stream_url = "https://customer-xxx.cloudflarestream.com/stream_789/manifest/video.m3u8"
        
        recording_service.db_service.update_document.return_value = {"success": True}
        
        result = recording_service.attach_recording(
            session_id=session_id,
            stream_id=stream_id,
            stream_url=stream_url,
            duration_seconds=3600,
            file_size_bytes=524288000
        )
        
        assert result["session_id"] == str(session_id)
        assert result["stream_id"] == stream_id
        assert result["stream_url"] == stream_url
        assert result["status"] == RecordingStatus.READY.value
        
        # Verify database update
        update_call = recording_service.db_service.update_document.call_args
        update_data = update_call[0][2]
        assert update_data["cloudflare_stream_id"] == stream_id
        assert update_data["vod_stream_url"] == stream_url
        assert update_data["recording_status"] == RecordingStatus.READY.value

    def test_get_recording_status(self, recording_service, mock_session_data):
        """Test getting recording status"""
        session_id = mock_session_data["id"]
        mock_session_data["recording_status"] = RecordingStatus.READY.value
        mock_session_data["cloudflare_stream_id"] = "stream_789"
        
        recording_service.db_service.get_document.return_value = mock_session_data
        
        result = recording_service.get_recording_status(session_id)
        
        assert result["session_id"] == session_id
        assert result["recording_status"] == RecordingStatus.READY.value
        assert result["stream_id"] == "stream_789"

    def test_generate_vod_signed_url_success(self, recording_service, mock_session_data):
        """Test signed URL generation"""
        session_id = mock_session_data["id"]
        user_id = uuid4()
        mock_session_data["recording_status"] = RecordingStatus.READY.value
        mock_session_data["cloudflare_stream_id"] = "stream_789"
        
        recording_service.db_service.get_document.return_value = mock_session_data
        recording_service.stream_service.generate_signed_url.return_value = \
            "https://customer-xxx.cloudflarestream.com/stream_789/manifest/video.m3u8?exp=...&sig=..."
        
        result = recording_service.generate_vod_signed_url(session_id, user_id)
        
        assert "cloudflarestream.com" in result
        recording_service.stream_service.generate_signed_url.assert_called_once_with(
            "stream_789",
            expiry_hours=24
        )

    def test_generate_vod_signed_url_not_ready(self, recording_service, mock_session_data):
        """Test signed URL generation when recording not ready"""
        session_id = mock_session_data["id"]
        user_id = uuid4()
        mock_session_data["recording_status"] = RecordingStatus.PROCESSING.value
        mock_session_data["cloudflare_stream_id"] = "stream_789"
        
        recording_service.db_service.get_document.return_value = mock_session_data
        
        with pytest.raises(RecordingServiceError) as exc_info:
            recording_service.generate_vod_signed_url(session_id, user_id)
        
        assert "Recording not ready" in str(exc_info.value)

    def test_delete_recording_success(self, recording_service, mock_session_data):
        """Test successful recording deletion"""
        session_id = mock_session_data["id"]
        mock_session_data["cloudflare_stream_id"] = "stream_789"
        
        recording_service.db_service.get_document.return_value = mock_session_data
        recording_service.stream_service.delete_video.return_value = True
        recording_service.db_service.update_document.return_value = {"success": True}
        
        result = recording_service.delete_recording(session_id)
        
        assert result is True
        recording_service.stream_service.delete_video.assert_called_once_with("stream_789")

    def test_export_chat_to_storage(self, recording_service):
        """Test chat export functionality"""
        session_id = uuid4()
        chat_messages = [
            {"user": "Alice", "message": "Hello", "timestamp": "2025-11-10T10:00:00Z"},
            {"user": "Bob", "message": "Hi there", "timestamp": "2025-11-10T10:01:00Z"}
        ]
        
        recording_service.db_service.update_document.return_value = {"success": True}
        
        result = recording_service.export_chat_to_storage(session_id, chat_messages)
        
        assert "chat-transcripts" in result
        assert str(session_id) in result
        
        # Verify message count was updated
        update_call = recording_service.db_service.update_document.call_args
        assert update_call[0][2]["chat_message_count"] == 2


# Run tests with coverage
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.services.recording_service", "--cov-report=term-missing"])
