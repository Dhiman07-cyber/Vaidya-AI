"""
Gemini Flash Provider Integration
Handles communication with Google's Gemini Flash API
Requirements: 21.6
"""
import httpx
import logging
from typing import Dict, Any, Optional, AsyncIterator
import json

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Provider integration for Google Gemini Flash
    
    Requirements:
    - 21.6: Support Gemini Flash as the primary free-tier provider
    """
    
    # Gemini API endpoint
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self):
        """Initialize the Gemini provider"""
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def format_request(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Format a request for the Gemini API
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            
        Returns:
            Dict containing formatted request payload for Gemini API
            
        Requirements: 21.6
        """
        # Gemini API format
        # https://ai.google.dev/api/rest/v1beta/models/generateContent
        
        contents = []
        
        # Add system prompt if provided (as a user message with context)
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
        
        # Add user prompt
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        request_payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        return request_payload
    
    async def call_gemini(
        self,
        api_key: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Call the Gemini API with a prompt
        
        Args:
            api_key: Gemini API key
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            stream: Whether to stream the response (not implemented yet)
            
        Returns:
            Dict containing:
                - success: bool indicating if call succeeded
                - content: Generated text content (if success)
                - error: Error message (if not success)
                - tokens_used: Approximate token count
                
        Raises:
            Exception: If API call fails
            
        Requirements: 21.6
        """
        try:
            # Format the request
            request_payload = self.format_request(prompt, system_prompt)
            
            # Build the API URL
            # Using gemini-1.5-flash model (free tier)
            model = "gemini-1.5-flash"
            url = f"{self.BASE_URL}/models/{model}:generateContent"
            
            # Add API key as query parameter
            params = {"key": api_key}
            
            # Make the API call
            logger.info(f"Calling Gemini API: {model}")
            
            response = await self.client.post(
                url,
                params=params,
                json=request_payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Gemini API error: {response.status_code} - {error_detail}")
                
                # Parse error message if possible
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", error_detail)
                except:
                    error_message = error_detail
                
                return {
                    "success": False,
                    "error": f"Gemini API error ({response.status_code}): {error_message}",
                    "tokens_used": 0
                }
            
            # Parse response
            response_data = response.json()
            
            # Extract generated content
            # Gemini response format: { "candidates": [{ "content": { "parts": [{ "text": "..." }] } }] }
            candidates = response_data.get("candidates", [])
            
            if not candidates:
                logger.warning("Gemini API returned no candidates")
                return {
                    "success": False,
                    "error": "No response generated by Gemini",
                    "tokens_used": 0
                }
            
            # Get the first candidate
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            if not parts:
                logger.warning("Gemini API returned no content parts")
                return {
                    "success": False,
                    "error": "No content in Gemini response",
                    "tokens_used": 0
                }
            
            # Extract text from parts
            generated_text = parts[0].get("text", "")
            
            # Get token usage if available
            usage_metadata = response_data.get("usageMetadata", {})
            tokens_used = usage_metadata.get("totalTokenCount", 0)
            
            # If no token count, estimate based on text length
            if tokens_used == 0:
                # Rough estimate: 1 token ≈ 4 characters
                tokens_used = len(prompt) // 4 + len(generated_text) // 4
            
            logger.info(f"Gemini API call successful. Tokens used: {tokens_used}")
            
            return {
                "success": True,
                "content": generated_text,
                "tokens_used": tokens_used
            }
            
        except httpx.TimeoutException:
            logger.error("Gemini API call timed out")
            return {
                "success": False,
                "error": "Request timed out",
                "tokens_used": 0
            }
        except httpx.RequestError as e:
            logger.error(f"Gemini API request error: {str(e)}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "tokens_used": 0
            }
    
    async def call_gemini_streaming(
        self,
        api_key: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Call the Gemini API with streaming response
        
        Args:
            api_key: Gemini API key
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            
        Yields:
            Text chunks as they arrive from the API
            
        Requirements: 21.6
        """
        try:
            # Format the request
            request_payload = self.format_request(prompt, system_prompt)
            
            # Build the API URL for streaming
            model = "gemini-1.5-flash"
            url = f"{self.BASE_URL}/models/{model}:streamGenerateContent"
            
            # Add API key as query parameter
            params = {"key": api_key, "alt": "sse"}
            
            # Make the streaming API call
            logger.info(f"Calling Gemini API (streaming): {model}")
            
            async with self.client.stream(
                "POST",
                url,
                params=params,
                json=request_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_detail = await response.aread()
                    logger.error(f"Gemini streaming API error: {response.status_code}")
                    yield f"Error: Gemini API returned status {response.status_code}"
                    return
                
                # Process streaming response
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # SSE format: "data: {...}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract text from the chunk
                            candidates = data.get("candidates", [])
                            if candidates:
                                candidate = candidates[0]
                                content = candidate.get("content", {})
                                parts = content.get("parts", [])
                                
                                if parts:
                                    text = parts[0].get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk: {data_str}")
                            continue
                
                logger.info("Gemini streaming API call completed")
                
        except httpx.TimeoutException:
            logger.error("Gemini streaming API call timed out")
            yield "Error: Request timed out"
        except httpx.RequestError as e:
            logger.error(f"Gemini streaming API request error: {str(e)}")
            yield f"Error: Network error - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in Gemini streaming: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_gemini_provider: Optional[GeminiProvider] = None


def get_gemini_provider() -> GeminiProvider:
    """
    Get or create the singleton Gemini provider instance
    
    Returns:
        GeminiProvider instance
    """
    global _gemini_provider
    
    if _gemini_provider is None:
        _gemini_provider = GeminiProvider()
    
    return _gemini_provider
