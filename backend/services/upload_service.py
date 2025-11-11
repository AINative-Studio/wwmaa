"""
Upload Service - Chunked File Upload Handler

This service manages large file uploads with progress tracking and resumable uploads.
Uses Redis for tracking upload state and progress.
"""

import os
import hashlib
import time
from typing import Optional, Dict, Any
from pathlib import Path
from uuid import uuid4
import redis
import json


class UploadService:
    """
    Service for managing chunked file uploads

    Features:
    - Chunked uploads for large files (up to 30GB)
    - Progress tracking in Redis
    - Resumable uploads
    - Temporary file management
    """

    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
    MAX_FILE_SIZE = 30 * 1024 * 1024 * 1024  # 30GB
    UPLOAD_TTL = 86400  # 24 hours

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        temp_dir: Optional[str] = None
    ):
        """
        Initialize upload service

        Args:
            redis_client: Redis client for progress tracking
            temp_dir: Temporary directory for uploads
        """
        self.redis_client = redis_client or redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )

        self.temp_dir = Path(temp_dir or os.getenv('UPLOAD_TEMP_DIR', '/tmp/uploads'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def initiate_upload(
        self,
        file_name: str,
        file_size: int,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a chunked upload session

        Args:
            file_name: Original filename
            file_size: Total file size in bytes
            user_id: User ID initiating upload
            metadata: Optional metadata

        Returns:
            Upload session details

        Raises:
            ValueError: If file size exceeds maximum

        Example:
            session = service.initiate_upload(
                "training_video.mp4",
                500_000_000,  # 500MB
                user_id="user-123",
                metadata={"title": "Training Session 1"}
            )
            upload_id = session['upload_id']
        """
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_size / (1024**3):.2f}GB exceeds maximum "
                f"{self.MAX_FILE_SIZE / (1024**3):.2f}GB"
            )

        # Generate upload ID
        upload_id = str(uuid4())

        # Create upload session in Redis
        session_data = {
            'upload_id': upload_id,
            'file_name': file_name,
            'file_size': file_size,
            'user_id': user_id,
            'bytes_uploaded': 0,
            'chunks_uploaded': 0,
            'total_chunks': (file_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE,
            'status': 'initiated',
            'metadata': metadata or {},
            'temp_file': str(self.temp_dir / f"{upload_id}.tmp")
        }

        # Store in Redis with TTL
        self.redis_client.setex(
            f"upload:{upload_id}",
            self.UPLOAD_TTL,
            json.dumps(session_data)
        )

        # Create temporary file
        temp_file = Path(session_data['temp_file'])
        temp_file.touch()

        return {
            'upload_id': upload_id,
            'chunk_size': self.CHUNK_SIZE,
            'total_chunks': session_data['total_chunks'],
            'expires_in': self.UPLOAD_TTL
        }

    def upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_data: bytes
    ) -> Dict[str, Any]:
        """
        Upload a file chunk

        Args:
            upload_id: Upload session ID
            chunk_index: Chunk index (0-based)
            chunk_data: Chunk bytes

        Returns:
            Upload progress

        Raises:
            ValueError: If upload session not found or chunk invalid

        Example:
            progress = service.upload_chunk(
                upload_id,
                chunk_index=0,
                chunk_data=chunk_bytes
            )
            print(f"Progress: {progress['progress_percent']}%")
        """
        # Get upload session
        session = self._get_upload_session(upload_id)
        if not session:
            raise ValueError(f"Upload session not found: {upload_id}")

        # Validate chunk
        total_chunks = session['total_chunks']
        if chunk_index < 0 or chunk_index >= total_chunks:
            raise ValueError(f"Invalid chunk index: {chunk_index}")

        # Write chunk to temp file
        temp_file = Path(session['temp_file'])
        if not temp_file.exists():
            raise ValueError(f"Temporary file not found for upload: {upload_id}")

        offset = chunk_index * self.CHUNK_SIZE

        with open(temp_file, 'r+b') as f:
            f.seek(offset)
            f.write(chunk_data)

        # Update session
        session['bytes_uploaded'] = session.get('bytes_uploaded', 0) + len(chunk_data)
        session['chunks_uploaded'] = session.get('chunks_uploaded', 0) + 1

        # Mark chunk as uploaded
        self.redis_client.sadd(f"upload:{upload_id}:chunks", str(chunk_index))

        # Update session in Redis
        self.redis_client.setex(
            f"upload:{upload_id}",
            self.UPLOAD_TTL,
            json.dumps(session)
        )

        # Calculate progress
        progress_percent = (session['bytes_uploaded'] / session['file_size']) * 100

        return {
            'upload_id': upload_id,
            'chunk_index': chunk_index,
            'bytes_uploaded': session['bytes_uploaded'],
            'total_bytes': session['file_size'],
            'chunks_uploaded': session['chunks_uploaded'],
            'total_chunks': total_chunks,
            'progress_percent': round(progress_percent, 2),
            'is_complete': session['chunks_uploaded'] >= total_chunks
        }

    def finalize_upload(
        self,
        upload_id: str
    ) -> Dict[str, Any]:
        """
        Finalize upload and verify file integrity

        Args:
            upload_id: Upload session ID

        Returns:
            Finalized upload details with temp_file path

        Raises:
            ValueError: If upload incomplete or verification fails

        Example:
            result = service.finalize_upload(upload_id)
            temp_file = result['temp_file']
            # Now upload temp_file to Cloudflare Stream
        """
        # Get upload session
        session = self._get_upload_session(upload_id)
        if not session:
            raise ValueError(f"Upload session not found: {upload_id}")

        # Verify all chunks uploaded
        if session['chunks_uploaded'] < session['total_chunks']:
            raise ValueError(
                f"Upload incomplete: {session['chunks_uploaded']}/{session['total_chunks']} chunks uploaded"
            )

        # Verify file size
        temp_file = Path(session['temp_file'])
        if not temp_file.exists():
            raise ValueError(f"Temporary file not found: {upload_id}")

        actual_size = temp_file.stat().st_size
        expected_size = session['file_size']

        if actual_size != expected_size:
            raise ValueError(
                f"File size mismatch: expected {expected_size}, got {actual_size}"
            )

        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(temp_file)

        # Update session status
        session['status'] = 'completed'
        session['file_hash'] = file_hash

        self.redis_client.setex(
            f"upload:{upload_id}",
            self.UPLOAD_TTL,
            json.dumps(session)
        )

        return {
            'upload_id': upload_id,
            'file_name': session['file_name'],
            'file_size': session['file_size'],
            'temp_file': session['temp_file'],
            'file_hash': file_hash,
            'metadata': session.get('metadata', {})
        }

    def get_upload_progress(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """
        Get upload progress

        Args:
            upload_id: Upload session ID

        Returns:
            Upload progress or None if not found

        Example:
            progress = service.get_upload_progress(upload_id)
            if progress:
                print(f"{progress['progress_percent']}% complete")
        """
        session = self._get_upload_session(upload_id)
        if not session:
            return None

        progress_percent = (session.get('bytes_uploaded', 0) / session['file_size']) * 100

        return {
            'upload_id': upload_id,
            'file_name': session['file_name'],
            'bytes_uploaded': session.get('bytes_uploaded', 0),
            'total_bytes': session['file_size'],
            'chunks_uploaded': session.get('chunks_uploaded', 0),
            'total_chunks': session['total_chunks'],
            'progress_percent': round(progress_percent, 2),
            'status': session.get('status', 'initiated'),
            'is_complete': session.get('chunks_uploaded', 0) >= session['total_chunks']
        }

    def cancel_upload(self, upload_id: str) -> bool:
        """
        Cancel upload and cleanup temporary files

        Args:
            upload_id: Upload session ID

        Returns:
            True if canceled successfully
        """
        session = self._get_upload_session(upload_id)
        if not session:
            return False

        # Delete temporary file
        temp_file = Path(session['temp_file'])
        if temp_file.exists():
            temp_file.unlink()

        # Delete Redis keys
        self.redis_client.delete(f"upload:{upload_id}")
        self.redis_client.delete(f"upload:{upload_id}:chunks")

        return True

    def cleanup_temp_file(self, upload_id: str) -> bool:
        """
        Cleanup temporary file after successful upload to Cloudflare

        Args:
            upload_id: Upload session ID

        Returns:
            True if cleaned up successfully
        """
        session = self._get_upload_session(upload_id)
        if not session:
            return False

        # Delete temporary file
        temp_file = Path(session['temp_file'])
        if temp_file.exists():
            temp_file.unlink()

        # Keep session in Redis for audit trail, but mark as cleaned
        session['temp_file_deleted'] = True
        self.redis_client.setex(
            f"upload:{upload_id}",
            3600,  # Keep for 1 hour
            json.dumps(session)
        )

        return True

    def get_missing_chunks(self, upload_id: str) -> list[int]:
        """
        Get list of missing chunk indices for resumable upload

        Args:
            upload_id: Upload session ID

        Returns:
            List of missing chunk indices
        """
        session = self._get_upload_session(upload_id)
        if not session:
            return []

        total_chunks = session['total_chunks']

        # Get uploaded chunks from Redis set
        uploaded_chunks = self.redis_client.smembers(f"upload:{upload_id}:chunks")
        uploaded_indices = {int(idx) for idx in uploaded_chunks}

        # Find missing chunks
        missing = [i for i in range(total_chunks) if i not in uploaded_indices]

        return missing

    def _get_upload_session(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """Get upload session from Redis"""
        data = self.redis_client.get(f"upload:{upload_id}")
        if not data:
            return None

        return json.loads(data)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def cleanup_expired_uploads(self) -> int:
        """
        Cleanup expired upload temporary files

        Returns:
            Number of files cleaned up
        """
        # Redis TTL handles session expiry, but we need to cleanup temp files
        # This should be run periodically by a background job

        cleanup_count = 0

        # Find all temp files older than TTL
        for temp_file in self.temp_dir.glob("*.tmp"):
            # Check if file is older than TTL
            file_age = os.path.getmtime(temp_file)
            if (time.time() - file_age) > self.UPLOAD_TTL:
                temp_file.unlink()
                cleanup_count += 1

        return cleanup_count
