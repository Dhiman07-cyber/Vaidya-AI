-- Cleanup and Add API Keys Script
-- This script will:
-- 1. Remove duplicate/old API keys
-- 2. Add your API key for ALL features

-- Step 1: Clean up existing keys for openrouter
-- (This prevents duplicates)
DELETE FROM api_keys WHERE provider = 'openrouter';

-- Step 2: Add your encrypted API key for all features
-- IMPORTANT: Replace 'YOUR_ENCRYPTED_KEY_HERE' with the output from add_api_key.py

-- Core features
INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'chat', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'flashcard', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'mcq', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'highyield', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'explain', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'map', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

-- Medical-specific features
INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'clinical', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'osce', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'safety', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

-- Advanced features (for future use)
INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'image', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

INSERT INTO api_keys (provider, feature, key_value, priority, status, failure_count, created_at, updated_at)
VALUES ('openrouter', 'embedding', 'YOUR_ENCRYPTED_KEY_HERE', 100, 'active', 0, NOW(), NOW());

-- Step 3: Verify all keys were added
SELECT 
    provider,
    feature,
    priority,
    status,
    created_at,
    SUBSTRING(key_value, 1, 20) || '...' as key_preview
FROM api_keys 
WHERE provider = 'openrouter'
ORDER BY feature;

-- Expected result: 11 rows (one for each feature)
SELECT COUNT(*) as total_keys FROM api_keys WHERE provider = 'openrouter';
