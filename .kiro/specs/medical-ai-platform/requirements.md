# Requirements Document

## Introduction

This document specifies the requirements for a production-grade AI medical education platform designed for medical students. The platform provides AI-powered tutoring, study tools, clinical reasoning simulation, and administrative controls, built with a scarcity-first engineering approach that assumes API limitations, quota exhaustion, and zero initial budget.

## Glossary

- **System**: The complete medical AI platform including frontend, backend, database, and admin components
- **User**: A medical student using the platform
- **Admin**: A platform administrator with elevated privileges
- **Super_Admin**: The highest privilege administrator with emergency access
- **API_Key_Pool**: Collection of manually-entered API keys for AI providers
- **Provider**: External AI service (e.g., Gemini Flash, open-source LLMs)
- **Maintenance_Mode**: System state when critical services are unavailable
- **Feature**: Specific capability (chat, flashcards, MCQs, etc.)
- **Plan**: User subscription tier (free, student, pro, admin)
- **Token**: Unit of AI model usage measurement
- **RLS**: Row Level Security in Supabase
- **RAG**: Retrieval Augmented Generation
- **OSCE**: Objective Structured Clinical Examination

## Requirements

### Requirement 1: User Authentication and Authorization

**User Story:** As a user, I want to securely authenticate and access features appropriate to my subscription plan, so that my account and usage are properly tracked.

#### Acceptance Criteria

1. THE System SHALL use Supabase Auth for user authentication
2. WHEN a user registers, THE System SHALL assign them the "free" plan by default
3. WHEN a user authenticates, THE System SHALL retrieve their plan and role from the database
4. THE System SHALL enforce plan-based feature access at the backend level
5. THE System SHALL never store authentication logic in the frontend

### Requirement 2: Admin Access Control

**User Story:** As a super admin, I want multiple fail-safe mechanisms to ensure admin access is never lost, so that the platform remains manageable under all conditions.

#### Acceptance Criteria

1. THE System SHALL maintain an admin_allowlist table with email addresses and roles
2. THE System SHALL check admin access by verifying email is in the allowlist AND role permits access
3. THE System SHALL support roles: super_admin, admin, ops, support, viewer
4. THE System SHALL read a SUPER_ADMIN_EMAIL from environment variables as a fail-safe
5. WHEN all database admin checks fail, THE System SHALL grant super_admin access if email matches SUPER_ADMIN_EMAIL
6. THE System SHALL provide an emergency admin token mechanism for recovery scenarios
7. THE System SHALL restrict admin panel routes to authenticated admin users only

### Requirement 3: AI Chat Interface

**User Story:** As a medical student, I want to chat with an AI tutor about medical topics, so that I can learn interactively and get immediate answers.

#### Acceptance Criteria

1. THE System SHALL provide a chat interface as the default user experience
2. WHEN a user sends a message, THE System SHALL route it to the backend API gateway
3. THE System SHALL support streaming responses from AI providers
4. THE System SHALL maintain chat session history in the database
5. THE System SHALL display messages with timestamps and sender identification
6. THE System SHALL support medical-specific context and terminology

### Requirement 4: Slash Commands

**User Story:** As a user, I want to use slash commands to quickly generate specific study materials, so that I can efficiently create flashcards, MCQs, and summaries.

#### Acceptance Criteria

1. WHEN a user types "/flashcard <topic>", THE System SHALL generate flashcards for that topic
2. WHEN a user types "/mcq <topic>", THE System SHALL generate multiple choice questions
3. WHEN a user types "/highyield <topic>", THE System SHALL generate high-yield summary points
4. WHEN a user types "/explain <topic>", THE System SHALL provide detailed explanations
5. WHEN a user types "/map <topic>", THE System SHALL generate a concept map
6. THE System SHALL parse slash commands at the backend level
7. THE System SHALL track usage of each command type separately

### Requirement 5: Clinical Reasoning and OSCE Simulation

**User Story:** As a medical student, I want to practice clinical reasoning and OSCE scenarios, so that I can prepare for practical examinations.

#### Acceptance Criteria

1. THE System SHALL provide a clinical reasoning mode with case-based scenarios
2. THE System SHALL provide an OSCE simulator with structured examination scenarios
3. WHEN a user enters clinical reasoning mode, THE System SHALL present patient cases progressively
4. WHEN a user enters OSCE mode, THE System SHALL simulate examiner interactions
5. THE System SHALL track user performance and provide feedback

### Requirement 6: Study Planner

**User Story:** As a user, I want a study planner to organize my learning schedule, so that I can manage my study time effectively.

#### Acceptance Criteria

1. THE System SHALL provide a study planner interface
2. THE System SHALL allow users to create study sessions with topics and time allocations
3. THE System SHALL persist study plans to the database
4. THE System SHALL display upcoming and completed study sessions
5. THE System SHALL integrate study planner data with usage tracking

### Requirement 7: Optional PDF and Image Processing

**User Story:** As a user, I want to optionally upload PDFs and images for enhanced learning, so that I can extract summaries, flashcards, and get image interpretations when API capacity allows.

#### Acceptance Criteria

1. WHERE PDF upload is enabled, THE System SHALL accept PDF file uploads
2. WHEN a PDF is uploaded, THE System SHALL extract text and generate embeddings
3. WHEN a PDF is processed, THE System SHALL offer to generate summaries, flashcards, and MCQs
4. WHERE image upload is enabled, THE System SHALL accept medical image uploads
5. WHEN an image is uploaded, THE System SHALL provide AI-powered interpretation if provider supports it
6. THE System SHALL track PDF and image uploads against user quotas
7. IF a provider does not support image processing, THEN THE System SHALL disable image upload features

### Requirement 8: RAG-Grounded Chat

**User Story:** As a user, I want my chat responses to be grounded in my uploaded documents with citations, so that I can verify information sources.

#### Acceptance Criteria

1. WHERE a user has uploaded documents, THE System SHALL use RAG to ground chat responses
2. WHEN generating RAG responses, THE System SHALL use pgvector for similarity search
3. WHEN a response uses document content, THE System SHALL include citations
4. THE System SHALL maintain document embeddings in the database
5. THE System SHALL support semantic search across user documents

### Requirement 9: Freemium Rate Limiting

**User Story:** As the system, I want to enforce plan-based rate limits, so that free users have restricted access while paid users have expanded capabilities.

#### Acceptance Criteria

1. THE System SHALL track daily usage per user including: tokens_used, requests_count, pdf_uploads, mcqs_generated, images_used
2. WHEN a user makes a request, THE System SHALL check their current usage against plan limits
3. IF a user exceeds their plan limits, THEN THE System SHALL reject the request with an upgrade prompt
4. THE System SHALL reset daily counters at midnight UTC
5. WHEN a user with admin role makes requests, THE System SHALL bypass all rate limits
6. THE System SHALL enforce limits at the token level, feature level, and plan level
7. THE System SHALL provide clear feedback when limits are reached

### Requirement 10: API Key Pool Management

**User Story:** As an admin, I want to manually manage a pool of API keys for different providers, so that I can control costs and handle key rotation without code changes.

#### Acceptance Criteria

1. THE System SHALL store API keys encrypted at rest in the database
2. THE System SHALL associate each API key with a specific provider and feature
3. THE System SHALL support key status values: active, degraded, disabled
4. THE System SHALL assign keys based on priority ordering
5. WHEN an admin adds a key, THE System SHALL encrypt it before storage
6. WHEN the backend needs a key, THE System SHALL decrypt and use the highest priority active key
7. THE System SHALL never automatically create or rotate API keys

### Requirement 11: Provider Health Monitoring

**User Story:** As the system, I want to continuously monitor API provider health, so that I can automatically failover to backup keys when providers fail.

#### Acceptance Criteria

1. THE System SHALL periodically send minimal test calls to each active provider
2. THE System SHALL track failure counts per API key
3. WHEN a key fails repeatedly, THE System SHALL mark it as degraded
4. WHEN a key is degraded, THE System SHALL attempt the next priority key
5. THE System SHALL isolate failures by feature (one feature failure does not affect others)
6. THE System SHALL log all provider health checks and failures
7. THE System SHALL notify admins when failover occurs

### Requirement 12: Automatic Maintenance System

**User Story:** As the system, I want to automatically enter maintenance mode when all API keys fail, so that users receive clear communication instead of degraded service.

#### Acceptance Criteria

1. WHEN all active and backup keys for a critical feature fail, THE System SHALL trigger maintenance mode
2. WHEN a provider becomes unreachable, THE System SHALL trigger maintenance mode
3. WHEN quotas are fully exhausted, THE System SHALL trigger maintenance mode
4. THE System SHALL support two maintenance levels: soft and hard
5. WHILE in soft maintenance, THE System SHALL display a banner and pause heavy features while allowing admin access
6. WHILE in hard maintenance, THE System SHALL display a full lock screen and allow admin-only access
7. THE System SHALL never silently degrade output quality
8. WHERE an admin manually overrides maintenance, THE System SHALL allow normal operation
9. THE System SHALL notify admins when maintenance mode is triggered automatically

### Requirement 13: Admin User Management

**User Story:** As an admin, I want to manage users, assign plans, and reset usage limits, so that I can provide customer support and handle special cases.

#### Acceptance Criteria

1. THE Admin_Panel SHALL display a list of all users with their plans and usage statistics
2. WHEN an admin selects a user, THE Admin_Panel SHALL display detailed user information
3. THE Admin_Panel SHALL allow admins to change user plans
4. THE Admin_Panel SHALL allow admins to reset daily usage counters
5. THE Admin_Panel SHALL allow admins to disable or enable user accounts
6. THE System SHALL log all admin actions in an audit trail
7. THE Admin_Panel SHALL be accessible only to users with admin roles

### Requirement 14: Admin API Key Management Interface

**User Story:** As an admin, I want a UI to add, view, and manage API keys, so that I can control provider access without touching code or environment variables.

#### Acceptance Criteria

1. THE Admin_Panel SHALL display all API keys with their provider, feature, status, and priority
2. THE Admin_Panel SHALL allow admins to add new API keys with provider, feature, and priority
3. THE Admin_Panel SHALL mask API key values in the UI (show only last 4 characters)
4. THE Admin_Panel SHALL allow admins to change key status (active, degraded, disabled)
5. THE Admin_Panel SHALL allow admins to adjust key priority
6. THE Admin_Panel SHALL allow admins to delete keys
7. WHEN an admin adds a key, THE System SHALL validate it with a test call before saving

### Requirement 15: Admin Provider Health Dashboard

**User Story:** As an admin, I want to view provider health status and recent failures, so that I can proactively manage API issues.

#### Acceptance Criteria

1. THE Admin_Panel SHALL display current health status for each provider and feature combination
2. THE Admin_Panel SHALL display recent failure logs with timestamps and error messages
3. THE Admin_Panel SHALL display current failover status (which key is active)
4. THE Admin_Panel SHALL allow admins to manually trigger health checks
5. THE Admin_Panel SHALL display quota usage estimates when available

### Requirement 16: Admin Feature Toggles

**User Story:** As an admin, I want to enable or disable specific features globally, so that I can control platform capabilities based on API availability.

#### Acceptance Criteria

1. THE Admin_Panel SHALL display all features with their current enabled/disabled status
2. THE Admin_Panel SHALL allow admins to toggle features on or off
3. WHEN a feature is disabled, THE System SHALL reject user requests for that feature with a clear message
4. THE System SHALL store feature toggle state in the database
5. THE Admin_Panel SHALL allow admins to set feature-specific rate limits

### Requirement 17: Admin Maintenance Control

**User Story:** As an admin, I want to manually trigger or override maintenance mode, so that I can control system availability during planned maintenance or emergencies.

#### Acceptance Criteria

1. THE Admin_Panel SHALL display current maintenance mode status (none, soft, hard)
2. THE Admin_Panel SHALL allow admins to manually trigger soft or hard maintenance
3. THE Admin_Panel SHALL allow admins to override automatic maintenance and restore normal operation
4. THE Admin_Panel SHALL allow admins to set custom maintenance messages
5. WHEN maintenance is manually triggered, THE System SHALL log the admin action and reason

### Requirement 18: Admin Notifications

**User Story:** As an admin, I want to receive notifications for critical system events, so that I can respond quickly to issues.

#### Acceptance Criteria

1. WHEN an API key fails, THE System SHALL send a notification to admins
2. WHEN a fallback occurs, THE System SHALL send a notification to admins
3. WHEN maintenance mode is automatically triggered, THE System SHALL send a notification to admins
4. WHEN an admin manually overrides system behavior, THE System SHALL send a notification to other admins
5. THE System SHALL support email notifications as the primary channel
6. THE System SHALL support webhook notifications for integration with external tools

### Requirement 19: Audit Logging

**User Story:** As an admin, I want comprehensive audit logs of all admin actions and system events, so that I can track changes and investigate issues.

#### Acceptance Criteria

1. THE System SHALL log all admin actions with timestamp, admin email, action type, and details
2. THE System SHALL log all API key changes
3. THE System SHALL log all maintenance mode changes
4. THE System SHALL log all feature toggle changes
5. THE System SHALL log all plan changes and usage resets
6. THE Admin_Panel SHALL display audit logs with filtering and search capabilities
7. THE System SHALL retain audit logs for at least 90 days

### Requirement 20: Backend API Gateway Architecture

**User Story:** As a developer, I want a centralized FastAPI backend that acts as an API gateway, so that all business logic, rate limiting, and provider routing happens server-side.

#### Acceptance Criteria

1. THE Backend SHALL be built with FastAPI using async/await throughout
2. THE Backend SHALL provide a modular service architecture with separate modules for auth, chat, commands, admin, etc.
3. THE Backend SHALL act as the single source of truth for all business logic
4. THE Backend SHALL never expose API keys or sensitive logic to the frontend
5. THE Backend SHALL validate all requests before processing
6. THE Backend SHALL use Supabase for database operations with RLS policies
7. THE Backend SHALL support CORS for the Next.js frontend

### Requirement 21: Model Router and Provider Fallback

**User Story:** As the system, I want intelligent model routing with automatic fallback, so that requests succeed even when primary providers fail.

#### Acceptance Criteria

1. THE Backend SHALL implement a model router that selects providers based on feature and key health
2. WHEN a provider request fails, THE Backend SHALL automatically retry with the next available key
3. THE Backend SHALL track failure counts and adjust routing accordingly
4. THE Backend SHALL support provider-specific request formatting
5. THE Backend SHALL support Gemini Flash as the primary free-tier provider
6. THE Backend SHALL support open-source LLM fallbacks
7. WHERE a user provides their own API key, THE Backend SHALL use it with priority

### Requirement 22: Frontend Next.js Application

**User Story:** As a user, I want a responsive web application that works on desktop, tablet, and mobile, so that I can study from any device.

#### Acceptance Criteria

1. THE Frontend SHALL be built with Next.js
2. THE Frontend SHALL be responsive and work on desktop, tablet, and mobile screen sizes
3. THE Frontend SHALL use a chat-centric UI as the default experience
4. THE Frontend SHALL hide admin routes from non-admin users
5. THE Frontend SHALL never contain business logic or API keys
6. THE Frontend SHALL communicate with the backend via REST API calls
7. THE Frontend SHALL handle loading states and errors gracefully

### Requirement 23: Database Schema and RLS

**User Story:** As a developer, I want a well-designed database schema with proper security, so that data is organized and protected.

#### Acceptance Criteria

1. THE System SHALL use Supabase Postgres as the database
2. THE System SHALL implement tables for: users, admin_allowlist, usage_counters, api_keys, provider_health, system_flags, documents, embeddings, chat_sessions, messages, subscriptions, payments, audit_logs
3. THE System SHALL use pgvector extension for embedding storage
4. THE System SHALL implement RLS policies to protect user data
5. THE System SHALL ensure admin tables are only accessible to admin roles
6. THE System SHALL use foreign keys and constraints to maintain data integrity
7. THE System SHALL index frequently queried columns for performance

### Requirement 24: Payment Integration (Future)

**User Story:** As a user, I want to upgrade my plan using Razorpay, so that I can access premium features.

#### Acceptance Criteria

1. WHERE payment features are enabled, THE System SHALL integrate with Razorpay for subscriptions
2. WHEN a user initiates an upgrade, THE System SHALL create a Razorpay subscription
3. WHEN a payment succeeds, THE System SHALL update the user's plan
4. WHEN a subscription expires, THE System SHALL downgrade the user to the free plan
5. THE System SHALL store payment records in the payments table
6. THE System SHALL handle webhook notifications from Razorpay
7. THE System SHALL support plan upgrades, downgrades, and cancellations

### Requirement 25: Local Development First

**User Story:** As a developer, I want the entire system to work locally before any hosting, so that I can develop and test without deployment dependencies.

#### Acceptance Criteria

1. THE System SHALL run completely on localhost during development
2. THE Frontend SHALL run on a local development server
3. THE Backend SHALL run on a local FastAPI server
4. THE System SHALL use Supabase cloud or local Supabase for database
5. THE System SHALL not require any hosting services during development
6. THE System SHALL provide clear setup instructions for local development
7. THE System SHALL use environment variables for all configuration

### Requirement 26: Deployment Architecture (Final Phase)

**User Story:** As a developer, I want to deploy the system to production hosting after local validation, so that users can access the platform online.

#### Acceptance Criteria

1. WHEN the system is ready for deployment, THE Frontend SHALL be deployed to Netlify
2. WHEN the system is ready for deployment, THE Backend SHALL be deployed to Heroku
3. THE System SHALL use Supabase cloud for production database
4. WHERE CDN is needed, THE System SHALL optionally use Cloudflare
5. THE System SHALL be architected to support future Kubernetes deployment
6. THE System SHALL use environment variables for production configuration
7. THE System SHALL not be deployed until all local testing is complete

### Requirement 27: Optional User-Supplied API Keys

**User Story:** As a user, I want to optionally provide my own API keys, so that I can use the platform even when shared keys are exhausted.

#### Acceptance Criteria

1. WHERE a user provides their own API key, THE System SHALL store it encrypted in their user record
2. WHEN a user with a personal API key makes requests, THE System SHALL use their key with priority
3. THE System SHALL validate user-supplied keys before accepting them
4. THE System SHALL track usage of user-supplied keys separately
5. THE System SHALL allow users to update or remove their personal keys
6. THE System SHALL never share user-supplied keys with other users
7. WHEN a user-supplied key fails, THE System SHALL notify the user and fall back to shared keys if available

### Requirement 28: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages and feedback, so that I understand what went wrong and what actions I can take.

#### Acceptance Criteria

1. WHEN a request fails, THE System SHALL return a user-friendly error message
2. WHEN rate limits are exceeded, THE System SHALL explain the limit and suggest upgrade options
3. WHEN a feature is unavailable, THE System SHALL explain why and when it might be available
4. WHEN maintenance mode is active, THE System SHALL display the maintenance message
5. THE System SHALL distinguish between user errors and system errors
6. THE System SHALL log all errors for admin review
7. THE System SHALL never expose internal error details to non-admin users

### Requirement 29: Performance and Scalability

**User Story:** As a developer, I want the system to be performant and scalable, so that it can handle growing user loads efficiently.

#### Acceptance Criteria

1. THE Backend SHALL use async/await for all I/O operations
2. THE System SHALL implement database connection pooling
3. THE System SHALL cache frequently accessed data where appropriate
4. THE System SHALL use database indexes for query optimization
5. THE System SHALL implement pagination for large result sets
6. THE System SHALL use streaming for long AI responses
7. THE System SHALL be architected to support horizontal scaling in the future

### Requirement 30: Security Best Practices

**User Story:** As a developer, I want the system to follow security best practices, so that user data and platform integrity are protected.

#### Acceptance Criteria

1. THE System SHALL encrypt all API keys at rest using industry-standard encryption
2. THE System SHALL use HTTPS for all production communications
3. THE System SHALL implement CORS policies to restrict frontend access
4. THE System SHALL validate and sanitize all user inputs
5. THE System SHALL use parameterized queries to prevent SQL injection
6. THE System SHALL implement rate limiting to prevent abuse
7. THE System SHALL use Supabase RLS to enforce data access policies
8. THE System SHALL never log sensitive information (API keys, passwords)
9. THE System SHALL implement secure session management
10. THE System SHALL follow OWASP security guidelines
