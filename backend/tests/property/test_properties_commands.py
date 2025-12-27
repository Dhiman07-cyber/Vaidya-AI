"""
Property-Based Tests for Command Service
Tests universal properties related to command parsing and routing
Feature: medical-ai-platform
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock, patch
from services.commands import CommandService
import uuid


# Custom strategies for generating test data
def valid_command():
    """Generate valid command names"""
    return st.sampled_from(['flashcard', 'mcq', 'highyield', 'explain', 'map'])


def valid_topic():
    """Generate valid topic strings"""
    return st.text(min_size=1, max_size=100).filter(
        lambda x: x.strip() and '\n' not in x and '\r' not in x and x == x.strip()
    )


def command_message(command, topic):
    """Generate a command message from command and topic"""
    return f"/{command} {topic}"


# Feature: medical-ai-platform, Property 10: Slash commands route to correct handlers
@given(
    command=valid_command(),
    topic=valid_topic()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_command_routing(command, topic):
    """
    Property 10: For any valid slash command (/flashcard, /mcq, /highyield, /explain, /map),
    the system should invoke the corresponding command handler.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    
    # Create command service
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Create command message
    message = command_message(command, topic)
    
    # Act: Parse the command
    parsed = command_service.parse_command(message)
    
    # Assert: Command was parsed correctly
    assert parsed is not None, f"Failed to parse command: {message}"
    assert parsed['command'] == command, f"Expected command '{command}', got '{parsed['command']}'"
    assert parsed['topic'] == topic, f"Expected topic '{topic}', got '{parsed['topic']}'"
    
    # Verify the correct handler would be called
    expected_handler = CommandService.SUPPORTED_COMMANDS[command]
    assert hasattr(command_service, expected_handler), f"Handler '{expected_handler}' not found"


@given(
    text=st.text(min_size=1, max_size=100).filter(lambda x: not x.strip().startswith('/'))
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_non_command_messages_return_none(text):
    """
    Property: For any message that doesn't start with '/', 
    parse_command should return None.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Arrange
    mock_supabase = MagicMock()
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    parsed = command_service.parse_command(text)
    
    # Assert
    assert parsed is None, f"Non-command message '{text}' should return None"


@given(
    invalid_command=st.text(min_size=1, max_size=20).filter(
        lambda x: x.lower() not in ['flashcard', 'mcq', 'highyield', 'explain', 'map']
    ),
    topic=valid_topic()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_invalid_commands_return_none(invalid_command, topic):
    """
    Property: For any invalid command (not in supported list),
    parse_command should return None.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Arrange
    mock_supabase = MagicMock()
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Create message with invalid command
    message = f"/{invalid_command} {topic}"
    
    # Act
    parsed = command_service.parse_command(message)
    
    # Assert
    assert parsed is None, f"Invalid command '{invalid_command}' should return None"


@given(
    command=valid_command()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_command_without_topic_returns_none(command):
    """
    Property: For any command without a topic,
    parse_command should return None.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Arrange
    mock_supabase = MagicMock()
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Create message with command but no topic
    message = f"/{command}"
    
    # Act
    parsed = command_service.parse_command(message)
    
    # Assert
    assert parsed is None, f"Command '{command}' without topic should return None"


@given(
    command=valid_command(),
    topic=valid_topic()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_command_execution_calls_correct_handler(command, topic):
    """
    Property: For any valid command and topic,
    execute_command should call the correct handler method.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Arrange
    mock_supabase = MagicMock()
    command_service = CommandService(supabase_client=mock_supabase)
    user_id = str(uuid.uuid4())
    
    # Mock the handler method
    handler_name = CommandService.SUPPORTED_COMMANDS[command]
    mock_handler = AsyncMock(return_value={
        "command": command,
        "topic": topic,
        "content": "Test content",
        "tokens_used": 100
    })
    setattr(command_service, handler_name, mock_handler)
    
    # Act
    result = await command_service.execute_command(user_id, command, topic)
    
    # Assert
    assert result is not None
    assert result["command"] == command
    assert result["topic"] == topic
    mock_handler.assert_called_once_with(user_id, topic)



# Feature: medical-ai-platform, Property 11: Command usage is tracked separately
@given(
    command=st.sampled_from(['flashcard', 'mcq']),  # Only test commands with usage tracking
    topic=valid_topic()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_command_usage_tracking(command, topic):
    """
    Property 11: For any command execution, the corresponding usage counter
    (mcqs_generated, flashcards_generated, etc.) should be incremented by the appropriate amount.
    
    Validates: Requirements 4.7
    """
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Test content",
        "tokens_used": 100
    })
    
    # Mock rate limiter
    mock_rate_limiter = MagicMock()
    mock_rate_limiter.increment_usage = AsyncMock()
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Get the handler
    handler_name = CommandService.SUPPORTED_COMMANDS[command]
    handler = getattr(command_service, handler_name)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        with patch('services.rate_limiter.get_rate_limiter', return_value=mock_rate_limiter):
            result = await handler(user_id, topic)
    
    # Assert: Usage was tracked with correct feature
    mock_rate_limiter.increment_usage.assert_called_once()
    call_args = mock_rate_limiter.increment_usage.call_args
    
    # Verify the call included user_id, tokens, and feature
    assert call_args.kwargs['user_id'] == user_id
    assert call_args.kwargs['tokens'] == 100
    assert call_args.kwargs['feature'] == command
