-- Seed HuggingFace keys for all features
-- Phase 1: Database & HF Keys

-- Insert HuggingFace keys for all features in one go
DO $$
DECLARE
    hf_key TEXT := 'HF_INFERENCE_KEY';
    features TEXT[] := ARRAY[
        'chat', 
        'flashcard', 
        'mcq', 
        'highyield', 
        'explain', 
        'map', 
        'clinical', 
        'osce', 
        'image'
    ];
    feature TEXT;
BEGIN
    FOREACH feature IN ARRAY features
    LOOP
        -- Insert or update HF key for each feature
        INSERT INTO api_keys (
            provider,
            feature,
            key_value,
            priority,
            status,
            health_status,
            health_score,
            recent_attempts,
            recent_successes,
            recent_failures
        ) VALUES (
            'huggingface',
            feature,
            hf_key,  -- Will be encrypted by trigger if exists
            10,      -- Low priority (fallback)
            'active',
            'healthy',
            1.0,
            0,
            0,
            0
        )
        ON CONFLICT (provider, feature, key_value) 
        DO UPDATE SET
            status = 'active',
            priority = 10,
            health_status = 'healthy',
            health_score = 1.0,
            recent_attempts = 0,
            recent_successes = 0,
            recent_failures = 0;
        
        RAISE NOTICE 'Seeded HF key for feature: %', feature;
    END LOOP;
END $$;

-- Verify
SELECT provider, feature, priority, status, health_status
FROM api_keys
WHERE provider = 'huggingface'
ORDER BY feature;
