-- Migration: Add health tracking columns to api_keys table
-- Phase 1: Database & HF Keys

-- Add health tracking columns
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    recent_attempts INTEGER DEFAULT 0;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    recent_successes INTEGER DEFAULT 0;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    recent_failures INTEGER DEFAULT 0;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    last_success_time TIMESTAMPTZ;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    last_failure_time TIMESTAMPTZ;

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    health_status TEXT DEFAULT 'healthy' CHECK (health_status IN ('healthy', 'recovering', 'degraded'));

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS
    health_score FLOAT DEFAULT 1.0;

-- Create index for fast health queries
CREATE INDEX IF NOT EXISTS idx_api_keys_health 
ON api_keys(feature, status, health_status, priority DESC);

-- Create index for recovery checks
CREATE INDEX IF NOT EXISTS idx_api_keys_recovery
ON api_keys(health_status, last_failure_time)
WHERE health_status = 'degraded';

-- Update existing keys to have healthy status
UPDATE api_keys 
SET health_status = 'healthy', health_score = 1.0
WHERE health_status IS NULL;
