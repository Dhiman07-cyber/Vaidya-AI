"""
Hugging Face Provider
Uses Hugging Face Inference API for medical-specific open-source models
No model downloads required - all inference happens via API
Requirements: Medical model fallback, cost optimization
"""
import os
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging
import json

load_dotenv()
logger = logging.getLogger(__name__)


class HuggingFaceProvider:
    """Provider for Hugging Face Inference API"""
    
    # Medical-specific models available on Hugging Face Router
    # Using router.huggingface.co/v1 with inference provider suffixes
    MEDICAL_MODELS = {
        # Medical reasoning - Med42-70B via Featherless AI provider
        "chat": "m42-health/Llama3-Med42-70B:featherless-ai",
        "clinical": "m42-health/Llama3-Med42-70B:featherless-ai",
        "osce": "m42-health/Llama3-Med42-70B:featherless-ai",
        "explain": "m42-health/Llama3-Med42-70B:featherless-ai",
        "highyield": "m42-health/Llama3-Med42-70B:featherless-ai",

        # Content generation - Using Llama-3.1
        "flashcard": "meta-llama/Llama-3.1-8B-Instruct",
        "mcq": "meta-llama/Llama-3.1-8B-Instruct",
        "map": "meta-llama/Llama-3.1-8B-Instruct",
        
        # Specialized medical models
        "safety": "m42-health/Llama3-Med42-70B:featherless-ai",
        "image": "microsoft/llava-med-v1.5-mistral-7b",
        
        # Embeddings
        "embedding": "BAAI/bge-small-en-v1.5",
    }
    
    def __init__(self):
        """Initialize Hugging Face provider"""
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        # Router endpoint (OpenAI-compatible) - old inference endpoint is deprecated
        self.router_url = "https://router.huggingface.co/v1"
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set - Hugging Face provider will not work")
    
    async def call_huggingface(
        self,
        feature: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Call Hugging Face Router API (OpenAI-compatible format)
        
        Args:
            feature: Feature name (chat, flashcard, etc.)
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with success, content, error, tokens_used
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Hugging Face API key not configured",
                "content": "",
                "tokens_used": 0
            }
        
        model = self.MEDICAL_MODELS.get(feature, self.MEDICAL_MODELS["chat"])
        logger.info(f"Calling Hugging Face model: {model} for feature: {feature}")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            url = f"{self.router_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        generated_text = result["choices"][0]["message"]["content"]
                        tokens_used = result.get("usage", {}).get("total_tokens", 0)
                        if tokens_used == 0:
                            tokens_used = len(prompt + generated_text) // 4
                    else:
                        generated_text = str(result)
                        tokens_used = len(prompt + generated_text) // 4
                    
                    logger.info(f"Hugging Face call succeeded. Model: {model}, Tokens: ~{tokens_used}")
                    
                    return {
                        "success": True,
                        "content": generated_text.strip(),
                        "error": None,
                        "tokens_used": tokens_used,
                        "model": model,
                        "provider": "huggingface"
                    }
                else:
                    error_msg = f"Hugging Face API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "content": "",
                        "tokens_used": 0,
                        "model": model,
                        "provider": "huggingface"
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Hugging Face API timeout",
                "content": "",
                "tokens_used": 0,
                "model": model,
                "provider": "huggingface"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Hugging Face API error: {str(e)}",
                "content": "",
                "tokens_used": 0,
                "model": model,
                "provider": "huggingface"
            }
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embeddings using Hugging Face model
        
        Args:
            text: Text to embed
            
        Returns:
            Dict with success, embedding, error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Hugging Face API key not configured",
                "embedding": None
            }
        
        model = self.MEDICAL_MODELS["embedding"]
        
        try:
            url = f"{self.router_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "input": text
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("data", [{}])[0].get("embedding")
                    
                    return {
                        "success": True,
                        "embedding": embedding,
                        "error": None,
                        "model": model
                    }
                else:
                    error_msg = f"Embedding API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "embedding": None
                    }
                    
        except Exception as e:
            error_msg = f"Embedding API error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "embedding": None
            }
    async def health_check(self, feature: str = "chat") -> Dict[str, Any]:
        """
        Perform a health check on Hugging Face models
        
        Args:
            feature: Feature to test (default: chat)
            
        Returns:
            Dict with success, model, response_time_ms, error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Hugging Face API key not configured",
                "model": None,
                "response_time_ms": 0
            }
        
        model = self.MEDICAL_MODELS.get(feature, self.MEDICAL_MODELS["chat"])
        
        logger.info(f"Performing health check on Hugging Face model: {model}")
        
        import time
        start_time = time.time()
        
        try:
            url = f"{self.router_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "What is diabetes?"}],
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    logger.info(f"Hugging Face health check passed for {model} ({response_time}ms)")
                    return {
                        "success": True,
                        "model": model,
                        "response_time_ms": response_time,
                        "error": None
                    }
                elif response.status_code == 503:
                    logger.warning(f"Hugging Face model {model} is loading (cold start)")
                    return {
                        "success": False,
                        "model": model,
                        "response_time_ms": response_time,
                        "error": "Model loading (cold start)",
                        "is_loading": True
                    }
                else:
                    error_msg = f"Health check failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "model": model,
                        "response_time_ms": response_time,
                        "error": error_msg
                    }
                    
        except httpx.TimeoutException:
            response_time = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "model": model,
                "response_time_ms": response_time,
                "error": "Health check timeout"
            }
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "model": model,
                "response_time_ms": response_time,
                "error": f"Health check error: {str(e)}"
            }


# Singleton instance
_huggingface_provider: Optional[HuggingFaceProvider] = None


def get_huggingface_provider() -> HuggingFaceProvider:
    """Get or create singleton Hugging Face provider instance"""
    global _huggingface_provider
    
    if _huggingface_provider is None:
        _huggingface_provider = HuggingFaceProvider()
    
    return _huggingface_provider
