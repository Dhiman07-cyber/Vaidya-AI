"""
Property-based tests for failover notifications

Requirements: 11.7, 18.2
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.model_router import ModelRouterService
from services.notifications import NotificationService


# Custom strategies for generating valid test data
@st.composite
def valid_provider(draw):
    """Generate valid provider names - only gemini is implemented"""
    return 'gemini'  # Only gemini is implemented currently


@st.composite
def valid_feature(draw):
    """Generate valid feature names"""
    return draw(st.sampled_from(['chat', 'flashcard', 'mcq', 'highyield', 'explain', 'map', 'image']))


@st.composite
def valid_prompt(draw):
    """Generate valid prompts"""
    return draw(st.text(min_size=5, max_size=100, alphabet=st.characters(
        min_codepoint=32, max_codepoint=126  # ASCII printable characters only
    )))


# Feature: medical-ai-platform, Property 36: Failover triggers admin notification
@given(
    provider=valid_provider(),
    feature=valid_feature(),
    prompt=valid_prompt()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_failover_triggers_notification(
    provider, feature, prompt
):
    """
    Property 36: When a primary key fails and fallback occurs, 
    an admin notification should be triggered.
    
    Validates: Requirements 11.7, 18.2
    """
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create model router with mock client
    router = ModelRouterService(supabase_client=mock_supabase)
    
    # Mock get_all_active_keys to return multiple keys
    # First key will fail, second key will succeed (triggering fallback)
    mock_keys = [
        {
            "id": "key-1-primary",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-1",
            "priority": 100,
            "status": "active"
        },
        {
            "id": "key-2-fallback",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-2",
            "priority": 50,
            "status": "active"
        }
    ]
    
    with patch.object(router, 'get_all_active_keys', new_callable=AsyncMock) as mock_get_keys, \
         patch.object(router, 'record_failure', new_callable=AsyncMock) as mock_record_failure, \
         patch('services.model_router.get_notification_service') as mock_get_notif_service:
        
        # Configure mock to return keys
        mock_get_keys.return_value = mock_keys
        
        # Mock notification service
        mock_notification_service = Mock(spec=NotificationService)
        mock_notification_service.notify_fallback = AsyncMock(return_value={
            "email_results": [{"success": True}],
            "webhook_result": {"success": True}
        })
        mock_get_notif_service.return_value = mock_notification_service
        
        # Mock provider call - first fails, second succeeds
        with patch('services.providers.gemini.get_gemini_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_provider.call_gemini = AsyncMock()
            
            # First call fails, second call succeeds
            mock_provider.call_gemini.side_effect = [
                {"success": False, "error": "API key invalid", "tokens_used": 0},
                {"success": True, "content": "Test response", "tokens_used": 10}
            ]
            
            mock_get_provider.return_value = mock_provider
            
            # Execute request with fallback
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt=prompt,
                max_retries=2
            )
            
            # Property: Request should succeed with fallback key
            assert result["success"] is True, "Request should succeed with fallback key"
            assert result["key_id"] == "key-2-fallback", "Should use fallback key"
            assert result["attempts"] == 2, "Should take 2 attempts (1 failure + 1 success)"
            
            # Property: Notification should be triggered for fallback
            assert mock_notification_service.notify_fallback.called, \
                "Fallback notification should be triggered"
            
            # Property: Notification should contain correct key IDs
            call_args = mock_notification_service.notify_fallback.call_args
            assert call_args is not None, "notify_fallback should be called"
            
            # Check the arguments passed to notify_fallback
            kwargs = call_args[1] if call_args[1] else {}
            assert kwargs.get("from_key_id") == "key-1-primary", \
                "Notification should contain original failed key ID"
            assert kwargs.get("to_key_id") == "key-2-fallback", \
                "Notification should contain fallback key ID"
            assert kwargs.get("provider") == provider, \
                "Notification should contain provider"
            assert kwargs.get("feature") == feature, \
                "Notification should contain feature"


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    prompt=valid_prompt()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_no_notification_on_first_key_success(
    provider, feature, prompt
):
    """
    Property: When the primary key succeeds on first attempt,
    no fallback notification should be triggered.
    
    Validates: Requirements 11.7, 18.2
    """
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create model router with mock client
    router = ModelRouterService(supabase_client=mock_supabase)
    
    # Mock get_all_active_keys to return multiple keys
    mock_keys = [
        {
            "id": "key-1-primary",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-1",
            "priority": 100,
            "status": "active"
        },
        {
            "id": "key-2-fallback",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-2",
            "priority": 50,
            "status": "active"
        }
    ]
    
    with patch.object(router, 'get_all_active_keys', new_callable=AsyncMock) as mock_get_keys, \
         patch.object(router, 'record_failure', new_callable=AsyncMock) as mock_record_failure, \
         patch('services.model_router.get_notification_service') as mock_get_notif_service:
        
        # Configure mock to return keys
        mock_get_keys.return_value = mock_keys
        
        # Mock notification service
        mock_notification_service = Mock(spec=NotificationService)
        mock_notification_service.notify_fallback = AsyncMock(return_value={
            "email_results": [{"success": True}],
            "webhook_result": {"success": True}
        })
        mock_get_notif_service.return_value = mock_notification_service
        
        # Mock provider call - succeeds on first attempt
        with patch('services.providers.gemini.get_gemini_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_provider.call_gemini = AsyncMock(return_value={
                "success": True,
                "content": "Test response",
                "tokens_used": 10
            })
            
            mock_get_provider.return_value = mock_provider
            
            # Execute request with fallback
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt=prompt,
                max_retries=2
            )
            
            # Property: Request should succeed with primary key
            assert result["success"] is True, "Request should succeed with primary key"
            assert result["key_id"] == "key-1-primary", "Should use primary key"
            assert result["attempts"] == 1, "Should take 1 attempt (immediate success)"
            
            # Property: No fallback notification should be triggered
            assert not mock_notification_service.notify_fallback.called, \
                "No fallback notification should be triggered when primary key succeeds"
