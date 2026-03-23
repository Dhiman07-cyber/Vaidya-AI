"""
Voyage AI Provider
High-quality embeddings with generous free tier
Free tier: 10M tokens/month, 3 RPM, 10k TPM
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class VoyageProvider:
    """Provider for Voyage AI Embeddings API"""
    
    MODELS = {
        "embedding": "voyage-large-2",  # 1536 dimensions, best quality
        "embedding_lite": "voyage-2",    # 1024 dimensions, faster
    }
    
    def __init__(self):
        """Initialize Voyage provider"""
        self.api_url = "https://api.voyageai.com/v1/embeddings"
        logger.info("Voyage AI provider initialized")
    
    async def generate_embedding(
        self, 
        text: str, 
        api_key: Optional[str] = None,
        model: str = "voyage-large-2"
    ) -> Dict[str, Any]:
        """
        Generate embeddings using Voyage AI API
        
        Args:
            text: Text to embed
            api_key: Optional Voyage API key (falls back to env if not provided)
            model: Model to use (voyage-large-2 or voyage-2)
            
        Returns:
            Dict with success, embedding, error, model, dimension
        """
        # Use provided key or fall back to environment variable
        if not api_key:
            api_key = os.getenv("VOYAGE_API_KEY")
        
        if not api_key:
            return {
                "success": False,
                "error": "Voyage API key not configured",
                "embedding": None,
                "dimension": 0
            }
        
        try:
            import httpx
            
            logger.info(f"Generating embedding with Voyage model: {model}")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "input": text,
                "model": model
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code == 429:
                    logger.warning("Voyage API rate limit exceeded")
                    return {
                        "success": False,
                        "error": "Rate limit exceeded. Voyage allows 3 requests/minute.",
                        "embedding": None,
                        "dimension": 0
                    }
                
                if response.status_code == 401:
                    logger.error("Voyage API key invalid")
                    return {
                        "success": False,
                        "error": "Invalid Voyage API key",
                        "embedding": None,
                        "dimension": 0
                    }
                
                if response.status_code != 200:
                    error_msg = f"API error: {response.status_code} - {response.text[:200]}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "embedding": None,
                        "dimension": 0
                    }
                
                result = response.json()
                
                # Voyage returns embeddings in OpenAI-compatible format
                if "data" in result and len(result["data"]) > 0:
                    embedding = result["data"][0]["embedding"]
                    dimension = len(embedding)
                    
                    logger.info(f"Voyage embedding generated successfully, dimension: {dimension}")
                    
                    return {
                        "success": True,
                        "embedding": embedding,
                        "error": None,
                        "model": model,
                        "dimension": dimension
                    }
                else:
                    return {
                        "success": False,
                        "error": "Invalid response format from Voyage API",
                        "embedding": None,
                        "dimension": 0
                    }
                    
        except Exception as e:
            error_msg = f"Voyage API error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "embedding": None,
                "dimension": 0
            }


# Singleton instance
_voyage_provider: Optional[VoyageProvider] = None


def get_voyage_provider() -> VoyageProvider:
    """Get or create singleton Voyage provider instance"""
    global _voyage_provider
    
    if _voyage_provider is None:
        _voyage_provider = VoyageProvider()
    
    return _voyage_provider
