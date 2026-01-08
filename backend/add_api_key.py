#!/usr/bin/env python3
"""
Script to add an API key for all features
Usage: python add_api_key.py <your_api_key>
"""
import sys
import os
from dotenv import load_dotenv
from services.encryption import encrypt_key

# Load environment variables
load_dotenv()

def generate_sql_for_api_key(api_key: str, provider: str = "openrouter"):
    """
    Generate SQL commands to insert an API key for all features
    
    Args:
        api_key: The plaintext API key
        provider: Provider name (default: openrouter)
    """
    # Encrypt the API key
    try:
        encrypted_key = encrypt_key(api_key)
    except Exception as e:
        print(f"Error encrypting API key: {e}")
        print("\nMake sure ENCRYPTION_KEY is set in your .env file")
        print("Generate one with: python -c 'import os, base64; print(base64.b64encode(os.urandom(32)).decode())'")
        sys.exit(1)
    
    # Define all features that need API keys
    features = [
        "chat",
        "flashcard",
        "mcq",
        "highyield",
        "explain",
        "map",
        "clinical",
        "osce",
        "safety",
        "image",
        "embedding"
    ]
    
    print("-- SQL Commands to Add API Key for All Features")
    print("-- Copy and paste these into your Supabase SQL editor\n")
    print("-- First, delete any existing keys for this provider to avoid duplicates")
    print(f"DELETE FROM api_keys WHERE provider = '{provider}';\n")
    
    print("-- Now insert the API key for all features")
    for i, feature in enumerate(features, start=1):
        priority = 100  # High priority
        status = "active"
        
        sql = f"""INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('{provider}', '{feature}', '{encrypted_key}', {priority}, '{status}', 0, NOW(), NOW());"""
        print(sql)
    
    print("\n-- Verify the keys were added:")
    print("SELECT provider, feature, priority, status, created_at FROM api_keys ORDER BY feature;")
    
    print("\n" + "="*80)
    print("IMPORTANT NOTES:")
    print("="*80)
    print("1. The DELETE command removes any existing keys to avoid duplicates")
    print("2. The API key has been encrypted using your ENCRYPTION_KEY")
    print("3. Copy ALL the SQL commands above and run them in Supabase SQL Editor")
    print("4. The same encrypted key is used for all features")
    print(f"5. Provider: {provider}")
    print("6. Priority: 100 (highest)")
    print("7. Status: active")
    print(f"\n{len(features)} features configured:")
    for feature in features:
        print(f"  ✓ {feature}")
    print("\nAfter running the SQL, restart your backend server.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_api_key.py <your_api_key> [provider]")
        print("\nExample:")
        print("  python add_api_key.py sk-or-v1-abc123xyz openrouter")
        print("\nProvider options: openrouter, gemini, openai")
        print("Default provider: openrouter")
        sys.exit(1)
    
    api_key = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else "openrouter"
    
    generate_sql_for_api_key(api_key, provider)
