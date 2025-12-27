"""
Unit tests for Command Handlers
Tests specific examples and edge cases for command execution
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.commands import CommandService, get_command_service
import uuid


@pytest.mark.asyncio
async def test_generate_flashcards_success():
    """Test successful flashcard generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Diabetes Mellitus"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Q: What is diabetes?\nA: A metabolic disorder...",
        "tokens_used": 150
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await command_service.generate_flashcards(user_id, topic)
    
    # Assert
    assert result["command"] == "flashcard"
    assert result["topic"] == topic
    assert "content" in result
    assert result["tokens_used"] == 150
    mock_router.select_provider.assert_called_once_with("flashcard")
    mock_router.execute_with_fallback.assert_called_once()


@pytest.mark.asyncio
async def test_generate_mcqs_success():
    """Test successful MCQ generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Cardiology"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Q1: What is the most common cause of heart failure?\nA) ...",
        "tokens_used": 200
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await command_service.generate_mcqs(user_id, topic)
    
    # Assert
    assert result["command"] == "mcq"
    assert result["topic"] == topic
    assert "content" in result
    assert result["tokens_used"] == 200
    mock_router.select_provider.assert_called_once_with("mcq")


@pytest.mark.asyncio
async def test_generate_summary_success():
    """Test successful high-yield summary generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Hypertension"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "# Hypertension - High-Yield Points\n- Definition: BP > 140/90...",
        "tokens_used": 120
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await command_service.generate_summary(user_id, topic)
    
    # Assert
    assert result["command"] == "highyield"
    assert result["topic"] == topic
    assert "content" in result
    assert result["tokens_used"] == 120
    mock_router.select_provider.assert_called_once_with("highyield")


@pytest.mark.asyncio
async def test_generate_explanation_success():
    """Test successful explanation generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Mitochondria"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Mitochondria are the powerhouse of the cell...",
        "tokens_used": 180
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await command_service.generate_explanation(user_id, topic)
    
    # Assert
    assert result["command"] == "explain"
    assert result["topic"] == topic
    assert "content" in result
    assert result["tokens_used"] == 180
    mock_router.select_provider.assert_called_once_with("explain")


@pytest.mark.asyncio
async def test_generate_concept_map_success():
    """Test successful concept map generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Cell Cycle"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Cell Cycle\n├── G1 Phase\n├── S Phase\n└── G2 Phase",
        "tokens_used": 100
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await command_service.generate_concept_map(user_id, topic)
    
    # Assert
    assert result["command"] == "map"
    assert result["topic"] == topic
    assert "content" in result
    assert result["tokens_used"] == 100
    mock_router.select_provider.assert_called_once_with("map")


@pytest.mark.asyncio
async def test_command_handler_uses_model_router():
    """Test that command handlers use model router for AI generation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Test Topic"
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": "Test content",
        "tokens_used": 50
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act - Test each command type
    commands_to_test = [
        ('generate_flashcards', 'flashcard'),
        ('generate_mcqs', 'mcq'),
        ('generate_summary', 'highyield'),
        ('generate_explanation', 'explain'),
        ('generate_concept_map', 'map')
    ]
    
    for handler_name, feature in commands_to_test:
        mock_router.select_provider.reset_mock()
        mock_router.execute_with_fallback.reset_mock()
        
        handler = getattr(command_service, handler_name)
        
        with patch('services.model_router.get_model_router_service', return_value=mock_router):
            result = await handler(user_id, topic)
        
        # Assert
        assert result is not None
        mock_router.select_provider.assert_called_once_with(feature)
        mock_router.execute_with_fallback.assert_called_once()


@pytest.mark.asyncio
async def test_command_handler_failure_raises_exception():
    """Test that command handler failures raise exceptions"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    topic = "Test Topic"
    
    # Mock model router with failure
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": False,
        "error": "API key exhausted"
    })
    
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act & Assert
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        with pytest.raises(Exception) as exc_info:
            await command_service.generate_flashcards(user_id, topic)
    
    assert "Failed to generate flashcards" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_command_with_unsupported_command():
    """Test that execute_command raises exception for unsupported commands"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    command_service = CommandService(supabase_client=mock_supabase)
    
    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await command_service.execute_command(user_id, "invalid_command", "topic")
    
    assert "Unsupported command" in str(exc_info.value)


def test_get_command_service_singleton():
    """Test that get_command_service returns singleton instance"""
    # Arrange
    mock_supabase = MagicMock()
    
    # Act
    service1 = get_command_service(mock_supabase)
    service2 = get_command_service(mock_supabase)
    
    # Assert
    assert service1 is service2
