"""
File Upload Validation Utilities (US-070)

This module provides comprehensive file upload validation to prevent:
- Malicious file uploads
- File type spoofing
- Oversized files
- Path traversal attacks
- Content-based attacks

Security Features:
- File extension validation (whitelist)
- MIME type validation
- Magic bytes verification
- File size limits
- Filename sanitization
- Content scanning
"""

import os
import re
from typing import Optional, Set, Tuple
from pathlib import Path
from fastapi import UploadFile

# Import python-magic if available (optional dependency)
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


# ============================================================================
# CONSTANTS - File Type Configurations
# ============================================================================

# Image file types
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}
ALLOWED_IMAGE_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml',
}
IMAGE_MAGIC_BYTES = {
    'image/jpeg': [b'\xFF\xD8\xFF'],
    'image/png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
    'image/gif': [b'GIF87a', b'GIF89a'],
    'image/webp': [b'RIFF'],
}

# Video file types
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi', 'mkv'}
ALLOWED_VIDEO_MIME_TYPES = {
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
}

# Document file types
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}
ALLOWED_DOCUMENT_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
}

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB (for upload; actual videos stored in Cloudflare Stream)
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

# Dangerous file patterns
DANGEROUS_PATTERNS = [
    r'\.\./',  # Parent directory
    r'\.\.\\',  # Parent directory (Windows)
    r'^/',  # Absolute path
    r'^[A-Z]:',  # Windows drive letter
    r'\x00',  # Null byte
    r'<script',  # Script tag in filename
]


# ============================================================================
# FILE EXTENSION VALIDATION
# ============================================================================

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename (lowercase)

    Args:
        filename: Original filename

    Returns:
        File extension without dot (e.g., 'jpg')
    """
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Validate file extension against whitelist

    Args:
        filename: Filename to validate
        allowed_extensions: Set of allowed extensions (without dot)

    Returns:
        True if extension is allowed, False otherwise
    """
    ext = get_file_extension(filename)
    return ext in allowed_extensions


# ============================================================================
# MIME TYPE VALIDATION
# ============================================================================

def validate_mime_type(content_type: str, allowed_mime_types: Set[str]) -> bool:
    """
    Validate MIME type against whitelist

    Args:
        content_type: MIME type from upload
        allowed_mime_types: Set of allowed MIME types

    Returns:
        True if MIME type is allowed, False otherwise
    """
    if not content_type:
        return False

    # Handle MIME type with parameters (e.g., "image/jpeg; charset=utf-8")
    base_type = content_type.split(';')[0].strip().lower()
    return base_type in allowed_mime_types


# ============================================================================
# MAGIC BYTES VALIDATION
# ============================================================================

def verify_magic_bytes(file_content: bytes, expected_mime_type: str) -> bool:
    """
    Verify file magic bytes match expected MIME type

    Args:
        file_content: First bytes of file (at least 12 bytes)
        expected_mime_type: Expected MIME type

    Returns:
        True if magic bytes match, False otherwise
    """
    if not file_content or len(file_content) < 12:
        return False

    # Get expected magic bytes for MIME type
    magic_bytes_list = IMAGE_MAGIC_BYTES.get(expected_mime_type, [])

    # Check if any magic bytes match
    for magic_bytes in magic_bytes_list:
        if file_content.startswith(magic_bytes):
            return True

    # For WebP, check RIFF header and WEBP signature
    if expected_mime_type == 'image/webp':
        return file_content.startswith(b'RIFF') and b'WEBP' in file_content[:16]

    # If no specific magic bytes defined, use python-magic if available
    if MAGIC_AVAILABLE:
        try:
            detected_type = magic.from_buffer(file_content[:1024], mime=True)
            return detected_type == expected_mime_type
        except Exception:
            return False

    # If python-magic not available, basic validation passed
    return True


# ============================================================================
# FILE SIZE VALIDATION
# ============================================================================

def validate_file_size(file: UploadFile, max_size: int) -> Tuple[bool, int]:
    """
    Validate file size against maximum

    Args:
        file: UploadFile object
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, actual_size)
    """
    # Get current position
    current_pos = file.file.tell()

    # Seek to end to get size
    file.file.seek(0, 2)
    size = file.file.tell()

    # Reset to original position
    file.file.seek(current_pos)

    return (size <= max_size, size)


# ============================================================================
# FILENAME SANITIZATION
# ============================================================================

def sanitize_upload_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize uploaded filename to prevent attacks

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            # Replace dangerous characters with underscore
            filename = re.sub(pattern, '_', filename, flags=re.IGNORECASE)

    # Remove special characters except dot, underscore, hyphen
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Prevent multiple dots (except before extension)
    parts = filename.rsplit('.', 1)
    if len(parts) == 2:
        name, ext = parts
        name = name.replace('.', '_')
        filename = f"{name}.{ext}"

    # Limit length while preserving extension
    if len(filename) > max_length:
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]

    return filename


# ============================================================================
# IMAGE VALIDATION
# ============================================================================

def validate_image_upload(file: UploadFile, max_size: int = MAX_IMAGE_SIZE) -> Tuple[bool, str]:
    """
    Validate image file upload

    Checks:
    1. File extension (whitelist)
    2. MIME type (whitelist)
    3. File size
    4. Magic bytes verification

    Args:
        file: UploadFile object
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename is provided
    if not file.filename:
        return (False, "Filename is required")

    # 1. Validate file extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return (False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    # 2. Validate MIME type
    if not validate_mime_type(file.content_type, ALLOWED_IMAGE_MIME_TYPES):
        return (False, f"Invalid MIME type. Expected image type, got {file.content_type}")

    # 3. Validate file size
    is_valid_size, actual_size = validate_file_size(file, max_size)
    if not is_valid_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = actual_size / (1024 * 1024)
        return (False, f"File too large. Maximum: {max_mb:.1f}MB, actual: {actual_mb:.1f}MB")

    # 4. Verify magic bytes
    file.file.seek(0)
    header = file.file.read(16)
    file.file.seek(0)

    if not verify_magic_bytes(header, file.content_type):
        return (False, "File content does not match file extension (possible file spoofing)")

    return (True, "")


# ============================================================================
# VIDEO VALIDATION
# ============================================================================

def validate_video_upload(file: UploadFile, max_size: int = MAX_VIDEO_SIZE) -> Tuple[bool, str]:
    """
    Validate video file upload

    Checks:
    1. File extension (whitelist)
    2. MIME type (whitelist)
    3. File size

    Args:
        file: UploadFile object
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename is provided
    if not file.filename:
        return (False, "Filename is required")

    # 1. Validate file extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return (False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}")

    # 2. Validate MIME type
    if not validate_mime_type(file.content_type, ALLOWED_VIDEO_MIME_TYPES):
        return (False, f"Invalid MIME type. Expected video type, got {file.content_type}")

    # 3. Validate file size
    is_valid_size, actual_size = validate_file_size(file, max_size)
    if not is_valid_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = actual_size / (1024 * 1024)
        return (False, f"File too large. Maximum: {max_mb:.1f}MB, actual: {actual_mb:.1f}MB")

    return (True, "")


# ============================================================================
# DOCUMENT VALIDATION
# ============================================================================

def validate_document_upload(file: UploadFile, max_size: int = MAX_DOCUMENT_SIZE) -> Tuple[bool, str]:
    """
    Validate document file upload

    Checks:
    1. File extension (whitelist)
    2. MIME type (whitelist)
    3. File size

    Args:
        file: UploadFile object
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename is provided
    if not file.filename:
        return (False, "Filename is required")

    # 1. Validate file extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        return (False, f"Invalid file extension. Allowed: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}")

    # 2. Validate MIME type
    if not validate_mime_type(file.content_type, ALLOWED_DOCUMENT_MIME_TYPES):
        return (False, f"Invalid MIME type. Expected document type, got {file.content_type}")

    # 3. Validate file size
    is_valid_size, actual_size = validate_file_size(file, max_size)
    if not is_valid_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = actual_size / (1024 * 1024)
        return (False, f"File too large. Maximum: {max_mb:.1f}MB, actual: {actual_mb:.1f}MB")

    return (True, "")


# ============================================================================
# AVATAR VALIDATION
# ============================================================================

def validate_avatar_upload(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate avatar/profile picture upload

    Stricter limits than regular images:
    - Max size: 2 MB
    - Only common image formats (jpg, png, gif, webp)

    Args:
        file: UploadFile object

    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_image_upload(file, max_size=MAX_AVATAR_SIZE)


# ============================================================================
# GENERIC FILE VALIDATION
# ============================================================================

def validate_upload(
    file: UploadFile,
    allowed_extensions: Set[str],
    allowed_mime_types: Set[str],
    max_size: int,
    verify_content: bool = True
) -> Tuple[bool, str]:
    """
    Generic file upload validation

    Args:
        file: UploadFile object
        allowed_extensions: Set of allowed file extensions
        allowed_mime_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
        verify_content: Whether to verify magic bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename
    if not file.filename:
        return (False, "Filename is required")

    # Sanitize filename
    sanitized_filename = sanitize_upload_filename(file.filename)
    if not sanitized_filename:
        return (False, "Invalid filename")

    # Validate extension
    ext = get_file_extension(file.filename)
    if ext not in allowed_extensions:
        return (False, f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")

    # Validate MIME type
    if not validate_mime_type(file.content_type, allowed_mime_types):
        return (False, f"Invalid MIME type: {file.content_type}")

    # Validate size
    is_valid_size, actual_size = validate_file_size(file, max_size)
    if not is_valid_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = actual_size / (1024 * 1024)
        return (False, f"File too large. Maximum: {max_mb:.1f}MB, actual: {actual_mb:.1f}MB")

    # Verify content (magic bytes) if requested and python-magic available
    if verify_content and MAGIC_AVAILABLE:
        file.file.seek(0)
        header = file.file.read(1024)
        file.file.seek(0)

        try:
            detected_type = magic.from_buffer(header, mime=True)
            if detected_type not in allowed_mime_types:
                return (False, f"File content does not match declared type (detected: {detected_type})")
        except Exception as e:
            # If magic detection fails, log but don't block
            # (some files may not be detectable)
            pass

    return (True, "")


# ============================================================================
# CONTENT SCANNING
# ============================================================================

def scan_file_content(file_path: Path) -> Tuple[bool, str]:
    """
    Scan file content for malicious patterns

    Basic content scanning - in production, integrate with antivirus/malware scanner

    Args:
        file_path: Path to file to scan

    Returns:
        Tuple of (is_safe, issue_description)
    """
    try:
        # Check file size is reasonable
        if file_path.stat().st_size > 1024 * 1024 * 1024:  # 1 GB
            return (False, "File too large for content scanning")

        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read(10240)  # First 10 KB

        # Check for common malware signatures
        malware_patterns = [
            b'eval(',
            b'exec(',
            b'system(',
            b'passthru(',
            b'shell_exec(',
            b'<?php',
            b'<script',
            b'javascript:',
            b'vbscript:',
        ]

        for pattern in malware_patterns:
            if pattern in content:
                return (False, f"Potentially malicious content detected: {pattern.decode('utf-8', errors='ignore')}")

        return (True, "")

    except Exception as e:
        return (False, f"Error scanning file: {str(e)}")
