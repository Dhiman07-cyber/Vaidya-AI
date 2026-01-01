"""
Model Configuration Manager
Simple model name mapping
"""
import json
from typing import Dict, Optional
from pathlib import Path

# Cache for loaded config
_config_cache: Optional[Dict] = None


def load_model_config() -> Dict:
    """
    Load model configuration from models.json
    
    Returns:
        Dictionary containing model mappings
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    # models.json is in backend root
    config_path = Path(__file__).parent.parent / "models.json"
    
    with open(config_path, 'r') as f:
        _config_cache = json.load(f)
    
    return _config_cache


def get_model_name(provider: str, feature: str = "chat") -> str:
    """
    Get the model name for a provider and feature
    
    Args:
        provider: Provider name (e.g., "gemini", "openai", "anthropic")
        feature: Feature type (e.g., "chat", "image", "video")
        
    Returns:
        Model name to use with the provider API
        
    Example:
        >>> get_model_name("gemini", "chat")
        "models/gemini-2.5-flash"
        
        >>> get_model_name("openai")
        "gpt-4o-mini"
    """
    config = load_model_config()
    
    provider_config = config.get(provider, {})
    
    if isinstance(provider_config, dict):
        return provider_config.get(feature, "")
    
    return ""


# Convenience functions for common use cases
def get_gemini_chat_model() -> str:
    """Get Gemini chat model name"""
    return get_model_name("gemini", "chat")


def get_gemini_image_model() -> str:
    """Get Gemini image model name"""
    return get_model_name("gemini", "image")


def get_gemini_video_model() -> str:
    """Get Gemini video model name"""
    return get_model_name("gemini", "video")


def get_openai_chat_model() -> str:
    """Get OpenAI chat model name"""
    return get_model_name("openai", "chat")


def get_anthropic_chat_model() -> str:
    """Get Anthropic chat model name"""
    return get_model_name("anthropic", "chat")


def get_ollama_chat_model() -> str:
    """Get Ollama chat model name"""
    return get_model_name("ollama", "chat")
