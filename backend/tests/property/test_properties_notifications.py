"""
Property-based tests for notification service

Requirements: 18.1, 18.2, 18.3, 18.4
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.notifications import NotificationService


# Custom strategies for generating valid test data
@st.composite
def valid_key_id(draw):
    """Generate valid key IDs"""
    return draw(st.text(min_size=10, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))


@st.composite
def valid_provider(draw):
    """Generate valid provider names"""
    return draw(st.sampled_from(['gemini', 'openai', 'ollama', 'anthropic']))


@st.composite
def valid_feature(draw):
    """Generate valid feature names"""
    return draw(st.sampled_from(['chat', 'flashcard', 'mcq', 'highyield', 'explain', 'map', 'image']))


@st.composite
def valid_error_message(draw):
    """Generate valid error messages"""
    return draw(st.text(min_size=10, max_size=200, alphabet=st.characters(
        min_codepoint=32, max_codepoint=126  # ASCII printable characters only
    )))


@st.composite
def valid_maintenance_level(draw):
    """Generate valid maintenance levels"""
    return draw(st.sampled_from(['soft', 'hard']))


@st.composite
def valid_admin_id(draw):
    """Generate valid admin IDs"""
    return draw(st.text(min_size=10, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))


# Feature: medical-ai-platform, Property 51: Critical events trigger notifications
@given(
    key_id=valid_key_id(),
    error=valid_error_message(),
    provider=valid_provider(),
    feature=valid_feature()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_api_key_failure_triggers_notification(
    key_id, error, provider, feature
):
    """
    Property 51: For any API key failure, a notification should be triggered.
    
    Validates: Requirements 18.1
    """
    # Create notification service
    notification_service = NotificationService()
    
    # Mock email and webhook sending
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_email, \
         patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks to return success
        mock_email.return_value = {"success": True, "message": "Email sent"}
        mock_webhook.return_value = {"success": True, "message": "Webhook sent"}
        
        # Enable notifications for test
        notification_service.email_enabled = True
        notification_service.admin_emails = ["admin@example.com"]
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Trigger notification
        result = await notification_service.notify_api_key_failure(
            key_id=key_id,
            error=error,
            provider=provider,
            feature=feature
        )
        
        # Property: Notification should be triggered
        assert result is not None, "Notification result should not be None"
        
        # Property: Email notification should be attempted
        assert "email_results" in result, "Result should contain email_results"
        assert len(result["email_results"]) > 0, "At least one email should be sent"
        
        # Property: Webhook notification should be attempted
        assert "webhook_result" in result, "Result should contain webhook_result"
        
        # Property: Email should be called with correct parameters
        assert mock_email.called, "Email should be sent"
        call_args = mock_email.call_args
        assert key_id in str(call_args), "Email should contain key_id"
        assert provider in str(call_args), "Email should contain provider"
        assert feature in str(call_args), "Email should contain feature"


@given(
    from_key_id=valid_key_id(),
    to_key_id=valid_key_id(),
    provider=valid_provider(),
    feature=valid_feature()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_fallback_triggers_notification(
    from_key_id, to_key_id, provider, feature
):
    """
    Property 51: For any fallback event, a notification should be triggered.
    
    Validates: Requirements 18.2
    """
    # Skip if keys are the same
    if from_key_id == to_key_id:
        return
    
    # Create notification service
    notification_service = NotificationService()
    
    # Mock email and webhook sending
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_email, \
         patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks to return success
        mock_email.return_value = {"success": True, "message": "Email sent"}
        mock_webhook.return_value = {"success": True, "message": "Webhook sent"}
        
        # Enable notifications for test
        notification_service.email_enabled = True
        notification_service.admin_emails = ["admin@example.com"]
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Trigger notification
        result = await notification_service.notify_fallback(
            from_key_id=from_key_id,
            to_key_id=to_key_id,
            provider=provider,
            feature=feature
        )
        
        # Property: Notification should be triggered
        assert result is not None, "Notification result should not be None"
        
        # Property: Email notification should be attempted
        assert "email_results" in result, "Result should contain email_results"
        assert len(result["email_results"]) > 0, "At least one email should be sent"
        
        # Property: Webhook notification should be attempted
        assert "webhook_result" in result, "Result should contain webhook_result"
        
        # Property: Email should be called with correct parameters
        assert mock_email.called, "Email should be sent"
        call_args = mock_email.call_args
        assert from_key_id in str(call_args), "Email should contain from_key_id"
        assert to_key_id in str(call_args), "Email should contain to_key_id"


@given(
    level=valid_maintenance_level(),
    reason=valid_error_message(),
    feature=st.one_of(st.none(), valid_feature())
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_maintenance_triggers_notification(
    level, reason, feature
):
    """
    Property 51: For any maintenance mode trigger, a notification should be sent.
    
    Validates: Requirements 18.3
    """
    # Create notification service
    notification_service = NotificationService()
    
    # Mock email and webhook sending
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_email, \
         patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks to return success
        mock_email.return_value = {"success": True, "message": "Email sent"}
        mock_webhook.return_value = {"success": True, "message": "Webhook sent"}
        
        # Enable notifications for test
        notification_service.email_enabled = True
        notification_service.admin_emails = ["admin@example.com"]
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Trigger notification
        result = await notification_service.notify_maintenance_triggered(
            level=level,
            reason=reason,
            feature=feature
        )
        
        # Property: Notification should be triggered
        assert result is not None, "Notification result should not be None"
        
        # Property: Email notification should be attempted
        assert "email_results" in result, "Result should contain email_results"
        assert len(result["email_results"]) > 0, "At least one email should be sent"
        
        # Property: Webhook notification should be attempted
        assert "webhook_result" in result, "Result should contain webhook_result"
        
        # Property: Email should be called with correct parameters
        assert mock_email.called, "Email should be sent"
        call_args = mock_email.call_args
        # Check the actual email body (third argument)
        email_body = call_args[0][2] if call_args[0] else ""
        assert level in email_body, "Email should contain maintenance level"
        assert reason in email_body, "Email should contain reason"


@given(
    admin_id=valid_admin_id(),
    action=st.text(min_size=5, max_size=100, alphabet=st.characters(
        min_codepoint=32, max_codepoint=126  # ASCII printable characters only
    ))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_admin_override_triggers_notification(
    admin_id, action
):
    """
    Property 51: For any admin override action, a notification should be sent.
    
    Validates: Requirements 18.4
    """
    # Create notification service
    notification_service = NotificationService()
    
    # Mock email and webhook sending
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_email, \
         patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks to return success
        mock_email.return_value = {"success": True, "message": "Email sent"}
        mock_webhook.return_value = {"success": True, "message": "Webhook sent"}
        
        # Enable notifications for test
        notification_service.email_enabled = True
        notification_service.admin_emails = ["admin@example.com"]
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Trigger notification
        result = await notification_service.notify_admin_override(
            admin_id=admin_id,
            action=action,
            details={"test": "data"}
        )
        
        # Property: Notification should be triggered
        assert result is not None, "Notification result should not be None"
        
        # Property: Email notification should be attempted
        assert "email_results" in result, "Result should contain email_results"
        assert len(result["email_results"]) > 0, "At least one email should be sent"
        
        # Property: Webhook notification should be attempted
        assert "webhook_result" in result, "Result should contain webhook_result"
        
        # Property: Email should be called with correct parameters
        assert mock_email.called, "Email should be sent"
        call_args = mock_email.call_args
        # Check the actual email body (third argument)
        email_body = call_args[0][2] if call_args[0] else ""
        assert admin_id in email_body, "Email should contain admin_id"
        assert action in email_body, "Email should contain action"


@given(
    num_admins=st.integers(min_value=1, max_value=5),
    key_id=valid_key_id(),
    error=valid_error_message(),
    provider=valid_provider(),
    feature=valid_feature()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_notifications_sent_to_all_admins(
    num_admins, key_id, error, provider, feature
):
    """
    Property: For any critical event, notifications should be sent to all configured admins.
    
    Validates: Requirements 18.1, 18.5
    """
    # Create notification service
    notification_service = NotificationService()
    
    # Configure multiple admin emails
    admin_emails = [f"admin{i}@example.com" for i in range(num_admins)]
    
    # Mock email and webhook sending
    with patch.object(notification_service, 'send_email', new_callable=AsyncMock) as mock_email, \
         patch.object(notification_service, 'send_webhook', new_callable=AsyncMock) as mock_webhook:
        
        # Configure mocks to return success
        mock_email.return_value = {"success": True, "message": "Email sent"}
        mock_webhook.return_value = {"success": True, "message": "Webhook sent"}
        
        # Enable notifications for test
        notification_service.email_enabled = True
        notification_service.admin_emails = admin_emails
        notification_service.webhook_enabled = True
        notification_service.webhook_url = "https://example.com/webhook"
        
        # Trigger notification
        result = await notification_service.notify_api_key_failure(
            key_id=key_id,
            error=error,
            provider=provider,
            feature=feature
        )
        
        # Property: Email should be sent to all admins
        assert len(result["email_results"]) == num_admins, \
            f"Should send email to all {num_admins} admins, sent to {len(result['email_results'])}"
        
        # Property: Email should be called once per admin
        assert mock_email.call_count == num_admins, \
            f"Email should be called {num_admins} times, called {mock_email.call_count} times"
        
        # Property: All admin emails should be in the results
        result_emails = [r["to"] for r in result["email_results"]]
        for admin_email in admin_emails:
            assert admin_email in result_emails, \
                f"Admin email {admin_email} should be in results"


@given(
    key_id=valid_key_id(),
    error=valid_error_message(),
    provider=valid_provider(),
    feature=valid_feature()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_notifications_gracefully_handle_disabled_config(
    key_id, error, provider, feature
):
    """
    Property: For any critical event, if notifications are not configured,
    the system should handle it gracefully without crashing.
    
    Validates: Requirements 18.1
    """
    # Create notification service with no configuration
    notification_service = NotificationService()
    notification_service.email_enabled = False
    notification_service.webhook_enabled = False
    
    # Trigger notification (should not crash)
    result = await notification_service.notify_api_key_failure(
        key_id=key_id,
        error=error,
        provider=provider,
        feature=feature
    )
    
    # Property: Should return a result (not crash)
    assert result is not None, "Should return result even when notifications disabled"
    
    # Property: Should indicate no notifications were sent
    assert "email_results" in result, "Result should contain email_results"
    assert "webhook_result" in result, "Result should contain webhook_result"
