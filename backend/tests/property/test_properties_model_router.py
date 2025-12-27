"""
Property-based tests for model router service
Tests universal properties that should hold for all valid inputs
Requirements: 10.4, 10.6, 21.1
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.model_router import ModelRouterService
from services.encryption import encrypt_key


# Custom strategies for generating valid test data
@st.composite
def valid_provider(draw):
    """Generate valid provider names"""
    return draw(st.sampled_from(['gemini', 'openai', 'ollama', 'anthropic']))


@st.composite
def valid_feature(draw):
    """Generate valid feature names"""
    return draw(st.sampled_from(['chat', 'flashcard', 'mcq', 'highyield', 'explain', 'map', 'image']))


@st.composite
def valid_api_key_string(draw):
    """Generate valid API key strings"""
    return draw(st.text(min_size=20, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))


@st.composite
def valid_priority(draw):
    """Generate valid priority values"""
    return draw(st.integers(min_value=0, max_value=100))


@st.composite
def valid_key_status(draw):
    """Generate valid key status values"""
    return draw(st.sampled_from(['active', 'degraded', 'disabled']))


@st.composite
def valid_encryption_key(draw):
    """Generate valid 32-byte encryption keys (base64-encoded)"""
    key_bytes = draw(st.binary(min_size=32, max_size=32))
    return base64.b64encode(key_bytes).decode('utf-8')


# Feature: medical-ai-platform, Property 28: Higher priority keys are selected first
@given(
    provider=valid_provider(),
    feature=valid_feature(),
    priorities=st.lists(valid_priority(), min_size=2, max_size=5, unique=True),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_higher_priority_keys_selected_first(provider, feature, priorities, encryption_key):
    """
    Property 28: For any feature request requiring an API key, 
    the system should select the active key with the highest priority value.
    
    Validates: Requirements 10.4
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Sort priorities to find the highest
        sorted_priorities = sorted(priorities, reverse=True)
        highest_priority = sorted_priorities[0]
        
        # Create mock API keys with different priorities
        mock_keys = []
        for priority in priorities:
            api_key_plaintext = f"test-key-{priority}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            mock_keys.append({
                "id": f"key-{priority}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": priority,
                "status": "active",
                "last_used_at": None
            })
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain for get_active_key
        mock_response = MagicMock()
        # Return only the highest priority key (database would order by priority desc and limit 1)
        highest_priority_key = [k for k in mock_keys if k["priority"] == highest_priority][0]
        mock_response.data = [highest_priority_key]
        
        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_response
        
        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for last_used_at
        mock_update_response = MagicMock()
        mock_update_response.execute.return_value = MagicMock()
        mock_update_eq = MagicMock()
        mock_update_eq.execute.return_value = mock_update_response
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update_eq
        mock_table.update.return_value = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get active key
        result = await router.get_active_key(provider, feature)
        
        # Property: Should return the key with highest priority
        assert result is not None, "Should return a key"
        assert result["priority"] == highest_priority, \
            f"Should select key with highest priority {highest_priority}, got {result['priority']}"
        assert result["key_value"] == f"test-key-{highest_priority}", \
            "Should decrypt and return the correct key"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


# Feature: medical-ai-platform, Property 29: Backend decrypts and uses correct key
@given(
    provider=valid_provider(),
    feature=valid_feature(),
    api_key_plaintext=valid_api_key_string(),
    priority=valid_priority(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_backend_decrypts_and_uses_correct_key(
    provider, feature, api_key_plaintext, priority, encryption_key
):
    """
    Property 29: For any request requiring an API key, 
    the backend should decrypt the selected key and use it for the provider call.
    
    Validates: Requirements 10.6
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Encrypt the API key (as it would be stored in database)
        encrypted_key = encrypt_key(api_key_plaintext)
        
        # Create mock API key data
        mock_key_data = {
            "id": "test-key-id",
            "provider": provider,
            "feature": feature,
            "key_value": encrypted_key,  # Stored encrypted
            "priority": priority,
            "status": "active",
            "last_used_at": None
        }
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain
        mock_response = MagicMock()
        mock_response.data = [mock_key_data]
        
        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_response
        
        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for last_used_at
        mock_update_response = MagicMock()
        mock_update_response.execute.return_value = MagicMock()
        mock_update_eq = MagicMock()
        mock_update_eq.execute.return_value = mock_update_response
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update_eq
        mock_table.update.return_value = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get active key
        result = await router.get_active_key(provider, feature)
        
        # Property: Backend should decrypt the key and return plaintext
        assert result is not None, "Should return a key"
        assert result["key_value"] == api_key_plaintext, \
            f"Backend should decrypt key. Expected '{api_key_plaintext}', got '{result['key_value']}'"
        assert result["key_value"] != encrypted_key, \
            "Returned key should be decrypted (not encrypted)"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    num_keys=st.integers(min_value=2, max_value=5),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_all_active_keys_ordered_by_priority(provider, feature, num_keys, encryption_key):
    """
    Property: For any provider and feature, get_all_active_keys should return 
    all active keys ordered by priority (highest first).
    
    Validates: Requirements 10.4
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Generate random priorities
        priorities = list(range(num_keys))
        
        # Create mock API keys with different priorities
        mock_keys = []
        for i, priority in enumerate(priorities):
            api_key_plaintext = f"test-key-{priority}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            mock_keys.append({
                "id": f"key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": priority,
                "status": "active",
                "last_used_at": None
            })
        
        # Sort by priority descending (as database would)
        mock_keys_sorted = sorted(mock_keys, key=lambda k: k["priority"], reverse=True)
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain for get_all_active_keys
        mock_response = MagicMock()
        mock_response.data = mock_keys_sorted
        
        mock_order = MagicMock()
        mock_order.execute.return_value = mock_response
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get all active keys
        result = await router.get_all_active_keys(provider, feature)
        
        # Property: Should return all keys ordered by priority (highest first)
        assert len(result) == num_keys, f"Should return all {num_keys} keys"
        
        # Check ordering
        for i in range(len(result) - 1):
            assert result[i]["priority"] >= result[i + 1]["priority"], \
                f"Keys should be ordered by priority descending. " \
                f"Key at index {i} has priority {result[i]['priority']}, " \
                f"key at index {i+1} has priority {result[i+1]['priority']}"
        
        # Check all keys are decrypted
        for i, key in enumerate(result):
            expected_plaintext = f"test-key-{key['priority']}"
            assert key["key_value"] == expected_plaintext, \
                f"Key {i} should be decrypted"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    feature=valid_feature()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_select_provider_returns_valid_provider(feature):
    """
    Property: For any feature, select_provider should return a valid provider name.
    
    Validates: Requirements 21.1
    """
    # Create model router service
    router = ModelRouterService(supabase_client=MagicMock())
    
    # Select provider
    provider = await router.select_provider(feature)
    
    # Property: Should return a non-empty string
    assert provider, "Provider should not be empty"
    assert isinstance(provider, str), "Provider should be a string"
    
    # Property: Should return a known provider
    valid_providers = ['gemini', 'openai', 'ollama', 'anthropic']
    assert provider in valid_providers, \
        f"Provider '{provider}' should be one of {valid_providers}"


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_no_active_keys_returns_none(provider, feature, encryption_key):
    """
    Property: For any provider and feature with no active keys, 
    get_active_key should return None.
    
    Validates: Requirements 10.4
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain to return no keys
        mock_response = MagicMock()
        mock_response.data = []  # No keys
        
        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_response
        
        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get active key
        result = await router.get_active_key(provider, feature)
        
        # Property: Should return None when no active keys exist
        assert result is None, "Should return None when no active keys exist"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


# Feature: medical-ai-platform, Property 53: Failed requests trigger automatic retry
@given(
    feature=valid_feature(),
    num_keys=st.integers(min_value=2, max_value=4),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_failed_requests_trigger_automatic_retry(feature, num_keys, encryption_key):
    """
    Property 53: For any provider request that fails, 
    the system should automatically retry with the next available key.
    
    Validates: Requirements 21.2
    """
    # Only test with gemini provider (others not yet implemented)
    provider = 'gemini'
    
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock API keys with different priorities
        mock_keys = []
        for i in range(num_keys):
            api_key_plaintext = f"test-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            mock_keys.append({
                "id": f"key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": num_keys - i,  # Descending priority
                "status": "active",
                "failure_count": 0
            })
        
        # Sort by priority descending
        mock_keys_sorted = sorted(mock_keys, key=lambda k: k["priority"], reverse=True)
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock get_all_active_keys to return all keys
        mock_response = MagicMock()
        mock_response.data = mock_keys_sorted
        
        mock_order = MagicMock()
        mock_order.execute.return_value = mock_response
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for failure recording
        mock_update_response = MagicMock()
        mock_update_response.data = [{"failure_count": 1}]
        mock_update_response.execute.return_value = mock_update_response
        mock_update_eq = MagicMock()
        mock_update_eq.execute.return_value = mock_update_response
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update_eq
        mock_table.update.return_value = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Mock the Gemini provider to fail on first attempt, succeed on second
        call_count = [0]
        
        async def mock_call_gemini(self, api_key, prompt, system_prompt=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call fails
                return {
                    "success": False,
                    "error": "API key quota exceeded",
                    "tokens_used": 0
                }
            else:
                # Second call succeeds
                return {
                    "success": True,
                    "content": "Test response",
                    "tokens_used": 10
                }
        
        from services.providers.gemini import GeminiProvider
        with patch.object(GeminiProvider, 'call_gemini', new=mock_call_gemini):
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt="Test prompt"
            )
        
        # Property: Should retry with next key after first failure
        assert result["success"] is True, "Should succeed after retry"
        assert result["attempts"] == 2, f"Should have made 2 attempts, made {result['attempts']}"
        assert call_count[0] == 2, "Should have called provider twice"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    feature=valid_feature(),
    num_keys=st.integers(min_value=1, max_value=3),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_all_keys_fail_returns_error(feature, num_keys, encryption_key):
    """
    Property: For any provider request where all available keys fail,
    the system should return an error after exhausting all retries.
    
    Validates: Requirements 21.2, 21.3
    """
    # Only test with gemini provider (others not yet implemented)
    provider = 'gemini'
    
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock API keys
        mock_keys = []
        for i in range(num_keys):
            api_key_plaintext = f"test-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            mock_keys.append({
                "id": f"key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": num_keys - i,
                "status": "active",
                "failure_count": 0
            })
        
        # Sort by priority descending
        mock_keys_sorted = sorted(mock_keys, key=lambda k: k["priority"], reverse=True)
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock get_all_active_keys to return all keys
        mock_response = MagicMock()
        mock_response.data = mock_keys_sorted
        
        mock_order = MagicMock()
        mock_order.execute.return_value = mock_response
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for failure recording
        mock_update_response = MagicMock()
        mock_update_response.data = [{"failure_count": 1}]
        mock_update_response.execute.return_value = mock_update_response
        mock_update_eq = MagicMock()
        mock_update_eq.execute.return_value = mock_update_response
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update_eq
        mock_table.update.return_value = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Mock the Gemini provider to always fail
        call_count = [0]
        
        async def mock_call_gemini_fail(self, api_key, prompt, system_prompt=None):
            call_count[0] += 1
            return {
                "success": False,
                "error": "API key invalid",
                "tokens_used": 0
            }
        
        from services.providers.gemini import GeminiProvider
        with patch.object(GeminiProvider, 'call_gemini', new=mock_call_gemini_fail):
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt="Test prompt",
                max_retries=3
            )
        
        # Property: Should fail after trying all available keys (up to max_retries)
        assert result["success"] is False, "Should fail when all keys fail"
        expected_attempts = min(num_keys, 3)  # Limited by max_retries
        assert result["attempts"] == expected_attempts, \
            f"Should have made {expected_attempts} attempts, made {result['attempts']}"
        assert call_count[0] == expected_attempts, \
            f"Should have called provider {expected_attempts} times"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    feature=valid_feature(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_failure_count_incremented(feature, encryption_key):
    """
    Property: For any failed API key, the failure_count should be incremented.
    
    Validates: Requirements 21.2, 21.3
    """
    # Only test with gemini provider (others not yet implemented)
    provider = 'gemini'
    
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock API key
        api_key_plaintext = "test-key"
        encrypted_key = encrypt_key(api_key_plaintext)
        
        mock_key = {
            "id": "key-1",
            "provider": provider,
            "feature": feature,
            "key_value": encrypted_key,
            "priority": 1,
            "status": "active",
            "failure_count": 0
        }
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock select for getting current failure count
        mock_select_response = MagicMock()
        mock_select_response.data = [{"failure_count": 0}]
        
        mock_select_eq = MagicMock()
        mock_select_eq.execute.return_value = mock_select_response
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select_eq
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for incrementing failure count
        update_called = [False]
        update_value = [None]
        
        def mock_update(data):
            update_called[0] = True
            update_value[0] = data
            mock_update_eq = MagicMock()
            mock_update_eq.execute.return_value = MagicMock()
            mock_update_result = MagicMock()
            mock_update_result.eq.return_value = mock_update_eq
            return mock_update_result
        
        mock_table.update = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Record a failure
        await router.record_failure("key-1", "Test error")
        
        # Property: Update should have been called with incremented failure count
        assert update_called[0], "Update should have been called"
        assert update_value[0] is not None, "Update value should be set"
        assert update_value[0]["failure_count"] == 1, \
            f"Failure count should be incremented to 1, got {update_value[0]['failure_count']}"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


# Feature: medical-ai-platform, Property 33: Degraded keys trigger fallback
@given(
    provider=valid_provider(),
    feature=valid_feature(),
    num_active_keys=st.integers(min_value=1, max_value=3),
    num_degraded_keys=st.integers(min_value=1, max_value=3),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_degraded_keys_trigger_fallback(
    provider, feature, num_active_keys, num_degraded_keys, encryption_key
):
    """
    Property 33: For any request where the primary key is degraded,
    the system should attempt the next priority active key.
    
    Degraded keys should be skipped entirely and not used for requests.
    
    Validates: Requirements 11.4
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock API keys with mixed statuses
        all_keys = []
        
        # Add degraded keys with higher priorities (should be skipped)
        for i in range(num_degraded_keys):
            api_key_plaintext = f"degraded-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            all_keys.append({
                "id": f"degraded-key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": 100 + i,  # High priority but degraded
                "status": "degraded",
                "last_used_at": None
            })
        
        # Add active keys with lower priorities (should be used)
        active_keys = []
        for i in range(num_active_keys):
            api_key_plaintext = f"active-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            active_key = {
                "id": f"active-key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": 50 + i,  # Lower priority but active
                "status": "active",
                "last_used_at": None
            }
            all_keys.append(active_key)
            active_keys.append(active_key)
        
        # Sort active keys by priority descending
        active_keys_sorted = sorted(active_keys, key=lambda k: k["priority"], reverse=True)
        highest_priority_active = active_keys_sorted[0]
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain for get_active_key
        # Database query filters for status='active', so degraded keys are excluded
        mock_response = MagicMock()
        mock_response.data = [highest_priority_active]
        
        mock_limit = MagicMock()
        mock_limit.execute.return_value = mock_response
        
        mock_order = MagicMock()
        mock_order.limit.return_value = mock_limit
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        # Mock update for last_used_at
        mock_update_response = MagicMock()
        mock_update_response.execute.return_value = MagicMock()
        mock_update_eq = MagicMock()
        mock_update_eq.execute.return_value = mock_update_response
        mock_update = MagicMock()
        mock_update.eq.return_value = mock_update_eq
        mock_table.update.return_value = mock_update
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get active key
        result = await router.get_active_key(provider, feature)
        
        # Property: Should return an active key, not a degraded one
        assert result is not None, "Should return a key"
        assert result["status"] == "active", \
            f"Should return active key, got status '{result['status']}'"
        assert "degraded" not in result["id"], \
            f"Should not return degraded key, got key ID '{result['id']}'"
        assert "active" in result["id"], \
            f"Should return active key, got key ID '{result['id']}'"
        
        # Property: Should return the highest priority ACTIVE key (not degraded)
        assert result["priority"] == highest_priority_active["priority"], \
            f"Should return highest priority active key (priority {highest_priority_active['priority']}), " \
            f"got priority {result['priority']}"
        
        # Property: Degraded keys should be completely skipped
        # Even though degraded keys have higher priority (100+), they should not be returned
        assert result["priority"] < 100, \
            f"Should skip degraded keys with priority 100+, got priority {result['priority']}"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    num_active_keys=st.integers(min_value=2, max_value=4),
    num_degraded_keys=st.integers(min_value=1, max_value=3),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_get_all_active_keys_excludes_degraded(
    provider, feature, num_active_keys, num_degraded_keys, encryption_key
):
    """
    Property: For any provider and feature, get_all_active_keys should return
    only active keys and exclude degraded keys.
    
    Validates: Requirements 11.4
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create mock API keys with mixed statuses
        all_keys = []
        
        # Add degraded keys
        for i in range(num_degraded_keys):
            api_key_plaintext = f"degraded-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            all_keys.append({
                "id": f"degraded-key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": 100 + i,
                "status": "degraded",
                "last_used_at": None
            })
        
        # Add active keys
        active_keys = []
        for i in range(num_active_keys):
            api_key_plaintext = f"active-key-{i}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            active_key = {
                "id": f"active-key-{i}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": 50 + i,
                "status": "active",
                "last_used_at": None
            }
            all_keys.append(active_key)
            active_keys.append(active_key)
        
        # Sort active keys by priority descending (as database would)
        active_keys_sorted = sorted(active_keys, key=lambda k: k["priority"], reverse=True)
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Mock the query chain for get_all_active_keys
        # Database query filters for status='active', so degraded keys are excluded
        mock_response = MagicMock()
        mock_response.data = active_keys_sorted
        
        mock_order = MagicMock()
        mock_order.execute.return_value = mock_response
        
        mock_eq3 = MagicMock()
        mock_eq3.order.return_value = mock_order
        
        mock_eq2 = MagicMock()
        mock_eq2.eq.return_value = mock_eq3
        
        mock_eq1 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_eq1
        
        mock_table = MagicMock()
        mock_table.select.return_value = mock_select
        
        mock_supabase.table.return_value = mock_table
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Get all active keys
        result = await router.get_all_active_keys(provider, feature)
        
        # Property: Should return only active keys (no degraded keys)
        assert len(result) == num_active_keys, \
            f"Should return {num_active_keys} active keys, got {len(result)}"
        
        # Property: All returned keys should have status='active'
        for key in result:
            assert key["status"] == "active", \
                f"All returned keys should be active, found key with status '{key['status']}'"
            assert "degraded" not in key["id"], \
                f"Should not return degraded keys, found key ID '{key['id']}'"
        
        # Property: No degraded keys should be in the result
        degraded_key_ids = [f"degraded-key-{i}" for i in range(num_degraded_keys)]
        result_key_ids = [key["id"] for key in result]
        
        for degraded_id in degraded_key_ids:
            assert degraded_id not in result_key_ids, \
                f"Degraded key '{degraded_id}' should not be in results"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


# Feature: medical-ai-platform, Property 34: Feature failure isolation
@given(
    provider=valid_provider(),
    feature1=valid_feature(),
    feature2=valid_feature(),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_feature_failure_isolation(
    provider, feature1, feature2, encryption_key
):
    """
    Property 34: For any API key failure in one feature,
    other features using different keys should continue to function normally.
    
    Feature failure isolation ensures that a key failure for one feature
    (e.g., chat) does not affect other features (e.g., flashcard).
    
    Validates: Requirements 11.5
    """
    # Skip if both features are the same
    if feature1 == feature2:
        return
    
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create API keys for two different features
        key1_plaintext = "key-for-feature1"
        key1_encrypted = encrypt_key(key1_plaintext)
        
        key2_plaintext = "key-for-feature2"
        key2_encrypted = encrypt_key(key2_plaintext)
        
        # Key for feature1 (will be marked as degraded)
        key_feature1 = {
            "id": "key-feature1",
            "provider": provider,
            "feature": feature1,
            "key_value": key1_encrypted,
            "priority": 1,
            "status": "degraded",  # This feature's key is degraded
            "failure_count": 5
        }
        
        # Key for feature2 (remains active)
        key_feature2 = {
            "id": "key-feature2",
            "provider": provider,
            "feature": feature2,
            "key_value": key2_encrypted,
            "priority": 1,
            "status": "active",  # This feature's key is still active
            "failure_count": 0
        }
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Track which feature was queried
        queried_feature = [None]
        
        def mock_table_call(table_name):
            mock_table = MagicMock()
            
            def mock_select(fields):
                mock_select_obj = MagicMock()
                
                def mock_eq1(field, value):
                    if field == "provider":
                        mock_eq1_obj = MagicMock()
                        
                        def mock_eq2(field2, value2):
                            if field2 == "feature":
                                queried_feature[0] = value2
                                mock_eq2_obj = MagicMock()
                                
                                def mock_eq3(field3, value3):
                                    if field3 == "status" and value3 == "active":
                                        mock_eq3_obj = MagicMock()
                                        
                                        def mock_order(field4, desc=False):
                                            mock_order_obj = MagicMock()
                                            
                                            def mock_limit(n):
                                                mock_limit_obj = MagicMock()
                                                
                                                # Return appropriate key based on queried feature
                                                mock_response = MagicMock()
                                                if queried_feature[0] == feature1:
                                                    # Feature1 has degraded key, so no active keys
                                                    mock_response.data = []
                                                elif queried_feature[0] == feature2:
                                                    # Feature2 has active key
                                                    mock_response.data = [key_feature2]
                                                else:
                                                    mock_response.data = []
                                                
                                                mock_limit_obj.execute.return_value = mock_response
                                                return mock_limit_obj
                                            
                                            mock_order_obj.limit = mock_limit
                                            return mock_order_obj
                                        
                                        mock_eq3_obj.order = mock_order
                                        return mock_eq3_obj
                                    return MagicMock()
                                
                                mock_eq2_obj.eq = mock_eq3
                                return mock_eq2_obj
                            return MagicMock()
                        
                        mock_eq1_obj.eq = mock_eq2
                        return mock_eq1_obj
                    return MagicMock()
                
                mock_select_obj.eq = mock_eq1
                return mock_select_obj
            
            mock_table.select = mock_select
            
            # Mock update for last_used_at
            mock_update_response = MagicMock()
            mock_update_response.execute.return_value = MagicMock()
            mock_update_eq = MagicMock()
            mock_update_eq.execute.return_value = mock_update_response
            mock_update = MagicMock()
            mock_update.eq.return_value = mock_update_eq
            mock_table.update.return_value = mock_update
            
            return mock_table
        
        mock_supabase.table = mock_table_call
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Try to get key for feature1 (should fail - degraded)
        result_feature1 = await router.get_active_key(provider, feature1)
        
        # Try to get key for feature2 (should succeed - active)
        result_feature2 = await router.get_active_key(provider, feature2)
        
        # Property: Feature1 failure should not affect feature2
        assert result_feature1 is None, \
            f"Feature1 should have no active keys (degraded), got {result_feature1}"
        
        assert result_feature2 is not None, \
            f"Feature2 should have active key despite feature1 failure"
        
        assert result_feature2["feature"] == feature2, \
            f"Feature2 key should be for feature2, got {result_feature2['feature']}"
        
        assert result_feature2["status"] == "active", \
            f"Feature2 key should be active, got status '{result_feature2['status']}'"
        
        # Property: Keys are isolated by feature
        assert result_feature2["id"] == "key-feature2", \
            f"Should return feature2's key, got {result_feature2['id']}"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]


@given(
    provider=valid_provider(),
    features=st.lists(valid_feature(), min_size=2, max_size=4, unique=True),
    encryption_key=valid_encryption_key()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_health_status_tracked_per_feature(
    provider, features, encryption_key
):
    """
    Property: Health status should be tracked per feature-provider combination.
    
    Each feature should have independent health tracking, so failures in one
    feature don't affect the health status of keys in other features.
    
    Validates: Requirements 11.5
    """
    # Set encryption key for test
    original_env = os.environ.get("ENCRYPTION_KEY")
    os.environ["ENCRYPTION_KEY"] = encryption_key
    
    try:
        # Create API keys for different features with different health statuses
        keys_by_feature = {}
        
        for i, feature in enumerate(features):
            api_key_plaintext = f"key-{feature}"
            encrypted_key = encrypt_key(api_key_plaintext)
            
            # Alternate between active and degraded status
            status = "active" if i % 2 == 0 else "degraded"
            failure_count = 0 if status == "active" else 5
            
            key = {
                "id": f"key-{feature}",
                "provider": provider,
                "feature": feature,
                "key_value": encrypted_key,
                "priority": 1,
                "status": status,
                "failure_count": failure_count
            }
            
            keys_by_feature[feature] = key
        
        # Create mock Supabase client
        mock_supabase = MagicMock()
        
        # Track which feature was queried
        queried_feature = [None]
        
        def mock_table_call(table_name):
            mock_table = MagicMock()
            
            def mock_select(fields):
                mock_select_obj = MagicMock()
                
                def mock_eq1(field, value):
                    if field == "provider":
                        mock_eq1_obj = MagicMock()
                        
                        def mock_eq2(field2, value2):
                            if field2 == "feature":
                                queried_feature[0] = value2
                                mock_eq2_obj = MagicMock()
                                
                                def mock_eq3(field3, value3):
                                    if field3 == "status" and value3 == "active":
                                        mock_eq3_obj = MagicMock()
                                        
                                        def mock_order(field4, desc=False):
                                            mock_order_obj = MagicMock()
                                            
                                            def mock_limit(n):
                                                mock_limit_obj = MagicMock()
                                                
                                                # Return key for queried feature if it's active
                                                mock_response = MagicMock()
                                                feature_key = keys_by_feature.get(queried_feature[0])
                                                
                                                if feature_key and feature_key["status"] == "active":
                                                    mock_response.data = [feature_key]
                                                else:
                                                    mock_response.data = []
                                                
                                                mock_limit_obj.execute.return_value = mock_response
                                                return mock_limit_obj
                                            
                                            mock_order_obj.limit = mock_limit
                                            return mock_order_obj
                                        
                                        mock_eq3_obj.order = mock_order
                                        return mock_eq3_obj
                                    return MagicMock()
                                
                                mock_eq2_obj.eq = mock_eq3
                                return mock_eq2_obj
                            return MagicMock()
                        
                        mock_eq1_obj.eq = mock_eq2
                        return mock_eq1_obj
                    return MagicMock()
                
                mock_select_obj.eq = mock_eq1
                return mock_select_obj
            
            mock_table.select = mock_select
            
            # Mock update for last_used_at
            mock_update_response = MagicMock()
            mock_update_response.execute.return_value = MagicMock()
            mock_update_eq = MagicMock()
            mock_update_eq.execute.return_value = mock_update_response
            mock_update = MagicMock()
            mock_update.eq.return_value = mock_update_eq
            mock_table.update.return_value = mock_update
            
            return mock_table
        
        mock_supabase.table = mock_table_call
        
        # Create model router service with mock client
        router = ModelRouterService(supabase_client=mock_supabase)
        
        # Query keys for each feature
        results = {}
        for feature in features:
            result = await router.get_active_key(provider, feature)
            results[feature] = result
        
        # Property: Each feature should have independent health status
        for i, feature in enumerate(features):
            expected_status = "active" if i % 2 == 0 else "degraded"
            
            if expected_status == "active":
                assert results[feature] is not None, \
                    f"Feature '{feature}' should have active key"
                assert results[feature]["status"] == "active", \
                    f"Feature '{feature}' key should be active"
            else:
                assert results[feature] is None, \
                    f"Feature '{feature}' should have no active keys (degraded)"
        
        # Property: Active features should not be affected by degraded features
        active_features = [f for i, f in enumerate(features) if i % 2 == 0]
        degraded_features = [f for i, f in enumerate(features) if i % 2 != 0]
        
        for active_feature in active_features:
            assert results[active_feature] is not None, \
                f"Active feature '{active_feature}' should work despite degraded features {degraded_features}"
        
    finally:
        # Restore original environment variable
        if original_env is not None:
            os.environ["ENCRYPTION_KEY"] = original_env
        elif "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]
