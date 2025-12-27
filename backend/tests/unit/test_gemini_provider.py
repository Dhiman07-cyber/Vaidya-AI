"""
Unit tests for Gemini provider integration
Tests request formatting and error handling
Requirements: 21.6
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
import httpx

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.providers.gemini import GeminiProvider, get_gemini_provider


class TestGeminiProvider:
    """Test suite for Gemini provider"""
    
    def test_format_request_basic(self):
        """
        Test basic request formatting without system prompt
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        prompt = "What is the capital of France?"
        
        request = provider.format_request(prompt)
        
        # Check structure
        assert "contents" in request
        assert "generationConfig" in request
        assert "safetySettings" in request
        
        # Check contents
        assert len(request["contents"]) == 1
        assert request["contents"][0]["role"] == "user"
        assert request["contents"][0]["parts"][0]["text"] == prompt
        
        # Check generation config
        assert "temperature" in request["generationConfig"]
        assert "maxOutputTokens" in request["generationConfig"]
        
        # Check safety settings
        assert len(request["safetySettings"]) == 4
    
    def test_format_request_with_system_prompt(self):
        """
        Test request formatting with system prompt
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        prompt = "What is the capital of France?"
        system_prompt = "You are a helpful geography tutor."
        
        request = provider.format_request(prompt, system_prompt)
        
        # Check contents - should have 2 messages (system + user)
        assert len(request["contents"]) == 2
        
        # First message should contain system prompt
        assert request["contents"][0]["role"] == "user"
        assert "System:" in request["contents"][0]["parts"][0]["text"]
        assert system_prompt in request["contents"][0]["parts"][0]["text"]
        
        # Second message should be user prompt
        assert request["contents"][1]["role"] == "user"
        assert request["contents"][1]["parts"][0]["text"] == prompt
    
    @pytest.mark.asyncio
    async def test_call_gemini_success(self):
        """
        Test successful Gemini API call
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "The capital of France is Paris."}
                        ]
                    }
                }
            ],
            "usageMetadata": {
                "totalTokenCount": 25
            }
        }
        
        # Mock the HTTP client
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.call_gemini(
                api_key="test-api-key",
                prompt="What is the capital of France?"
            )
        
        # Check result
        assert result["success"] is True
        assert "Paris" in result["content"]
        assert result["tokens_used"] == 25
        assert "error" not in result
    
    @pytest.mark.asyncio
    async def test_call_gemini_http_error(self):
        """
        Test Gemini API call with HTTP error
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid API key"
        mock_response.json.return_value = {
            "error": {
                "message": "API key not valid"
            }
        }
        
        # Mock the HTTP client
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.call_gemini(
                api_key="invalid-key",
                prompt="Test prompt"
            )
        
        # Check result
        assert result["success"] is False
        assert "error" in result
        assert "400" in result["error"]
        assert result["tokens_used"] == 0
    
    @pytest.mark.asyncio
    async def test_call_gemini_timeout(self):
        """
        Test Gemini API call with timeout
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock timeout exception
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")
            
            result = await provider.call_gemini(
                api_key="test-key",
                prompt="Test prompt"
            )
        
        # Check result
        assert result["success"] is False
        assert "error" in result
        assert "timed out" in result["error"].lower()
        assert result["tokens_used"] == 0
    
    @pytest.mark.asyncio
    async def test_call_gemini_network_error(self):
        """
        Test Gemini API call with network error
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock network error
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError("Connection failed")
            
            result = await provider.call_gemini(
                api_key="test-key",
                prompt="Test prompt"
            )
        
        # Check result
        assert result["success"] is False
        assert "error" in result
        assert "network error" in result["error"].lower()
        assert result["tokens_used"] == 0
    
    @pytest.mark.asyncio
    async def test_call_gemini_no_candidates(self):
        """
        Test Gemini API call with no candidates in response
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock response with no candidates
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": []
        }
        
        # Mock the HTTP client
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.call_gemini(
                api_key="test-key",
                prompt="Test prompt"
            )
        
        # Check result
        assert result["success"] is False
        assert "error" in result
        assert "no response" in result["error"].lower()
        assert result["tokens_used"] == 0
    
    @pytest.mark.asyncio
    async def test_call_gemini_token_estimation(self):
        """
        Test token estimation when API doesn't provide token count
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock response without token count
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "This is a test response."}
                        ]
                    }
                }
            ]
            # No usageMetadata
        }
        
        # Mock the HTTP client
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.call_gemini(
                api_key="test-key",
                prompt="Test prompt"
            )
        
        # Check result
        assert result["success"] is True
        assert result["tokens_used"] > 0  # Should have estimated tokens
    
    def test_singleton_provider(self):
        """
        Test that get_gemini_provider returns singleton instance
        
        Requirements: 21.6
        """
        provider1 = get_gemini_provider()
        provider2 = get_gemini_provider()
        
        # Should be the same instance
        assert provider1 is provider2
    
    @pytest.mark.asyncio
    async def test_call_gemini_with_system_prompt(self):
        """
        Test Gemini API call with system prompt
        
        Requirements: 21.6
        """
        provider = GeminiProvider()
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "As a medical tutor, I can help with that."}
                        ]
                    }
                }
            ],
            "usageMetadata": {
                "totalTokenCount": 30
            }
        }
        
        # Mock the HTTP client
        with patch.object(provider.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await provider.call_gemini(
                api_key="test-api-key",
                prompt="Explain the heart",
                system_prompt="You are a medical education tutor."
            )
        
        # Check result
        assert result["success"] is True
        assert result["content"]
        assert result["tokens_used"] > 0
        
        # Verify system prompt was included in request
        call_args = mock_post.call_args
        request_json = call_args.kwargs["json"]
        assert len(request_json["contents"]) == 2  # System + user message
