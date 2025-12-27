"""
Unit tests for background health check task

Requirements: 11.1
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.mark.asyncio
async def test_health_checks_run_on_schedule():
    """
    Test that health checks run on schedule
    
    Verifies that the periodic health check task executes health checks
    at regular intervals.
    
    Requirements: 11.1
    """
    # Import here to avoid circular dependencies
    import main
    
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock API keys data
    mock_keys_data = [
        {
            "id": "key-1",
            "provider": "gemini",
            "feature": "chat",
            "key_value": "encrypted_key_1",
            "status": "active"
        },
        {
            "id": "key-2",
            "provider": "openai",
            "feature": "flashcard",
            "key_value": "encrypted_key_2",
            "status": "active"
        }
    ]
    
    mock_result = Mock()
    mock_result.data = mock_keys_data
    
    # Set up mock chain for table query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Mock health monitor
    mock_health_monitor = Mock()
    mock_health_monitor.check_provider_health = AsyncMock(return_value={
        "status": "healthy",
        "response_time_ms": 100,
        "error_message": None,
        "quota_remaining": None
    })
    mock_health_monitor.log_health_check = AsyncMock(return_value={
        "api_key_id": "key-1",
        "status": "healthy"
    })
    
    # Mock encryption service
    mock_encryption = Mock()
    mock_encryption.decrypt_key = Mock(return_value="decrypted_key")
    
    # Patch dependencies
    with patch('main.create_client', return_value=mock_supabase), \
         patch('main.get_health_monitor', return_value=mock_health_monitor), \
         patch('main.get_encryption_service', return_value=mock_encryption), \
         patch.dict('os.environ', {
             'SUPABASE_URL': 'http://test.supabase.co',
             'SUPABASE_SERVICE_KEY': 'test-key'
         }):
        
        # Set flag to stop after one iteration
        main._health_check_running = True
        
        # Create task
        task = asyncio.create_task(main.periodic_health_check())
        
        # Wait a short time for one iteration
        await asyncio.sleep(0.5)
        
        # Stop the task
        main._health_check_running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify health checks were called
        assert mock_health_monitor.check_provider_health.call_count >= 2, \
            "Health check should be called for each active key"
        
        # Verify log_health_check was called
        assert mock_health_monitor.log_health_check.call_count >= 2, \
            "Health check results should be logged"


@pytest.mark.asyncio
async def test_all_active_keys_are_checked():
    """
    Test that all active keys are checked during health check
    
    Verifies that the background task checks all active API keys,
    not just a subset.
    
    Requirements: 11.1
    """
    # Import here to avoid circular dependencies
    import main
    
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock multiple active keys
    mock_keys_data = [
        {
            "id": f"key-{i}",
            "provider": "gemini",
            "feature": "chat",
            "key_value": f"encrypted_key_{i}",
            "status": "active"
        }
        for i in range(5)
    ]
    
    mock_result = Mock()
    mock_result.data = mock_keys_data
    
    # Set up mock chain for table query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Mock health monitor
    mock_health_monitor = Mock()
    mock_health_monitor.check_provider_health = AsyncMock(return_value={
        "status": "healthy",
        "response_time_ms": 100,
        "error_message": None,
        "quota_remaining": None
    })
    mock_health_monitor.log_health_check = AsyncMock(return_value={
        "api_key_id": "key-1",
        "status": "healthy"
    })
    
    # Mock encryption service
    mock_encryption = Mock()
    mock_encryption.decrypt_key = Mock(return_value="decrypted_key")
    
    # Patch dependencies
    with patch('main.create_client', return_value=mock_supabase), \
         patch('main.get_health_monitor', return_value=mock_health_monitor), \
         patch('main.get_encryption_service', return_value=mock_encryption), \
         patch.dict('os.environ', {
             'SUPABASE_URL': 'http://test.supabase.co',
             'SUPABASE_SERVICE_KEY': 'test-key'
         }):
        
        # Set flag to stop after one iteration
        main._health_check_running = True
        
        # Create task
        task = asyncio.create_task(main.periodic_health_check())
        
        # Wait a short time for one iteration
        await asyncio.sleep(0.5)
        
        # Stop the task
        main._health_check_running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify all 5 keys were checked
        assert mock_health_monitor.check_provider_health.call_count == 5, \
            f"All 5 active keys should be checked, but only {mock_health_monitor.check_provider_health.call_count} were checked"
        
        # Verify all checks were logged
        assert mock_health_monitor.log_health_check.call_count == 5, \
            f"All 5 health checks should be logged, but only {mock_health_monitor.log_health_check.call_count} were logged"


@pytest.mark.asyncio
async def test_health_check_handles_failures():
    """
    Test that health check task handles failures gracefully
    
    Verifies that when a health check fails, the failure is recorded
    and the task continues checking other keys.
    
    Requirements: 11.1, 11.2
    """
    # Import here to avoid circular dependencies
    import main
    
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock API keys data
    mock_keys_data = [
        {
            "id": "key-1",
            "provider": "gemini",
            "feature": "chat",
            "key_value": "encrypted_key_1",
            "status": "active"
        },
        {
            "id": "key-2",
            "provider": "openai",
            "feature": "flashcard",
            "key_value": "encrypted_key_2",
            "status": "active"
        }
    ]
    
    mock_result = Mock()
    mock_result.data = mock_keys_data
    
    # Set up mock chain for table query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Mock health monitor with one failure
    mock_health_monitor = Mock()
    
    # First call fails, second succeeds
    mock_health_monitor.check_provider_health = AsyncMock(side_effect=[
        {
            "status": "failed",
            "response_time_ms": 5000,
            "error_message": "Connection timeout",
            "quota_remaining": None
        },
        {
            "status": "healthy",
            "response_time_ms": 100,
            "error_message": None,
            "quota_remaining": None
        }
    ])
    
    mock_health_monitor.log_health_check = AsyncMock(return_value={
        "api_key_id": "key-1",
        "status": "failed"
    })
    
    mock_health_monitor.record_failure = AsyncMock(return_value={
        "key_id": "key-1",
        "failure_count": 1,
        "degraded": False
    })
    
    # Mock encryption service
    mock_encryption = Mock()
    mock_encryption.decrypt_key = Mock(return_value="decrypted_key")
    
    # Patch dependencies
    with patch('main.create_client', return_value=mock_supabase), \
         patch('main.get_health_monitor', return_value=mock_health_monitor), \
         patch('main.get_encryption_service', return_value=mock_encryption), \
         patch.dict('os.environ', {
             'SUPABASE_URL': 'http://test.supabase.co',
             'SUPABASE_SERVICE_KEY': 'test-key'
         }):
        
        # Set flag to stop after one iteration
        main._health_check_running = True
        
        # Create task
        task = asyncio.create_task(main.periodic_health_check())
        
        # Wait a short time for one iteration
        await asyncio.sleep(0.5)
        
        # Stop the task
        main._health_check_running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify both keys were checked
        assert mock_health_monitor.check_provider_health.call_count == 2, \
            "Both keys should be checked even if one fails"
        
        # Verify failure was recorded
        assert mock_health_monitor.record_failure.call_count == 1, \
            "Failed health check should be recorded"
        
        # Verify the failure was recorded for the correct key
        mock_health_monitor.record_failure.assert_called_with(
            key_id="key-1",
            error="Connection timeout",
            provider="gemini",
            feature="chat"
        )


@pytest.mark.asyncio
async def test_health_check_skips_non_active_keys():
    """
    Test that health check only checks active keys
    
    Verifies that degraded and disabled keys are not checked.
    
    Requirements: 11.1
    """
    # Import here to avoid circular dependencies
    import main
    
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock only active keys returned (degraded and disabled filtered by query)
    mock_keys_data = [
        {
            "id": "key-1",
            "provider": "gemini",
            "feature": "chat",
            "key_value": "encrypted_key_1",
            "status": "active"
        }
    ]
    
    mock_result = Mock()
    mock_result.data = mock_keys_data
    
    # Set up mock chain for table query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Mock health monitor
    mock_health_monitor = Mock()
    mock_health_monitor.check_provider_health = AsyncMock(return_value={
        "status": "healthy",
        "response_time_ms": 100,
        "error_message": None,
        "quota_remaining": None
    })
    mock_health_monitor.log_health_check = AsyncMock(return_value={
        "api_key_id": "key-1",
        "status": "healthy"
    })
    
    # Mock encryption service
    mock_encryption = Mock()
    mock_encryption.decrypt_key = Mock(return_value="decrypted_key")
    
    # Patch dependencies
    with patch('main.create_client', return_value=mock_supabase), \
         patch('main.get_health_monitor', return_value=mock_health_monitor), \
         patch('main.get_encryption_service', return_value=mock_encryption), \
         patch.dict('os.environ', {
             'SUPABASE_URL': 'http://test.supabase.co',
             'SUPABASE_SERVICE_KEY': 'test-key'
         }):
        
        # Set flag to stop after one iteration
        main._health_check_running = True
        
        # Create task
        task = asyncio.create_task(main.periodic_health_check())
        
        # Wait a short time for one iteration
        await asyncio.sleep(0.5)
        
        # Stop the task
        main._health_check_running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify query filtered for active keys only
        mock_supabase.table.assert_called_with("api_keys")
        mock_supabase.table.return_value.select.assert_called_with(
            "id, provider, feature, key_value, status"
        )
        mock_supabase.table.return_value.select.return_value.eq.assert_called_with(
            "status", "active"
        )
        
        # Verify only 1 key was checked (the active one)
        assert mock_health_monitor.check_provider_health.call_count == 1, \
            "Only active keys should be checked"


@pytest.mark.asyncio
async def test_startup_event_starts_health_check_task():
    """
    Test that startup event starts the health check background task
    
    Requirements: 11.1
    """
    # Import here to avoid circular dependencies
    import main
    
    # Reset global state
    main._health_check_task = None
    main._health_check_running = False
    
    # Mock the periodic_health_check function to avoid actual execution
    with patch('main.periodic_health_check', new_callable=AsyncMock) as mock_periodic:
        # Call startup event
        await main.startup_event()
        
        # Verify task was created
        assert main._health_check_task is not None, \
            "Health check task should be created on startup"
        
        # Clean up
        if main._health_check_task:
            main._health_check_running = False
            main._health_check_task.cancel()
            try:
                await main._health_check_task
            except asyncio.CancelledError:
                pass


@pytest.mark.asyncio
async def test_shutdown_event_stops_health_check_task():
    """
    Test that shutdown event stops the health check background task
    
    Requirements: 11.1
    """
    # Import here to avoid circular dependencies
    import main
    
    # Create a mock coroutine that raises CancelledError
    async def mock_cancelled_task():
        raise asyncio.CancelledError()
    
    # Create a real task that we can cancel
    mock_task = asyncio.create_task(mock_cancelled_task())
    
    main._health_check_task = mock_task
    main._health_check_running = True
    
    # Call shutdown event
    await main.shutdown_event()
    
    # Verify task was cancelled
    assert main._health_check_running is False, \
        "Health check running flag should be set to False"
    
    # Verify task is done (cancelled)
    assert mock_task.done(), \
        "Health check task should be done after shutdown"
