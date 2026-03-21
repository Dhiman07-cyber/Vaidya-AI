-- Remove all HuggingFace API keys from database
-- Use this to clean up before re-seeding or switching providers

-- Show current HuggingFace keys before deletion
SELECT 
    'BEFORE DELETION' as status,
    provider, 
    feature, 
    priority, 
    status, 
    health_status,
    created_at
FROM api_keys
WHERE provider = 'huggingface'
ORDER BY feature;

-- Delete all HuggingFace keys
DELETE FROM api_keys
WHERE provider = 'huggingface';

-- Show result
SELECT 
    'AFTER DELETION' as status,
    COUNT(*) as remaining_hf_keys
FROM api_keys
WHERE provider = 'huggingface';

-- Show all remaining keys by provider
SELECT 
    provider,
    COUNT(*) as key_count
FROM api_keys
GROUP BY provider
ORDER BY provider;
