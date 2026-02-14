"""
Encryption service for securely storing user API keys.

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
The encryption key is loaded from the ENCRYPTION_KEY environment variable,
which must be a valid Fernet key (generated via Fernet.generate_key()).
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Encrypt and decrypt sensitive data using Fernet."""

    def __init__(self):
        key = getattr(settings, "ENCRYPTION_KEY", None)
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY is not configured. "
                "Generate one with: python -c "
                '"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plain_text: str) -> str:
        """Encrypt plaintext string, return base64-encoded ciphertext."""
        return self._fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt base64-encoded ciphertext, return plaintext string."""
        try:
            return self._fernet.decrypt(encrypted_text.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt data — invalid token or wrong key")
            raise
