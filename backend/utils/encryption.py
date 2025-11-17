"""
Encryption Utility for Sensitive Data

Provides symmetric encryption/decryption for sensitive data like API keys,
passwords, and secrets stored in the database.

Uses Fernet (AES-128 CBC with HMAC for authentication) from cryptography library.
The encryption key is derived from JWT_SECRET for consistency.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from backend.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data

    Uses Fernet symmetric encryption with a key derived from JWT_SECRET.
    This ensures that encryption keys are managed consistently with the
    application's existing secret management.
    """

    def __init__(self):
        """Initialize encryption service with key derived from JWT_SECRET"""
        settings = get_settings()

        # Derive a 32-byte key from JWT_SECRET using SHA-256
        key_material = settings.JWT_SECRET.encode()
        derived_key = hashlib.sha256(key_material).digest()

        # Fernet requires a base64-encoded 32-byte key
        self._fernet_key = base64.urlsafe_b64encode(derived_key)
        self._fernet = Fernet(self._fernet_key)

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt a plaintext string

        Args:
            plaintext: The string to encrypt (None returns None)

        Returns:
            Base64-encoded encrypted string, or None if input is None

        Raises:
            ValueError: If encryption fails
        """
        if plaintext is None or plaintext == "":
            return None

        try:
            # Encrypt and return as string
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        """
        Decrypt an encrypted string

        Args:
            encrypted_text: The encrypted string to decrypt (None returns None)

        Returns:
            Decrypted plaintext string, or None if input is None

        Raises:
            ValueError: If decryption fails (invalid key or corrupted data)
        """
        if encrypted_text is None or encrypted_text == "":
            return None

        try:
            # Decrypt and return as string
            decrypted_bytes = self._fernet.decrypt(encrypted_text.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or wrong key")
            raise ValueError("Failed to decrypt data: Invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def is_encrypted(self, value: Optional[str]) -> bool:
        """
        Check if a value appears to be encrypted

        Args:
            value: The value to check

        Returns:
            True if the value appears to be encrypted (can be decrypted)
        """
        if value is None or value == "":
            return False

        try:
            self.decrypt(value)
            return True
        except ValueError:
            return False


# Global singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the global encryption service instance

    Returns:
        EncryptionService: Singleton encryption service instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# Convenience functions for direct use
def encrypt_value(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt a plaintext value"""
    return get_encryption_service().encrypt(plaintext)


def decrypt_value(encrypted_text: Optional[str]) -> Optional[str]:
    """Decrypt an encrypted value"""
    return get_encryption_service().decrypt(encrypted_text)


def is_encrypted(value: Optional[str]) -> bool:
    """Check if a value is encrypted"""
    return get_encryption_service().is_encrypted(value)
