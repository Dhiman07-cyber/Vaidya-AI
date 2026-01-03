-- Migration: Create study tools tables (Version 2 - Corrected)
-- Description: Independent session and material storage for study tools
-- Date: 2026-01-03

-- Study tool sessions table
CREATE TABLE IF NOT EXISTS study_tool_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    feature VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Study tool materials table
CREATE TABLE IF NOT EXISTS study_tool_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES study_tool_sessions(id) ON DELETE CASCADE,
    feature VARCHAR(50) NOT NULL,
    topic TEXT NOT NULL,
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_study_tool_sessions_user_id ON study_tool_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_tool_sessions_feature ON study_tool_sessions(feature);
CREATE INDEX IF NOT EXISTS idx_study_tool_sessions_created_at ON study_tool_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_study_tool_materials_session_id ON study_tool_materials(session_id);
CREATE INDEX IF NOT EXISTS idx_study_tool_materials_feature ON study_tool_materials(feature);
CREATE INDEX IF NOT EXISTS idx_study_tool_materials_created_at ON study_tool_materials(created_at DESC);

-- Add RLS (Row Level Security) policies
ALTER TABLE study_tool_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_tool_materials ENABLE ROW LEVEL SECURITY;

-- Users can only see their own sessions
CREATE POLICY study_tool_sessions_select_policy ON study_tool_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only insert their own sessions
CREATE POLICY study_tool_sessions_insert_policy ON study_tool_sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can only update their own sessions
CREATE POLICY study_tool_sessions_update_policy ON study_tool_sessions
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can only delete their own sessions
CREATE POLICY study_tool_sessions_delete_policy ON study_tool_sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Users can only see materials from their own sessions
CREATE POLICY study_tool_materials_select_policy ON study_tool_materials
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM study_tool_sessions
            WHERE study_tool_sessions.id = study_tool_materials.session_id
            AND study_tool_sessions.user_id = auth.uid()
        )
    );

-- Users can only insert materials to their own sessions
CREATE POLICY study_tool_materials_insert_policy ON study_tool_materials
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM study_tool_sessions
            WHERE study_tool_sessions.id = study_tool_materials.session_id
            AND study_tool_sessions.user_id = auth.uid()
        )
    );

-- Users can only delete materials from their own sessions
CREATE POLICY study_tool_materials_delete_policy ON study_tool_materials
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM study_tool_sessions
            WHERE study_tool_sessions.id = study_tool_materials.session_id
            AND study_tool_sessions.user_id = auth.uid()
        )
    );

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_study_tool_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_study_tool_session_updated_at_trigger
    BEFORE UPDATE ON study_tool_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_study_tool_session_updated_at();
