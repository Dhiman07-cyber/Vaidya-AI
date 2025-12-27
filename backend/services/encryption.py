"""
API Key Encryption Service
Provides AES-256-GCM encryption/decryption for API keys at rest

Requirements: 10.1, 30.1
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting API keys using AES-256-GCM
    
    Requirements:
    - 10.1: Store API keys encrypted at rest in the database
    - 30.1: Encrypt all API keys at rest using industry-standard encryption
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the encryption service with a key from environment
        
        Args:
            encryption_key: Base64-encoded 32-byte encryption key.
                          If None, reads from ENCRYPTION_KEY environment variable.
        
        Raises:
            ValueError: If encryption key is missing or invalid
        """
        # Get encryption key from parameter or environment
        key_b64 = encryption_key or os.getenv("ENCRYPTION_KEY")
        
        if not key_b64:
            raise ValueError(
                "Encryption key not found. Set ENCRYPTION_KEY environment variable "
                "with a base64-encoded 32-byte key."
            )
        
        try:
            # Decode the base64 key
            self.key = base64.b64decode(key_b64)
            
            # Verify key length (must be 32 bytes for AES-256)
            if len(self.key) != 32:
                raise ValueError(
                    f"Encryption key must be 32 bytes (256 bits), got {len(self.key)} bytes. "
                    "Generate a valid key with: python -c 'import os, base64; "
                    "print(base64.b64encode(os.urandom(32)).decode())'"
                )
            
            # Initialize AESGCM cipher
            self.cipher = AESGCM(self.key)
            
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            raise ValueError(f"Invalid encryption key: {str(e)}")
    
    def encrypt_key(self, plaintext: str) -> str:
        """
        Encrypt an API key using AES-256-GCM
        
        Args:
            plaintext: The plaintext API key to encrypt
            
        Returns:
            Base64-encoded encrypted data in format: nonce||ciphertext||tag
            The nonce is 12 bytes, prepended to the ciphertext
            
        Raises:
            ValueError: If plaintext is empty or encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty plaintext")
        
        try:
            # Generate a random 12-byte nonce (recommended for GCM)
            nonce = os.urandom(12)
            
            # Encrypt the plaintext
            # AESGCM.encrypt returns ciphertext with authentication tag appended
            ciphertext = self.cipher.encrypt(
                nonce,
                plaintext.encode('utf-8'),
                None  # No associated data
            )
            
            # Combine nonce and ciphertext for storage
            # Format: nonce (12 bytes) || ciphertext || tag (16 bytes)
            encrypted_data = nonce + ciphertext
            
            # Encode as base64 for database storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            logger.debug(f"Successfully encrypted API key (length: {len(plaintext)})")
            
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt API key: {str(e)}")
    
    def decrypt_key(self, ciphertext: str) -> str:
        """
        Decrypt an API key using AES-256-GCM
        
        Args:
            ciphertext: Base64-encoded encrypted data (nonce||ciphertext||tag)
            
        Returns:
            The decrypted plaintext API key
            
        Raises:
            ValueError: If ciphertext is empty, invalid, or decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty ciphertext")
        
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(ciphertext)
            
            # Extract nonce (first 12 bytes) and ciphertext (remaining bytes)
            if len(encrypted_data) < 12:
                raise ValueError("Invalid ciphertext: too short")
            
            nonce = encrypted_data[:12]
            ciphertext_with_tag = encrypted_data[12:]
            
            # Decrypt the ciphertext
            # AESGCM.decrypt verifies the authentication tag automatically
            plaintext_bytes = self.cipher.decrypt(
                nonce,
                ciphertext_with_tag,
                None  # No associated data
            )
            
            # Decode to string
            plaintext = plaintext_bytes.decode('utf-8')
            
            logger.debug(f"Successfully decrypted API key (length: {len(plaintext)})")
            
            return plaintext
            
        except InvalidTag:
            logger.error("Decryption failed: Invalid authentication tag")
            raise ValueError(
                "Failed to decrypt API key: Authentication tag verification failed. "
                "The data may have been tampered with or the wrong key was used."
            )
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt API key: {str(e)}")


# Singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get or create the singleton encryption service instance
    
    Returns:
        EncryptionService instance
        
    Raises:
        ValueError: If encryption service cannot be initialized
    """
    global _encryption_service
    
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    
    return _encryption_service


def encrypt_key(plaintext: str) -> str:
    """
    Convenience function to encrypt an API key
    
    Args:
        plaintext: The plaintext API key to encrypt
        
    Returns:
        Base64-encoded encrypted data
        
    Raises:
        ValueError: If encryption fails
    """
    service = get_encryption_service()
    return service.encrypt_key(plaintext)


def decrypt_key(ciphertext: str) -> str:
    """
    Convenience function to decrypt an API key
    
    Args:
        ciphertext: Base64-encoded encrypted data
        
    Returns:
        The decrypted plaintext API key
        
    Raises:
        ValueError: If decryption fails
    """
    service = get_encryption_service()
    return service.decrypt_key(ciphertext)
