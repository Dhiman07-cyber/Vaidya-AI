"""
Property-based tests for health monitor service

Requirements: 11.1, 11.2, 11.3, 11.6
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch
from services.health_monitor import HealthMonitorService, FAILURE_THRESHOLD
import services.health_monitor as health_monitor_module


@given(
    provider=st.sampled_from(['gemini', 'openai', 'ollama']),
    feature=st.sampled_from(['chat', 'flashcard', 'mcq', 'image']),
    key=st.text(min_size=20, max_size=100, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_health_checks_occur_periodically(provider, feature, key):
    """
    Property 30: Health checks occur periodically
    
    Tests that health checks can be performed for any provider/feature/key combination.
    
    Requirements: 11.1
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Reset singleton
    health_monitor_module._health_monitor_instance = None
    
    health_monitor = HealthMonitorService(mock_supabase)
    
    # Perform health check
    result = await health_monitor.check_provider_health(provider, key, feature)
    
    # Property: Health check should return a result
    assert result is not None, "Health check should return result"
    assert "status" in result, "Result should contain status"
    assert "response_time_ms" in result, "Result should contain response time"
    assert "error_message" in result, "Result should contain error message field"
    
    # Property: Status should be valid
    assert result["status"] in ["healthy", "failed", "degraded"], "Status should be valid"


@given(
    key_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    error=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters='\x00')),
    provider=st.sampled_from(['gemini', 'openai', 'ollama']),
    feature=st.sampled_from(['chat', 'flashcard', 'mcq']),
    initial_failures=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_failures_increment_failure_counter(
    key_id, error, provider, feature, initial_failures
):
    """
    Property 31: Failures increment failure counter
    
    Tests that recording a failure increments the failure counter by exactly 1.
    
    Requirements: 11.2
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Reset singleton
    health_monitor_module._health_monitor_instance = None
    
    # Create mock result with data attribute
    mock_select_result = Mock()
    mock_select_result.data = [{"failure_count": initial_failures}]
    
    mock_update_result = Mock()
    mock_update_result.data = [{"id": key_id, "failure_count": initial_failures + 1}]
    
    mock_insert_result = Mock()
    mock_insert_result.data = [{"api_key_id": key_id, "status": "failed"}]
    
    # Set up mock chain
    call_count = [0]
    def mock_table_call(table_name):
        mock_table = Mock()
        if table_name == "api_keys":
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: select
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_result
            else:
                # Second call: update
                mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        elif table_name == "provider_health":
            mock_table.insert.return_value.execute.return_value = mock_insert_result
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_call
    
    health_monitor = HealthMonitorService(mock_supabase)
    
    # Record failure
    result = await health_monitor.record_failure(key_id, error, provider, feature)
    
    # Property: Failure count should increment by exactly 1
    assert result is not None, "Record failure should return result"
    assert result["failure_count"] == initial_failures + 1, \
        f"Failure count should increment from {initial_failures} to {initial_failures + 1}"
    assert result["key_id"] == key_id, "Key ID should match"


@given(
    key_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    error=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters='\x00')),
    provider=st.sampled_from(['gemini', 'openai', 'ollama']),
    feature=st.sampled_from(['chat', 'flashcard', 'mcq']),
    initial_failures=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_repeated_failures_mark_key_as_degraded(
    key_id, error, provider, feature, initial_failures
):
    """
    Property 32: Repeated failures mark key as degraded
    
    Tests that when failure count reaches threshold, key is marked as degraded.
    
    Requirements: 11.3
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Reset singleton
    health_monitor_module._health_monitor_instance = None
    
    # Create mock result with data attribute
    mock_select_result = Mock()
    mock_select_result.data = [{"failure_count": initial_failures}]
    
    new_failure_count = initial_failures + 1
    
    mock_update_result = Mock()
    mock_update_result.data = [{"id": key_id, "failure_count": new_failure_count, "status": "degraded"}]
    
    mock_insert_result = Mock()
    mock_insert_result.data = [{"api_key_id": key_id, "status": "failed"}]
    
    # Set up mock chain
    call_count = [0]
    def mock_table_call(table_name):
        mock_table = Mock()
        if table_name == "api_keys":
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: select
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_select_result
            else:
                # Second or third call: update
                mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_result
        elif table_name == "provider_health":
            mock_table.insert.return_value.execute.return_value = mock_insert_result
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_call
    
    health_monitor = HealthMonitorService(mock_supabase)
    
    # Record failure
    result = await health_monitor.record_failure(key_id, error, provider, feature)
    
    # Property: Key should be marked as degraded when threshold is reached
    if new_failure_count >= FAILURE_THRESHOLD:
        assert result["degraded"] is True, \
            f"Key should be marked as degraded when failures ({new_failure_count}) >= threshold ({FAILURE_THRESHOLD})"
    else:
        assert result["degraded"] is False, \
            f"Key should not be degraded when failures ({new_failure_count}) < threshold ({FAILURE_THRESHOLD})"


@given(
    key_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    status=st.sampled_from(['healthy', 'degraded', 'failed']),
    response_time_ms=st.integers(min_value=10, max_value=5000),
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters='\x00')))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_health_checks_are_logged(
    key_id, status, response_time_ms, error_message
):
    """
    Property 35: Health checks are logged
    
    Tests that all health checks are logged to the provider_health table.
    
    Requirements: 11.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Reset singleton
    health_monitor_module._health_monitor_instance = None
    
    # Mock inserting health record
    health_record = {
        "api_key_id": key_id,
        "status": status,
        "response_time_ms": response_time_ms,
        "error_message": error_message
    }
    
    mock_insert_result = Mock()
    mock_insert_result.data = [health_record]
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result
    
    health_monitor = HealthMonitorService(mock_supabase)
    
    # Log health check
    result = await health_monitor.log_health_check(
        key_id=key_id,
        status=status,
        response_time_ms=response_time_ms,
        error_message=error_message
    )
    
    # Property: Health check should be logged
    assert result is not None, "Log health check should return result"
    assert result["api_key_id"] == key_id, "Logged key ID should match"
    assert result["status"] == status, "Logged status should match"
    assert result["response_time_ms"] == response_time_ms, "Logged response time should match"
    
    # Property: Supabase insert should be called
    mock_supabase.table.assert_called_with("provider_health")
