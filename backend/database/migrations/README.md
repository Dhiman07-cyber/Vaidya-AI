# Database Migrations

This directory contains SQL migration files for the VaidyaAI platform database.

## Running Migrations

### Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the migration file content
4. Run the SQL

### Using Supabase CLI

```bash
supabase db push
```

## Migration Files

### 004_study_tools_tables.sql

Creates independent tables for study tools:

- `study_tool_sessions` - Stores study tool sessions (flashcards, MCQs, etc.)
- `study_tool_materials` - Stores generated study materials

**Features:**
- Row Level Security (RLS) enabled
- Automatic timestamp updates
- Proper foreign key relationships
- Indexes for performance
- User isolation policies

**Tables Created:**

#### study_tool_sessions
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to auth.users)
- `tool_type` (VARCHAR) - flashcard, mcq, conceptmap, highyield, explain
- `title` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### study_tool_materials
- `id` (UUID, Primary Key)
- `session_id` (UUID, Foreign Key to study_tool_sessions)
- `topic` (TEXT)
- `content` (TEXT) - Generated AI content
- `created_at` (TIMESTAMP)

## Security

All tables have Row Level Security (RLS) enabled with policies that ensure:
- Users can only access their own sessions and materials
- Proper cascade deletion when sessions are removed
- Secure foreign key relationships

## Indexes

Performance indexes are created on:
- `user_id` for fast user lookups
- `tool_type` for filtering by tool
- `created_at` for chronological ordering
- `session_id` for material lookups
