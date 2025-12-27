"""
Integration tests for slash command flow
Tests the complete flow from chat message to command execution

Requirements: 4.1, 4.2
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.chat import get_chat_service
from services.commands import get_command_service


@pytest.mark.asyncio
async def test_flashcard_command_returns_flashcards():
    """
    Test that sending /flashcard command returns flashcards
    
    Requirements: 4.1
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock session verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"id": "session-123"}]
    )
    
    # Mock message insertion (user message and assistant message)
    mock_message_response = Mock(data=[{
        "id": "msg-123",
        "session_id": "session-123",
        "role": "assistant",
        "content": "Q: What is diabetes?\nA: A metabolic disorder...",
        "tokens_used": 100,
        "created_at": "2024-01-01T00:00:00Z"
    }])
    
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = [
        Mock(data=[{"id": "user-msg-123"}]),  # User message
        mock_message_response  # Assistant message
    ]
    
    # Mock session update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
    
    # Mock model router - patch where it's imported in commands.py
    with patch('services.model_router.get_model_router_service') as mock_router_getter:
        mock_router = AsyncMock()
        mock_router.select_provider = AsyncMock(return_value="gemini")
        mock_router.execute_with_fallback = AsyncMock(return_value={
            "success": True,
            "content": "Q: What is diabetes?\nA: A metabolic disorder...",
            "tokens_used": 100
        })
        mock_router_getter.return_value = mock_router
        
        # Mock rate limiter - patch where it's imported in commands.py
        with patch('services.rate_limiter.get_rate_limiter') as mock_limiter_getter:
            mock_limiter = AsyncMock()
            mock_limiter.increment_usage = AsyncMock()
            mock_limiter_getter.return_value = mock_limiter
            
            # Create chat service and send flashcard command
            chat_service = get_chat_service(mock_supabase)
            result = await chat_service.send_message(
                user_id="user-123",
                session_id="session-123",
                message="/flashcard diabetes"
            )
            
            # Verify result contains flashcard content
            assert result is not None
            assert result["role"] == "assistant"
            assert "diabetes" in result["content"].lower()
            assert result["tokens_used"] == 100
            
            # Verify model router was called with correct parameters
            mock_router.select_provider.assert_called_once_with("flashcard")
            mock_router.execute_with_fallback.assert_called_once()
            
            # Verify rate limiter was called
            mock_limiter.increment_usage.assert_called_once_with(
                user_id="user-123",
                tokens=100,
                feature="flashcard"
            )


@pytest.mark.asyncio
async def test_mcq_command_returns_mcqs():
    """
    Test that sending /mcq command returns MCQs
    
    Requirements: 4.2
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock session verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"id": "session-123"}]
    )
    
    # Mock message insertion (user message and assistant message)
    mock_message_response = Mock(data=[{
        "id": "msg-123",
        "session_id": "session-123",
        "role": "assistant",
        "content": "Q1: What is the primary cause of Type 2 diabetes?\nA) Viral infection\nB) Insulin resistance\nC) Autoimmune destruction\nD) Genetic mutation\nCorrect Answer: B",
        "tokens_used": 150,
        "created_at": "2024-01-01T00:00:00Z"
    }])
    
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = [
        Mock(data=[{"id": "user-msg-123"}]),  # User message
        mock_message_response  # Assistant message
    ]
    
    # Mock session update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
    
    # Mock model router - patch where it's imported in commands.py
    with patch('services.model_router.get_model_router_service') as mock_router_getter:
        mock_router = AsyncMock()
        mock_router.select_provider = AsyncMock(return_value="gemini")
        mock_router.execute_with_fallback = AsyncMock(return_value={
            "success": True,
            "content": "Q1: What is the primary cause of Type 2 diabetes?\nA) Viral infection\nB) Insulin resistance\nC) Autoimmune destruction\nD) Genetic mutation\nCorrect Answer: B",
            "tokens_used": 150
        })
        mock_router_getter.return_value = mock_router
        
        # Mock rate limiter - patch where it's imported in commands.py
        with patch('services.rate_limiter.get_rate_limiter') as mock_limiter_getter:
            mock_limiter = AsyncMock()
            mock_limiter.increment_usage = AsyncMock()
            mock_limiter_getter.return_value = mock_limiter
            
            # Create chat service and send MCQ command
            chat_service = get_chat_service(mock_supabase)
            result = await chat_service.send_message(
                user_id="user-123",
                session_id="session-123",
                message="/mcq diabetes"
            )
            
            # Verify result contains MCQ content
            assert result is not None
            assert result["role"] == "assistant"
            assert "Q1:" in result["content"]
            assert "Correct Answer:" in result["content"]
            assert result["tokens_used"] == 150
            
            # Verify model router was called with correct parameters
            mock_router.select_provider.assert_called_once_with("mcq")
            mock_router.execute_with_fallback.assert_called_once()
            
            # Verify rate limiter was called
            mock_limiter.increment_usage.assert_called_once_with(
                user_id="user-123",
                tokens=150,
                feature="mcq"
            )


@pytest.mark.asyncio
async def test_regular_message_not_treated_as_command():
    """
    Test that regular messages (non-slash) are not treated as commands
    
    Requirements: 4.1
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock session verification
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"id": "session-123"}]
    )
    
    # Mock message insertion (user message and assistant message)
    mock_message_response = Mock(data=[{
        "id": "msg-123",
        "session_id": "session-123",
        "role": "assistant",
        "content": "I can help you with that...",
        "tokens_used": 50,
        "created_at": "2024-01-01T00:00:00Z"
    }])
    
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = [
        Mock(data=[{"id": "user-msg-123"}]),  # User message
        mock_message_response  # Assistant message
    ]
    
    # Mock session update
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
    
    # Mock model router for regular chat - patch where it's imported in chat.py
    with patch('services.model_router.get_model_router_service') as mock_router_getter:
        mock_router = AsyncMock()
        mock_router.select_provider = AsyncMock(return_value="gemini")
        mock_router.execute_with_fallback = AsyncMock(return_value={
            "success": True,
            "content": "I can help you with that...",
            "tokens_used": 50
        })
        mock_router_getter.return_value = mock_router
        
        # Mock rate limiter - patch where it's imported in chat.py
        with patch('services.rate_limiter.get_rate_limiter') as mock_limiter_getter:
            mock_limiter = AsyncMock()
            mock_limiter.increment_usage = AsyncMock()
            mock_limiter_getter.return_value = mock_limiter
            
            # Create chat service and send regular message
            chat_service = get_chat_service(mock_supabase)
            result = await chat_service.send_message(
                user_id="user-123",
                session_id="session-123",
                message="Tell me about diabetes"
            )
            
            # Verify result is from regular chat, not command
            assert result is not None
            assert result["role"] == "assistant"
            assert result["content"] == "I can help you with that..."
            
            # Verify model router was called with "chat" feature, not command feature
            mock_router.select_provider.assert_called_once_with("chat")
            
            # The key test: verify that command service was NOT used
            # (we can tell because the router was called with "chat" not a command feature)
            call_args = mock_router.execute_with_fallback.call_args
            assert call_args is not None
            assert call_args.kwargs["feature"] == "chat"
