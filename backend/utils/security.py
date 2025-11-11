"""
Security Utilities (US-070)

This module provides security utilities for:
- Path traversal prevention
- Command injection prevention
- Secure file operations
- Safe subprocess execution
- Security headers
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import Request
from fastapi.responses import Response


# ============================================================================
# PATH TRAVERSAL PREVENTION
# ============================================================================

def is_safe_path(path: str, allowed_dir: str) -> bool:
    """
    Check if path is within allowed directory (prevent path traversal)

    Args:
        path: Path to validate
        allowed_dir: Allowed base directory

    Returns:
        True if path is safe (within allowed_dir), False otherwise

    Example:
        >>> is_safe_path("/uploads/user/file.jpg", "/uploads")
        True
        >>> is_safe_path("../../etc/passwd", "/uploads")
        False
    """
    try:
        # Convert to absolute paths and resolve symlinks
        base_dir = Path(allowed_dir).resolve()
        target_path = (base_dir / path).resolve()

        # Check if target path is relative to base directory
        return target_path.is_relative_to(base_dir)

    except Exception:
        return False


def validate_file_path(path: str, allowed_directories: List[str]) -> bool:
    """
    Validate file path against list of allowed directories

    Args:
        path: File path to validate
        allowed_directories: List of allowed base directories

    Returns:
        True if path is in one of the allowed directories, False otherwise
    """
    for allowed_dir in allowed_directories:
        if is_safe_path(path, allowed_dir):
            return True
    return False


def safe_join_path(base_dir: str, *paths: str) -> Optional[Path]:
    """
    Safely join paths and verify result is within base directory

    Args:
        base_dir: Base directory
        *paths: Path components to join

    Returns:
        Resolved Path object if safe, None if path traversal detected

    Example:
        >>> safe_join_path("/uploads", "user", "file.jpg")
        Path('/uploads/user/file.jpg')
        >>> safe_join_path("/uploads", "..", "etc", "passwd")
        None
    """
    try:
        base = Path(base_dir).resolve()
        joined = base.joinpath(*paths).resolve()

        # Verify result is within base directory
        if joined.is_relative_to(base):
            return joined
        return None

    except Exception:
        return None


def get_safe_filename(filename: str) -> str:
    """
    Get safe filename by removing path components

    Args:
        filename: Original filename (may include path)

    Returns:
        Filename without path components
    """
    # Remove all path separators and get basename
    return os.path.basename(filename.replace('\\', '/'))


# ============================================================================
# COMMAND INJECTION PREVENTION
# ============================================================================

def safe_subprocess_run(
    command: List[str],
    timeout: int = 30,
    check: bool = True,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """
    Safely execute subprocess command

    Security features:
    - Never uses shell=True
    - Command as list (no string concatenation)
    - Timeout to prevent hanging
    - Validates command is in whitelist

    Args:
        command: Command and arguments as list
        timeout: Timeout in seconds
        check: Whether to raise CalledProcessError on non-zero exit
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess object

    Raises:
        ValueError: If command is not allowed
        subprocess.TimeoutExpired: If timeout exceeded
        subprocess.CalledProcessError: If check=True and command fails

    Example:
        >>> safe_subprocess_run(["/usr/bin/convert", "input.jpg", "output.png"])
    """
    # Validate command is a list
    if not isinstance(command, list) or len(command) == 0:
        raise ValueError("Command must be a non-empty list")

    # Whitelist of allowed executables (absolute paths)
    ALLOWED_EXECUTABLES = {
        '/usr/bin/convert',  # ImageMagick
        '/usr/bin/ffmpeg',   # Video processing
        '/usr/bin/gs',       # Ghostscript (PDF)
        '/usr/bin/pdfinfo',  # PDF info
    }

    # Get executable path
    executable = command[0]

    # Resolve to absolute path if relative
    if not os.path.isabs(executable):
        executable = os.path.abspath(executable)

    # Check if executable is in whitelist
    if executable not in ALLOWED_EXECUTABLES:
        raise ValueError(f"Executable not allowed: {executable}")

    # Verify executable exists and is executable
    if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
        raise ValueError(f"Executable not found or not executable: {executable}")

    # Execute command safely (never with shell=True)
    return subprocess.run(
        command,
        shell=False,  # NEVER use shell=True
        timeout=timeout,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def validate_command_arguments(args: List[str]) -> bool:
    """
    Validate command arguments for dangerous patterns

    Args:
        args: List of command arguments

    Returns:
        True if arguments are safe, False otherwise
    """
    dangerous_patterns = [
        ';', '|', '&', '$', '`', '\n', '\r',
        '>', '<', '$(', '${',
    ]

    for arg in args:
        for pattern in dangerous_patterns:
            if pattern in arg:
                return False

    return True


# ============================================================================
# SECURITY HEADERS
# ============================================================================

def add_security_headers(response: Response) -> Response:
    """
    Add security headers to response

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: HSTS
    - Content-Security-Policy: CSP
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: restrict features

    Args:
        response: FastAPI Response object

    Returns:
        Response with security headers added
    """
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Force HTTPS (HSTS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "media-src 'self' https://customer-*.cloudflarestream.com; "
        "connect-src 'self' https://api.stripe.com https://api.openai.com; "
        "frame-src 'self' https://js.stripe.com https://hooks.stripe.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp

    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions policy (restrict dangerous features)
    permissions = (
        "camera=(), "
        "microphone=(), "
        "geolocation=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )
    response.headers['Permissions-Policy'] = permissions

    return response


def get_csp_header(
    allow_inline_scripts: bool = False,
    allow_inline_styles: bool = False,
    additional_script_sources: Optional[List[str]] = None,
    additional_style_sources: Optional[List[str]] = None
) -> str:
    """
    Generate Content Security Policy header

    Args:
        allow_inline_scripts: Whether to allow inline scripts
        allow_inline_styles: Whether to allow inline styles
        additional_script_sources: Additional script sources to allow
        additional_style_sources: Additional style sources to allow

    Returns:
        CSP header value
    """
    script_src = ["'self'"]
    if allow_inline_scripts:
        script_src.append("'unsafe-inline'")
    if additional_script_sources:
        script_src.extend(additional_script_sources)

    style_src = ["'self'"]
    if allow_inline_styles:
        style_src.append("'unsafe-inline'")
    if additional_style_sources:
        style_src.extend(additional_style_sources)

    csp = (
        f"default-src 'self'; "
        f"script-src {' '.join(script_src)}; "
        f"style-src {' '.join(style_src)}; "
        f"img-src 'self' data: https:; "
        f"font-src 'self'; "
        f"connect-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self';"
    )

    return csp


# ============================================================================
# REQUEST VALIDATION
# ============================================================================

def validate_content_type(request: Request, allowed_types: List[str]) -> bool:
    """
    Validate request Content-Type header

    Args:
        request: FastAPI Request object
        allowed_types: List of allowed content types

    Returns:
        True if content type is allowed, False otherwise
    """
    content_type = request.headers.get('content-type', '').split(';')[0].strip()
    return content_type in allowed_types


def validate_origin(request: Request, allowed_origins: List[str]) -> bool:
    """
    Validate request Origin header (CORS)

    Args:
        request: FastAPI Request object
        allowed_origins: List of allowed origins

    Returns:
        True if origin is allowed, False otherwise
    """
    origin = request.headers.get('origin', '')
    if not origin:
        return True  # No origin header (non-CORS request)

    return origin in allowed_origins


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request

    Checks X-Forwarded-For header (for proxies/load balancers)
    Falls back to direct client IP

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (set by proxies/load balancers)
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, use the first (client IP)
        return forwarded_for.split(',')[0].strip()

    # Check X-Real-IP header (set by some proxies)
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return 'unknown'


# ============================================================================
# RATE LIMITING HELPERS
# ============================================================================

def get_rate_limit_key(request: Request, include_path: bool = True) -> str:
    """
    Generate rate limit key from request

    Args:
        request: FastAPI Request object
        include_path: Whether to include path in key

    Returns:
        Rate limit key (e.g., "ip:1.2.3.4:path:/api/login")
    """
    ip = get_client_ip(request)

    if include_path:
        path = request.url.path
        return f"ip:{ip}:path:{path}"
    else:
        return f"ip:{ip}"


# ============================================================================
# CRYPTOGRAPHIC HELPERS
# ============================================================================

def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison (prevent timing attacks)

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings are equal, False otherwise
    """
    import hmac
    return hmac.compare_digest(a.encode(), b.encode())


def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token

    Args:
        length: Token length in bytes

    Returns:
        Hex-encoded secure random token
    """
    import secrets
    return secrets.token_hex(length)


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """
    Hash sensitive data (e.g., IP addresses) for privacy

    Args:
        data: Data to hash
        salt: Optional salt (uses default if not provided)

    Returns:
        SHA256 hash of data
    """
    import hashlib

    if salt:
        data_with_salt = f"{data}:{salt}"
    else:
        data_with_salt = data

    return hashlib.sha256(data_with_salt.encode()).hexdigest()


# ============================================================================
# FILE PERMISSIONS
# ============================================================================

def set_secure_file_permissions(file_path: str, mode: int = 0o600) -> None:
    """
    Set secure file permissions (owner read/write only)

    Args:
        file_path: Path to file
        mode: Permission mode (default: 0o600 = rw-------)
    """
    os.chmod(file_path, mode)


def verify_file_permissions(file_path: str, max_permissions: int = 0o600) -> bool:
    """
    Verify file has secure permissions

    Args:
        file_path: Path to file
        max_permissions: Maximum allowed permissions

    Returns:
        True if permissions are secure, False otherwise
    """
    stat_info = os.stat(file_path)
    current_permissions = stat_info.st_mode & 0o777

    return current_permissions <= max_permissions


# ============================================================================
# ENVIRONMENT VARIABLE SECURITY
# ============================================================================

def load_env_secrets(env_file: str = '.env') -> Dict[str, str]:
    """
    Load secrets from .env file with validation

    Args:
        env_file: Path to .env file

    Returns:
        Dictionary of environment variables

    Raises:
        ValueError: If .env file has insecure permissions
    """
    # Verify .env file has secure permissions
    if os.path.exists(env_file):
        if not verify_file_permissions(env_file, max_permissions=0o640):
            raise ValueError(f"{env_file} has insecure permissions. Should be 0o600 or 0o640")

    # Load environment variables
    from dotenv import dotenv_values
    return dotenv_values(env_file)


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Bcrypt hash
    """
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hash

    Returns:
        True if password matches, False otherwise
    """
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)
