"""
Cloudflare Calls Pydantic Models

This module defines Pydantic models for Cloudflare Calls WebRTC rooms and recordings.
These models provide data validation and serialization for Cloudflare Calls integration.

Models:
- CloudflareRoom: WebRTC room metadata
- CloudflareRecording: Video recording metadata
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4


class RoomStatus(str, Enum):
    """Cloudflare Calls room status"""
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class RecordingStatus(str, Enum):
    """Cloudflare Calls recording status"""
    NOT_RECORDED = "not_recorded"
    RECORDING = "recording"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    STOPPED = "stopped"


class ParticipantRole(str, Enum):
    """Cloudflare Calls participant role"""
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    PRESENTER = "presenter"


class BaseDocument(BaseModel):
    """Base model with common fields for all documents"""
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=uuid4, description="Unique document identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Document creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Document last update timestamp")


class CloudflareRoom(BaseDocument):
    """
    Cloudflare Calls WebRTC room

    Represents a WebRTC video conferencing room created via Cloudflare Calls API.
    Each room is associated with a training session and has a maximum participant limit.

    Attributes:
        room_id: Unique Cloudflare room identifier
        session_id: Associated training session ID
        status: Current room status (active/closed/expired)
        max_participants: Maximum allowed participants
        current_participants: Current participant count
        room_name: Optional human-readable name
        join_url: Base URL for joining
        recording_enabled: Whether recording is enabled
        recording_id: Active recording identifier
        recording_status: Current recording status
        started_at: Room start timestamp
        ended_at: Room end timestamp
        expires_at: Room expiration timestamp
        metadata: Additional custom metadata
    """
    room_id: str = Field(..., min_length=1, max_length=200, description="Cloudflare room ID")
    session_id: UUID = Field(..., description="Reference to training_sessions collection")

    # Room Configuration
    status: RoomStatus = Field(default=RoomStatus.ACTIVE, description="Room status")
    max_participants: int = Field(default=50, ge=1, le=1000, description="Maximum participants allowed")
    current_participants: int = Field(default=0, ge=0, description="Current number of participants")

    # Room Details
    room_name: Optional[str] = Field(None, max_length=200, description="Human-readable room name")
    join_url: Optional[str] = Field(None, description="Base URL for joining the room")

    # Recording
    recording_enabled: bool = Field(default=True, description="Recording enabled flag")
    recording_id: Optional[str] = Field(None, description="Active recording ID")
    recording_status: RecordingStatus = Field(
        default=RecordingStatus.NOT_RECORDED,
        description="Current recording status"
    )

    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Room session start time")
    ended_at: Optional[datetime] = Field(None, description="Room session end time")
    expires_at: Optional[datetime] = Field(None, description="Room expiration time")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional room metadata")

    @field_validator('max_participants')
    @classmethod
    def validate_max_participants(cls, v):
        """Validate max_participants is within acceptable range"""
        if v < 1 or v > 1000:
            raise ValueError("max_participants must be between 1 and 1000")
        return v


class CloudflareRecording(BaseDocument):
    """
    Cloudflare Calls video recording

    Represents a video recording of a WebRTC room session.
    Recordings are processed asynchronously by Cloudflare and become available via webhook.

    Attributes:
        recording_id: Unique Cloudflare recording identifier
        room_id: Associated room identifier
        session_id: Associated training session ID
        status: Current recording status
        stream_url: Cloudflare Stream video URL (when ready)
        cloudflare_stream_id: Cloudflare Stream identifier
        duration: Recording duration in seconds
        size_bytes: File size in bytes
        recording_mode: Recording mode (composition/individual)
        started_at: Recording start timestamp
        stopped_at: Recording stop timestamp
        processed_at: Processing completion timestamp
        ready_at: Video ready timestamp
        error_message: Error details if failed
        metadata: Additional custom metadata
    """
    recording_id: str = Field(..., min_length=1, max_length=200, description="Cloudflare recording ID")
    room_id: str = Field(..., min_length=1, max_length=200, description="Associated room ID")
    session_id: UUID = Field(..., description="Reference to training_sessions collection")

    # Recording Status
    status: RecordingStatus = Field(..., description="Recording status")

    # Video Details
    stream_url: Optional[str] = Field(None, description="Cloudflare Stream video URL (when ready)")
    cloudflare_stream_id: Optional[str] = Field(None, description="Cloudflare Stream ID")
    duration: Optional[int] = Field(None, ge=0, description="Recording duration in seconds")
    size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")

    # Recording Configuration
    recording_mode: str = Field(
        default="composition",
        max_length=50,
        description="Recording mode (composition/individual)"
    )

    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Recording start time")
    stopped_at: Optional[datetime] = Field(None, description="Recording stop time")
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")
    ready_at: Optional[datetime] = Field(None, description="Video ready time")

    # Error Handling
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional recording metadata")

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v):
        """Validate duration is non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError("duration must be non-negative")
        return v


class WebhookRecordingReadyEvent(BaseModel):
    """
    Cloudflare webhook payload for recording ready event

    Represents the webhook payload sent by Cloudflare when a recording
    is processed and ready for viewing.
    """
    model_config = ConfigDict(use_enum_values=True)

    event_type: str = Field(..., description="Event type (e.g., 'recording.ready')")
    room_id: str = Field(..., description="Room identifier")
    recording_id: str = Field(..., description="Recording identifier")
    stream_url: str = Field(..., description="Cloudflare Stream URL")
    stream_id: str = Field(..., description="Cloudflare Stream ID")
    duration: int = Field(..., ge=0, description="Duration in seconds")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    timestamp: datetime = Field(..., description="Event timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
