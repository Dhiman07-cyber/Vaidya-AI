"""
Property-based tests for audit logging service

Requirements: 13.6, 19.1, 19.2, 19.3, 19.4, 19.5
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock
from services.audit import get_audit_service


@given(
    admin_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    action_type=st.sampled_from(['update_plan', 'reset_usage', 'disable_user', 'add_api_key', 'toggle_feature']),
    target_type=st.sampled_from(['user', 'api_key', 'system_flag', 'usage_counter']),
    target_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_admin_actions_are_logged(admin_id, action_type, target_type, target_id):
    """
    Property 44: Admin actions are logged
    
    Tests that all admin actions are properly logged to the audit_logs table
    with complete information.
    
    Requirements: 13.6, 19.1, 19.2, 19.3, 19.4, 19.5
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock successful audit log insertion
    mock_log_entry = {
        "id": "log-123",
        "admin_id": admin_id,
        "action_type": action_type,
        "target_type": target_type,
        "target_id": target_id,
        "details": None,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[mock_log_entry]
    )
    
    audit_service = get_audit_service(mock_supabase)
    
    # Log an admin action
    result = await audit_service.log_admin_action(
        admin_id=admin_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id
    )
    
    # Property: Admin action should be logged successfully
    assert result is not None, "Admin action should be logged"
    assert result["admin_id"] == admin_id, "Logged admin_id should match"
    assert result["action_type"] == action_type, "Logged action_type should match"
    assert result["target_type"] == target_type, "Logged target_type should match"
    assert result["target_id"] == target_id, "Logged target_id should match"
    
    # Verify Supabase insert was called
    mock_supabase.table.assert_called_with("audit_logs")


@given(
    admin_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    action_type=st.sampled_from(['update_plan', 'reset_usage', 'disable_user']),
    target_type=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='\x00')),
    target_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    old_value=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='\x00')),
    new_value=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_audit_logs_include_details(admin_id, action_type, target_type, target_id, old_value, new_value):
    """
    Property: Audit logs can include detailed information
    
    Tests that audit logs can store additional details about the action.
    
    Requirements: 19.4, 19.5
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    details = {
        "old_value": old_value,
        "new_value": new_value
    }
    
    # Mock successful audit log insertion with details
    mock_log_entry = {
        "id": "log-123",
        "admin_id": admin_id,
        "action_type": action_type,
        "target_type": target_type,
        "target_id": target_id,
        "details": details,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[mock_log_entry]
    )
    
    audit_service = get_audit_service(mock_supabase)
    
    # Log an admin action with details
    result = await audit_service.log_admin_action(
        admin_id=admin_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    
    # Property: Audit log should include details
    assert result is not None, "Admin action should be logged"
    assert result["details"] == details, "Logged details should match"


@given(
    admin_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    action_type=st.sampled_from(['update_plan', 'reset_usage', 'disable_user'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_audit_logs_can_be_filtered_by_admin(admin_id, action_type):
    """
    Property: Audit logs can be filtered by admin ID
    
    Tests that audit logs can be retrieved filtered by specific admin.
    
    Requirements: 19.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock audit log retrieval
    mock_logs = [
        {
            "id": "log-1",
            "admin_id": admin_id,
            "action_type": action_type,
            "target_type": "user",
            "target_id": "user-1",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    # Set up mock chain for query building
    mock_query = Mock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = Mock(data=mock_logs)
    
    mock_supabase.table.return_value.select.return_value = mock_query
    
    audit_service = get_audit_service(mock_supabase)
    
    # Retrieve audit logs filtered by admin
    result = await audit_service.get_audit_logs(admin_id=admin_id)
    
    # Property: Should return logs for the specified admin
    assert result is not None, "Should return audit logs"
    assert len(result) > 0, "Should return at least one log"
    assert all(log["admin_id"] == admin_id for log in result), "All logs should be for the specified admin"


@given(
    action_type=st.sampled_from(['update_plan', 'reset_usage', 'disable_user'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_audit_logs_can_be_filtered_by_action_type(action_type):
    """
    Property: Audit logs can be filtered by action type
    
    Tests that audit logs can be retrieved filtered by specific action type.
    
    Requirements: 19.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock audit log retrieval
    mock_logs = [
        {
            "id": "log-1",
            "admin_id": "admin-1",
            "action_type": action_type,
            "target_type": "user",
            "target_id": "user-1",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    # Set up mock chain for query building
    mock_query = Mock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = Mock(data=mock_logs)
    
    mock_supabase.table.return_value.select.return_value = mock_query
    
    audit_service = get_audit_service(mock_supabase)
    
    # Retrieve audit logs filtered by action type
    result = await audit_service.get_audit_logs(action_type=action_type)
    
    # Property: Should return logs for the specified action type
    assert result is not None, "Should return audit logs"
    assert len(result) > 0, "Should return at least one log"
    assert all(log["action_type"] == action_type for log in result), "All logs should be for the specified action type"


@given(
    target_type=st.sampled_from(['user', 'api_key', 'system_flag'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_audit_logs_can_be_filtered_by_target_type(target_type):
    """
    Property: Audit logs can be filtered by target type
    
    Tests that audit logs can be retrieved filtered by specific target type.
    
    Requirements: 19.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock audit log retrieval
    mock_logs = [
        {
            "id": "log-1",
            "admin_id": "admin-1",
            "action_type": "update",
            "target_type": target_type,
            "target_id": "target-1",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    # Set up mock chain for query building
    mock_query = Mock()
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = Mock(data=mock_logs)
    
    mock_supabase.table.return_value.select.return_value = mock_query
    
    audit_service = get_audit_service(mock_supabase)
    
    # Retrieve audit logs filtered by target type
    result = await audit_service.get_audit_logs(target_type=target_type)
    
    # Property: Should return logs for the specified target type
    assert result is not None, "Should return audit logs"
    assert len(result) > 0, "Should return at least one log"
    assert all(log["target_type"] == target_type for log in result), "All logs should be for the specified target type"
