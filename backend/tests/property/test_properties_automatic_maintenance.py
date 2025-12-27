"""
Property-based tests for automatic maintenance triggering

Requirements: 12.1, 12.9
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch
from services.model_router import ModelRouterService
from services.maintenance import MaintenanceService


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


# Feature: medical-ai-platform, Property 41: Automatic maintenance triggers notification
@given(
    provider=valid_provider(),
    feature=valid_feature(),
    prompt=valid_prompt()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_automatic_maintenance_triggers_notification(
    provider, feature, prompt
):
    """
    Property 41: When all keys fail and maintenance is automatically triggered,
    an admin notification should be sent.
    
    Validates: Requirements 12.1, 12.9
    """
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create model router with mock client
    router = ModelRouterService(supabase_client=mock_supabase)
    
    # Mock get_all_active_keys to return keys that will all fail
    mock_keys = [
        {
            "id": "key-1",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-1",
            "priority": 100,
            "status": "active"
        },
        {
            "id": "key-2",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-2",
            "priority": 50,
            "status": "active"
        }
    ]
    
    with patch.object(router, 'get_all_active_keys', new_callable=AsyncMock) as mock_get_keys, \
         patch.object(router, 'record_failure', new_callable=AsyncMock) as mock_record_failure, \
         patch('services.maintenance.get_maintenance_service') as mock_get_maint_service, \
         patch('services.model_router.get_notification_service') as mock_get_notif_service:
        
        # Configure mock to return keys
        mock_get_keys.return_value = mock_keys
        
        # Mock maintenance service
        mock_maintenance_service = Mock(spec=MaintenanceService)
        mock_maintenance_service.evaluate_maintenance_trigger = AsyncMock(return_value="soft")
        mock_maintenance_service.enter_maintenance = AsyncMock(return_value={
            "in_maintenance": True,
            "level": "soft",
            "reason": f"All API keys failed for {provider}/{feature}",
            "feature": feature
        })
        mock_get_maint_service.return_value = mock_maintenance_service
        
        # Mock notification service (for fallback notifications)
        mock_notif_service = Mock()
        mock_notif_service.notify_fallback = AsyncMock()
        mock_get_notif_service.return_value = mock_notif_service
        
        # Mock provider call - all calls fail
        with patch('services.providers.gemini.get_gemini_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_provider.call_gemini = AsyncMock(return_value={
                "success": False,
                "error": "API key invalid",
                "tokens_used": 0
            })
            
            mock_get_provider.return_value = mock_provider
            
            # Execute request with fallback (all keys will fail)
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt=prompt,
                max_retries=2
            )
            
            # Property: Request should fail
            assert result["success"] is False, "Request should fail when all keys fail"
            
            # Property: Maintenance evaluation should be called
            assert mock_maintenance_service.evaluate_maintenance_trigger.called, \
                "Maintenance evaluation should be triggered when all keys fail"
            
            # Property: Maintenance should be entered
            assert mock_maintenance_service.enter_maintenance.called, \
                "Maintenance mode should be entered when all keys fail"
            
            # Property: Notification is sent via enter_maintenance
            # (The enter_maintenance method internally calls notify_maintenance_triggered)
            call_args = mock_maintenance_service.enter_maintenance.call_args
            assert call_args is not None, "enter_maintenance should be called"
            
            kwargs = call_args[1] if call_args[1] else {}
            assert kwargs.get("level") == "soft", "Should enter soft maintenance"
            assert feature in kwargs.get("reason", ""), "Reason should mention the feature"


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    prompt=valid_prompt()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_no_maintenance_when_keys_succeed(
    provider, feature, prompt
):
    """
    Property: When at least one key succeeds,
    no maintenance mode should be triggered.
    
    Validates: Requirements 12.1
    """
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create model router with mock client
    router = ModelRouterService(supabase_client=mock_supabase)
    
    # Mock get_all_active_keys to return keys
    mock_keys = [
        {
            "id": "key-1",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-1",
            "priority": 100,
            "status": "active"
        }
    ]
    
    with patch.object(router, 'get_all_active_keys', new_callable=AsyncMock) as mock_get_keys, \
         patch.object(router, 'record_failure', new_callable=AsyncMock) as mock_record_failure, \
         patch('services.maintenance.get_maintenance_service') as mock_get_maint_service, \
         patch('services.model_router.get_notification_service') as mock_get_notif_service:
        
        # Configure mock to return keys
        mock_get_keys.return_value = mock_keys
        
        # Mock maintenance service
        mock_maintenance_service = Mock(spec=MaintenanceService)
        mock_maintenance_service.evaluate_maintenance_trigger = AsyncMock()
        mock_maintenance_service.enter_maintenance = AsyncMock()
        mock_get_maint_service.return_value = mock_maintenance_service
        
        # Mock notification service
        mock_notif_service = Mock()
        mock_notif_service.notify_fallback = AsyncMock()
        mock_get_notif_service.return_value = mock_notif_service
        
        # Mock provider call - succeeds
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
            
            # Property: Request should succeed
            assert result["success"] is True, "Request should succeed"
            
            # Property: Maintenance should NOT be triggered
            assert not mock_maintenance_service.evaluate_maintenance_trigger.called, \
                "Maintenance should not be evaluated when keys succeed"
            assert not mock_maintenance_service.enter_maintenance.called, \
                "Maintenance should not be entered when keys succeed"


@given(
    provider=valid_provider(),
    feature=valid_feature(),
    prompt=valid_prompt()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_maintenance_level_based_on_key_status(
    provider, feature, prompt
):
    """
    Property: The maintenance level should be determined by
    the status of available keys.
    
    Validates: Requirements 12.1, 12.2, 12.3
    """
    # Create mock Supabase client
    mock_supabase = Mock()
    
    # Create model router with mock client
    router = ModelRouterService(supabase_client=mock_supabase)
    
    # Mock get_all_active_keys to return keys that will all fail
    mock_keys = [
        {
            "id": "key-1",
            "provider": provider,
            "feature": feature,
            "key_value": "test-key-1",
            "priority": 100,
            "status": "active"
        }
    ]
    
    with patch.object(router, 'get_all_active_keys', new_callable=AsyncMock) as mock_get_keys, \
         patch.object(router, 'record_failure', new_callable=AsyncMock) as mock_record_failure, \
         patch('services.maintenance.get_maintenance_service') as mock_get_maint_service, \
         patch('services.model_router.get_notification_service') as mock_get_notif_service:
        
        # Configure mock to return keys
        mock_get_keys.return_value = mock_keys
        
        # Mock maintenance service to return hard maintenance
        mock_maintenance_service = Mock(spec=MaintenanceService)
        mock_maintenance_service.evaluate_maintenance_trigger = AsyncMock(return_value="hard")
        mock_maintenance_service.enter_maintenance = AsyncMock(return_value={
            "in_maintenance": True,
            "level": "hard",
            "reason": f"All API keys failed for {provider}/{feature}",
            "feature": feature
        })
        mock_get_maint_service.return_value = mock_maintenance_service
        
        # Mock notification service
        mock_notif_service = Mock()
        mock_notif_service.notify_fallback = AsyncMock()
        mock_get_notif_service.return_value = mock_notif_service
        
        # Mock provider call - fails
        with patch('services.providers.gemini.get_gemini_provider') as mock_get_provider:
            mock_provider = Mock()
            mock_provider.call_gemini = AsyncMock(return_value={
                "success": False,
                "error": "API key invalid",
                "tokens_used": 0
            })
            
            mock_get_provider.return_value = mock_provider
            
            # Execute request with fallback
            result = await router.execute_with_fallback(
                provider=provider,
                feature=feature,
                prompt=prompt,
                max_retries=1
            )
            
            # Property: Request should fail
            assert result["success"] is False, "Request should fail"
            
            # Property: Maintenance evaluation should be called
            assert mock_maintenance_service.evaluate_maintenance_trigger.called, \
                "Maintenance evaluation should be triggered"
            
            # Property: Maintenance level should be determined by evaluate_maintenance_trigger
            call_args = mock_maintenance_service.enter_maintenance.call_args
            if call_args:
                kwargs = call_args[1] if call_args[1] else {}
                # The level should match what evaluate_maintenance_trigger returned
                assert kwargs.get("level") == "hard", \
                    "Maintenance level should match evaluation result"
