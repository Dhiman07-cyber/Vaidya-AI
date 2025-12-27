"""
Property-based tests for encryption service
Tests universal properties that should hold for all valid inputs
Requirements: 10.1, 10.5, 30.1
"""
import pytest
from hypothesis import given, strategies as st, settings
import sys
import os
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.encryption import EncryptionService, encrypt_key, decrypt_key


# Custom strategies for generating valid test data
@st.composite
def valid_api_key(draw):
    """Generate valid API key strings"""
    # API keys can be various formats, generate realistic ones
    key_type = draw(st.sampled_from(['alphanumeric', 'base64', 'hex']))
    
    if key_type == 'alphanumeric':
        # Like: sk-1234567890abcdefghijklmnopqrstuvwxyz
        return draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        )))
    elif key_type == 'base64':
        # Like: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=
        random_bytes = draw(st.binary(min_size=20, max_size=100))
        return base64.b64encode(random_bytes).decode('utf-8')
    else:  # hex
        # Like: 0123456789abcdef0123456789abcdef
        return draw(st.text(min_size=20, max_size=100, alphabet='0123456789abcdef'))


@st.composite
def valid_encryption_key(draw):
    """Generate valid 32-byte encryption keys (base64-encoded)"""
    # Generate 32 random bytes and encode as base64
    key_bytes = draw(st.binary(min_size=32, max_size=32))
    return base64.b64encode(key_bytes).decode('utf-8')


# Feature: medical-ai-platform, Property 26: API keys are encrypted at rest
@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_api_keys_encrypted_at_rest(plaintext_key, encryption_key):
    """
    Property 26: For any API key stored in the database, 
    the key_value field should contain encrypted data (not plaintext).
    
    This property tests:
    1. Encryption produces output different from input (not plaintext)
    2. Encrypted output is not empty
    3. Encrypted output is base64-encoded (suitable for database storage)
    4. Round-trip encryption/decryption preserves the original value
    5. Same plaintext with different nonces produces different ciphertext
    
    Validates: Requirements 10.1, 10.5, 30.1
    """
    # Create encryption service with test key
    service = EncryptionService(encryption_key=encryption_key)
    
    # Encrypt the API key
    encrypted = service.encrypt_key(plaintext_key)
    
    # Property 1: Encrypted data should not be empty
    assert encrypted, "Encrypted data should not be empty"
    
    # Property 2: Encrypted data should be different from plaintext
    # (unless by extreme coincidence, which is cryptographically negligible)
    assert encrypted != plaintext_key, \
        "Encrypted data should not match plaintext (data should be encrypted)"
    
    # Property 3: Encrypted data should be valid base64
    try:
        decoded = base64.b64decode(encrypted)
        assert len(decoded) > 0, "Decoded encrypted data should not be empty"
    except Exception as e:
        pytest.fail(f"Encrypted data should be valid base64: {e}")
    
    # Property 4: Encrypted data should be longer than plaintext
    # (due to nonce and authentication tag)
    # Nonce: 12 bytes, Tag: 16 bytes, so at least 28 bytes overhead
    decoded_length = len(base64.b64decode(encrypted))
    plaintext_length = len(plaintext_key.encode('utf-8'))
    assert decoded_length >= plaintext_length + 28, \
        f"Encrypted data should be longer than plaintext (nonce + tag overhead). " \
        f"Got {decoded_length} bytes, expected at least {plaintext_length + 28} bytes"
    
    # Property 5: Round-trip encryption/decryption should preserve original value
    decrypted = service.decrypt_key(encrypted)
    assert decrypted == plaintext_key, \
        f"Round-trip encryption/decryption should preserve original value. " \
        f"Expected '{plaintext_key}', got '{decrypted}'"
    
    # Property 6: Encrypting the same plaintext twice should produce different ciphertext
    # (due to random nonce generation)
    encrypted2 = service.encrypt_key(plaintext_key)
    assert encrypted != encrypted2, \
        "Encrypting the same plaintext twice should produce different ciphertext " \
        "(due to random nonce)"
    
    # Property 7: Both encryptions should decrypt to the same plaintext
    decrypted2 = service.decrypt_key(encrypted2)
    assert decrypted2 == plaintext_key, \
        "Both encryptions should decrypt to the same plaintext"


@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_encryption_round_trip(plaintext_key, encryption_key):
    """
    Property: For any API key, encrypting then decrypting 
    should return the original value (round-trip property).
    
    This is a fundamental correctness property for encryption.
    
    Validates: Requirements 10.1, 30.1
    """
    # Create encryption service with test key
    service = EncryptionService(encryption_key=encryption_key)
    
    # Encrypt then decrypt
    encrypted = service.encrypt_key(plaintext_key)
    decrypted = service.decrypt_key(encrypted)
    
    # Property: decrypt(encrypt(x)) == x
    assert decrypted == plaintext_key, \
        f"Round-trip encryption should preserve original value. " \
        f"Original: '{plaintext_key}', After round-trip: '{decrypted}'"


@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_encryption_deterministic_decryption(plaintext_key, encryption_key):
    """
    Property: For any encrypted API key, decrypting it multiple times 
    should always return the same plaintext.
    
    Validates: Requirements 10.1, 30.1
    """
    # Create encryption service with test key
    service = EncryptionService(encryption_key=encryption_key)
    
    # Encrypt once
    encrypted = service.encrypt_key(plaintext_key)
    
    # Decrypt multiple times
    decrypted1 = service.decrypt_key(encrypted)
    decrypted2 = service.decrypt_key(encrypted)
    decrypted3 = service.decrypt_key(encrypted)
    
    # Property: All decryptions should return the same value
    assert decrypted1 == decrypted2 == decrypted3 == plaintext_key, \
        "Decrypting the same ciphertext multiple times should always return the same plaintext"


@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_encryption_non_deterministic(plaintext_key, encryption_key):
    """
    Property: For any API key, encrypting it multiple times 
    should produce different ciphertext (due to random nonce).
    
    This ensures that the same API key stored multiple times 
    will have different encrypted values, improving security.
    
    Validates: Requirements 10.1, 30.1
    """
    # Create encryption service with test key
    service = EncryptionService(encryption_key=encryption_key)
    
    # Encrypt the same plaintext multiple times
    encrypted1 = service.encrypt_key(plaintext_key)
    encrypted2 = service.encrypt_key(plaintext_key)
    encrypted3 = service.encrypt_key(plaintext_key)
    
    # Property: All encryptions should be different (due to random nonce)
    assert encrypted1 != encrypted2, \
        "Encrypting the same plaintext twice should produce different ciphertext"
    assert encrypted2 != encrypted3, \
        "Encrypting the same plaintext twice should produce different ciphertext"
    assert encrypted1 != encrypted3, \
        "Encrypting the same plaintext twice should produce different ciphertext"
    
    # But all should decrypt to the same plaintext
    decrypted1 = service.decrypt_key(encrypted1)
    decrypted2 = service.decrypt_key(encrypted2)
    decrypted3 = service.decrypt_key(encrypted3)
    
    assert decrypted1 == decrypted2 == decrypted3 == plaintext_key, \
        "All encryptions should decrypt to the same plaintext"


@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_tamper_detection(plaintext_key, encryption_key):
    """
    Property: For any encrypted API key, modifying the ciphertext 
    should cause decryption to fail (authentication tag verification).
    
    This tests the integrity protection provided by AES-GCM.
    
    Validates: Requirements 30.1
    """
    # Create encryption service with test key
    service = EncryptionService(encryption_key=encryption_key)
    
    # Encrypt the API key
    encrypted = service.encrypt_key(plaintext_key)
    
    # Decode the base64 to get raw bytes
    encrypted_bytes = base64.b64decode(encrypted)
    
    # Tamper with the ciphertext (flip a bit in the middle)
    if len(encrypted_bytes) > 20:
        tampered_bytes = bytearray(encrypted_bytes)
        # Flip a bit in the ciphertext portion (after nonce)
        tampered_bytes[15] ^= 0x01
        tampered_encrypted = base64.b64encode(bytes(tampered_bytes)).decode('utf-8')
        
        # Property: Decrypting tampered ciphertext should fail
        with pytest.raises(ValueError, match="authentication tag|tampered|wrong key"):
            service.decrypt_key(tampered_encrypted)


@given(
    plaintext_key=valid_api_key(),
    correct_key=valid_encryption_key(),
    wrong_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_wrong_key_fails(plaintext_key, correct_key, wrong_key):
    """
    Property: For any encrypted API key, attempting to decrypt 
    with a different key should fail.
    
    Validates: Requirements 30.1
    """
    # Skip if keys happen to be the same (very unlikely)
    if correct_key == wrong_key:
        return
    
    # Create encryption service with correct key
    service_correct = EncryptionService(encryption_key=correct_key)
    
    # Encrypt with correct key
    encrypted = service_correct.encrypt_key(plaintext_key)
    
    # Try to decrypt with wrong key
    service_wrong = EncryptionService(encryption_key=wrong_key)
    
    # Property: Decrypting with wrong key should fail
    with pytest.raises(ValueError, match="authentication tag|tampered|wrong key"):
        service_wrong.decrypt_key(encrypted)


@given(
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_empty_plaintext_rejected(encryption_key):
    """
    Property: For any encryption service, attempting to encrypt 
    an empty string should fail with a clear error.
    
    Validates: Requirements 10.1
    """
    # Create encryption service
    service = EncryptionService(encryption_key=encryption_key)
    
    # Property: Encrypting empty string should raise ValueError
    with pytest.raises(ValueError, match="empty"):
        service.encrypt_key("")


@given(
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_empty_ciphertext_rejected(encryption_key):
    """
    Property: For any encryption service, attempting to decrypt 
    an empty string should fail with a clear error.
    
    Validates: Requirements 10.1
    """
    # Create encryption service
    service = EncryptionService(encryption_key=encryption_key)
    
    # Property: Decrypting empty string should raise ValueError
    with pytest.raises(ValueError, match="empty"):
        service.decrypt_key("")


@given(
    plaintext_key=valid_api_key(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
def test_property_convenience_functions(plaintext_key, encryption_key):
    """
    Property: The convenience functions encrypt_key() and decrypt_key() 
    should work the same as the service methods.
    
    Validates: Requirements 10.1
    """
    # Set environment variable for convenience functions
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Use convenience functions
        encrypted = encrypt_key(plaintext_key)
        decrypted = decrypt_key(encrypted)
        
        # Property: Round-trip should preserve original value
        assert decrypted == plaintext_key, \
            "Convenience functions should preserve original value in round-trip"
        
        # Property: Encrypted data should not be plaintext
        assert encrypted != plaintext_key, \
            "Convenience functions should encrypt data"
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]
