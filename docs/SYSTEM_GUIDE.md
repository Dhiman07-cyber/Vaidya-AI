# Medical AI Platform - Comprehensive System Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Services Documentation](#services-documentation)
4. [Features Documentation](#features-documentation)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Admin Control Points](#admin-control-points)
7. [Failure and Maintenance Logic](#failure-and-maintenance-logic)
8. [API Key Pool Management](#api-key-pool-management)
9. [Rate Limiting and Quota System](#rate-limiting-and-quota-system)
10. [Security Measures](#security-measures)
11. [Development Guide](#development-guide)
12. [Deployment Guide](#deployment-guide)

---

## System Overview

The Medical AI Platform is a production-grade SaaS application designed for medical students with a **scarcity-first engineering approach**. The system assumes:
- API limitations and quota exhaustion
- Zero initial budget
- Provider failures are expected, not exceptional
- Manual admin control over all critical resources

### Core Principles

1. **Scarcity-First**: Design for API failures, not success
2. **Backend Authority**: All business logic server-side
3. **Admin Control**: Manual management of API keys and features
4. **Graceful Degradation**: Maintenance mode instead of silent quality loss
5. **Local-First**: Complete functionality on localhost before deployment

### Technology Stack

- **Frontend**: Next.js (React, TypeScript)
- **Backend**: FastAPI (Python, async/await)
- **Database**: Supabase (Postgres + Auth + pgvector)
- **AI Providers**: Gemini Flash (primary), Open-source LLMs (fallback)
- **Testing**: Hypothesis (Python PBT), fast-check (TypeScript PBT)


---

## Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat UI     │  │  Admin Panel │  │  Study Tools │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND (FastAPI Gateway)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Service │  │ Chat Service │  │ Rate Limiter │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Model Router  │  │Health Monitor│  │Admin Service │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Supabase Client
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE (Supabase Postgres)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Users     │  │  API Keys    │  │Usage Counters│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Messages   │  │  Documents   │  │  Embeddings  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ API Calls
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL AI PROVIDERS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Gemini Flash │  │  Open-Source │  │  User Keys   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow Architecture

```
User Request → Frontend → Backend API Gateway → Auth Check
                                    ↓
                            Rate Limit Check
                                    ↓
                            Service Router
                                    ↓
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Chat Service   Command Service   Admin Service
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                            Model Router
                                    ↓
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Health Check    Key Selection    Provider Call
                                    ↓
                            Response Stream
                                    ↓
                            Usage Tracking
                                    ↓
                            Frontend Display
```


---

## Services Documentation

### 1. Auth Service (`backend/services/auth.py`)

**Responsibility**: User authentication, authorization, and admin access control

**Key Functions**:
- `authenticate_user(email, password)` - Validates credentials via Supabase Auth
- `register_user(email, password, name)` - Creates new user with default "free" plan
- `verify_admin(user_id)` - Checks admin_allowlist and role
- `check_admin_allowlist(email)` - Verifies email in allowlist
- `get_user_plan(user_id)` - Retrieves user's subscription plan

**Admin Fail-Safe Mechanisms**:
1. **Primary**: admin_allowlist table with email + role
2. **Backup**: SUPER_ADMIN_EMAIL environment variable
3. **Emergency**: Emergency admin token mechanism

**Security Features**:
- Supabase Auth integration for secure authentication
- Multi-level admin verification
- Emergency access for disaster recovery

---

### 2. Chat Service (`backend/services/chat.py`)

**Responsibility**: Chat session management and message handling

**Key Functions**:
- `send_message(user_id, session_id, message)` - Processes user messages
- `get_chat_history(user_id, session_id)` - Retrieves conversation history
- `create_session(user_id, title)` - Creates new chat session
- `get_user_sessions(user_id)` - Lists user's chat sessions

**Features**:
- Streaming responses from AI providers
- RAG integration when user has documents
- Message persistence with timestamps
- Citation support for document-grounded responses

**Integration Points**:
- Rate Limiter: Checks limits before processing
- Model Router: Routes requests to AI providers
- Document Service: Retrieves relevant document chunks for RAG

---

### 3. Command Service (`backend/services/commands.py`)

**Responsibility**: Slash command parsing and execution

**Supported Commands**:
- `/flashcard <topic>` - Generates flashcards
- `/mcq <topic>` - Generates multiple choice questions
- `/highyield <topic>` - Generates high-yield summary points
- `/explain <topic>` - Provides detailed explanations
- `/map <topic>` - Generates concept maps

**Key Functions**:
- `parse_command(message)` - Detects and extracts slash commands
- `execute_command(user_id, command, topic)` - Routes to appropriate handler
- `generate_flashcards(topic)` - Creates flashcard content
- `generate_mcqs(topic)` - Creates MCQ content
- `generate_summary(topic)` - Creates summary content
- `generate_explanation(topic)` - Creates explanation content
- `generate_concept_map(topic)` - Creates concept map content

**Usage Tracking**:
- Each command type tracked separately
- Counters: mcqs_generated, flashcards_generated
- Subject to plan-based rate limits


---

### 4. Rate Limiter Service (`backend/services/rate_limiter.py`)

**Responsibility**: Enforce plan-based usage limits

**Key Functions**:
- `check_rate_limit(user_id, feature)` - Validates request against limits
- `increment_usage(user_id, tokens, feature)` - Updates usage counters
- `get_user_usage(user_id)` - Retrieves current usage statistics
- `reset_daily_counters()` - Scheduled job to reset at midnight UTC

**Plan Limits**:
```python
PLAN_LIMITS = {
    "free": {
        "daily_tokens": 10000,
        "daily_requests": 20,
        "pdf_uploads": 0,
        "mcqs_per_day": 5,
        "images_per_day": 0,
        "flashcards_per_day": 10,
    },
    "student": {
        "daily_tokens": 50000,
        "daily_requests": 100,
        "pdf_uploads": 5,
        "mcqs_per_day": 50,
        "images_per_day": 10,
        "flashcards_per_day": 100,
    },
    "pro": {
        "daily_tokens": 200000,
        "daily_requests": 500,
        "pdf_uploads": 50,
        "mcqs_per_day": 200,
        "images_per_day": 50,
        "flashcards_per_day": 500,
    },
    "admin": {
        # Unlimited for all metrics
    }
}
```

**Multi-Level Limiting**:
1. Token level: Total AI tokens consumed
2. Feature level: Specific feature usage (MCQs, flashcards, etc.)
3. Plan level: Overall request count

**Admin Bypass**: Users with admin role bypass all limits

---

### 5. Model Router Service (`backend/services/model_router.py`)

**Responsibility**: Intelligent provider selection and request routing

**Key Functions**:
- `route_request(feature, prompt, user_id)` - Main routing logic
- `select_provider(feature)` - Chooses provider based on feature
- `get_active_key(provider, feature)` - Selects best available API key
- `execute_with_fallback(provider, key, prompt)` - Executes with automatic retry

**Key Selection Priority**:
1. User-supplied API key (if present)
2. Highest priority active shared key
3. Next priority key on failure
4. Up to 3 retry attempts

**Provider-Specific Formatting**:
- Gemini Flash: Specific request format
- Open-source LLMs: Provider-specific formats
- Handles streaming responses

**Failure Handling**:
- Automatic retry with next available key
- Failure count tracking per key
- Triggers maintenance if all keys fail


---

### 6. Health Monitor Service (`backend/services/health_monitor.py`)

**Responsibility**: Continuous provider health monitoring

**Key Functions**:
- `check_provider_health(provider, key)` - Performs minimal test call
- `periodic_health_check()` - Background task (runs every 5 minutes)
- `record_failure(key_id, error)` - Logs failure with details
- `mark_key_degraded(key_id)` - Changes status after N failures
- `get_provider_status(provider, feature)` - Returns current health status

**Health Status Values**:
- `active`: Key working normally
- `degraded`: Recent failures, use with caution
- `disabled`: Manually disabled by admin

**Monitoring Strategy**:
- Minimal test calls to avoid quota waste
- Periodic checks every 5 minutes
- Failure threshold: N consecutive failures → degraded
- Logs stored in provider_health table

**Integration**:
- Model Router uses health status for key selection
- Maintenance Service triggered on total failure
- Notification Service alerts admins on degradation

---

### 7. Maintenance Service (`backend/services/maintenance.py`)

**Responsibility**: Automatic and manual maintenance mode management

**Key Functions**:
- `evaluate_maintenance_trigger(feature, failures)` - Determines if maintenance needed
- `enter_maintenance(level, reason)` - Activates maintenance mode
- `exit_maintenance()` - Deactivates maintenance mode
- `get_maintenance_status()` - Returns current status

**Maintenance Levels**:

**Soft Maintenance**:
- Display banner message
- Pause heavy features (PDF processing, image analysis)
- Allow chat and admin access
- Triggered by: Partial key failures, degraded performance

**Hard Maintenance**:
- Display full lock screen
- Block all non-admin access
- Admin-only access for recovery
- Triggered by: Total key failure, provider unreachable, quota exhausted

**Trigger Conditions**:
1. All active keys for critical feature failed
2. Provider completely unreachable
3. Quotas fully exhausted
4. Manual admin trigger

**Override Mechanism**:
- Admins can manually override automatic maintenance
- Logged in audit trail
- Notifications sent to other admins

---

### 8. Admin Service (`backend/services/admin.py`)

**Responsibility**: Administrative operations and user management

**User Management Functions**:
- `list_users(filters)` - Retrieves user list with filtering
- `update_user_plan(user_id, plan)` - Changes user subscription plan
- `reset_user_usage(user_id)` - Resets daily usage counters
- `disable_user(user_id)` - Disables user account

**API Key Management Functions**:
- `add_api_key(provider, feature, key, priority)` - Adds new API key
- `list_api_keys()` - Lists all API keys (masked)
- `update_key_status(key_id, status)` - Changes key status
- `delete_api_key(key_id)` - Removes API key
- `test_api_key(key)` - Validates key before storage

**Feature Management Functions**:
- `toggle_feature(feature, enabled)` - Enables/disables features globally
- `get_feature_status()` - Returns all feature statuses

**Maintenance Management Functions**:
- `trigger_maintenance(level, message)` - Manually enters maintenance
- `override_maintenance()` - Exits maintenance mode

**Audit Functions**:
- `get_audit_logs(filters)` - Retrieves audit log entries
- `log_admin_action(admin_id, action, details)` - Records admin action

**Security**:
- All functions require admin authentication
- All actions logged to audit_logs table
- Sensitive operations trigger notifications


---

### 9. Document Service (`backend/services/documents.py`)

**Responsibility**: PDF/image upload and RAG implementation

**Key Functions**:
- `upload_document(user_id, file)` - Handles file upload
- `process_pdf(document_id)` - Async text extraction and embedding
- `generate_embeddings(text)` - Creates vector embeddings
- `semantic_search(user_id, query, top_k)` - Finds relevant document chunks
- `get_user_documents(user_id)` - Lists user's documents
- `delete_document(document_id)` - Removes document and embeddings

**Processing Pipeline**:
1. File upload → Storage
2. Text extraction (PDF parsing)
3. Chunking (split into manageable pieces)
4. Embedding generation (vector representation)
5. Storage in embeddings table with pgvector

**RAG Integration**:
- Semantic search using pgvector similarity
- Top-k relevant chunks retrieved
- Chunks included in prompt context
- Citations added to response

**Quota Tracking**:
- pdf_uploads counter incremented
- Subject to plan limits
- Free plan: 0 uploads (disabled)

---

### 10. Notification Service (`backend/services/notifications.py`)

**Responsibility**: Admin alerts and notifications

**Key Functions**:
- `send_email(to, subject, body)` - Email notifications
- `send_webhook(url, payload)` - Webhook notifications
- `notify_api_key_failure(key_id, error)` - Key failure alert
- `notify_fallback(from_key, to_key)` - Fallback alert
- `notify_maintenance_triggered(level, reason)` - Maintenance alert
- `notify_admin_override(admin_id, action)` - Override alert

**Notification Channels**:
1. **Email**: Primary channel for critical alerts
2. **Webhook**: Integration with external tools (Slack, PagerDuty, etc.)

**Critical Events**:
- API key failures
- Automatic failover
- Maintenance mode triggered
- Admin manual overrides
- Security events

---

### 11. Clinical Service (`backend/services/clinical.py`)

**Responsibility**: Clinical reasoning and OSCE simulation

**Key Functions**:
- `create_clinical_case()` - Generates patient case scenarios
- `present_case_progressively(session_id)` - Reveals case information step-by-step
- `evaluate_clinical_reasoning(user_response)` - Assesses user's reasoning
- `create_osce_scenario()` - Generates OSCE examination scenarios
- `simulate_examiner_interaction(user_action)` - Simulates examiner responses
- `track_performance(user_id, session_id)` - Records performance metrics

**Clinical Reasoning Mode**:
- Progressive case presentation
- User makes diagnostic decisions
- System evaluates reasoning process
- Feedback on clinical thinking

**OSCE Simulator**:
- Structured examination scenarios
- Examiner interaction simulation
- Performance tracking
- Feedback on examination technique

---

### 12. Study Planner Service (`backend/services/study_planner.py`)

**Responsibility**: Study session management

**Key Functions**:
- `create_study_session(user_id, topic, duration)` - Creates study plan
- `get_study_sessions(user_id)` - Retrieves user's study plans
- `update_study_session(session_id, data)` - Updates study plan
- `delete_study_session(session_id)` - Removes study plan

**Features**:
- Calendar-based planning
- Topic organization
- Time allocation
- Progress tracking
- Integration with usage statistics

---

### 13. Payment Service (`backend/services/payments.py`)

**Responsibility**: Razorpay integration for subscriptions

**Key Functions**:
- `create_subscription(user_id, plan)` - Initiates Razorpay subscription
- `handle_payment_webhook(payload)` - Processes payment notifications
- `cancel_subscription(subscription_id)` - Cancels subscription

**Payment Flow**:
1. User selects plan
2. Razorpay subscription created
3. User completes payment
4. Webhook received
5. User plan updated
6. Payment recorded

**Subscription Management**:
- Active subscriptions tracked
- Expiry handling (downgrade to free)
- Payment history stored
- Webhook signature verification

---

### 14. Encryption Service (`backend/services/encryption.py`)

**Responsibility**: API key encryption/decryption

**Key Functions**:
- `encrypt_key(plaintext)` - Encrypts API key using AES-256-GCM
- `decrypt_key(ciphertext)` - Decrypts API key

**Security**:
- AES-256-GCM encryption
- Encryption key stored in environment variable
- Keys never logged or exposed
- Encrypted at rest in database


---

## Features Documentation

### 1. AI Chat Interface

**Description**: Primary user experience - conversational AI tutor

**User Flow**:
1. User logs in → Redirected to chat interface
2. User selects or creates chat session
3. User types message
4. Backend checks rate limits
5. Model Router selects provider and key
6. AI response streamed back
7. Message saved to database
8. Usage counters updated

**Technical Details**:
- Streaming responses for better UX
- Session-based conversation history
- Medical terminology support
- RAG integration when documents available

**Rate Limits**: Subject to daily_requests and daily_tokens limits

---

### 2. Slash Commands

**Description**: Quick generation of study materials

**Available Commands**:

**/flashcard <topic>**
- Generates flashcards for spaced repetition
- Format: Question on front, answer on back
- Tracked separately: flashcards_generated counter

**/mcq <topic>**
- Generates multiple choice questions
- Format: Question + 4 options + correct answer + explanation
- Tracked separately: mcqs_generated counter

**/highyield <topic>**
- Generates high-yield summary points
- Format: Bullet points of key information
- Ideal for quick review

**/explain <topic>**
- Provides detailed explanations
- Format: Comprehensive breakdown with examples
- Useful for complex topics

**/map <topic>**
- Generates concept maps
- Format: Visual representation of relationships
- Helps with understanding connections

**Usage**: Type command in chat, system routes to appropriate handler

---

### 3. Document Upload and RAG

**Description**: Upload PDFs for document-grounded chat

**Upload Flow**:
1. User uploads PDF via documents page
2. File stored in Supabase storage
3. Async processing begins:
   - Text extraction
   - Chunking
   - Embedding generation
   - Storage in embeddings table
4. Document available for RAG

**RAG Flow**:
1. User sends chat message
2. System detects user has documents
3. Semantic search finds relevant chunks
4. Chunks included in prompt context
5. Response includes citations

**Quota**: Subject to pdf_uploads limit (free plan: 0)

---

### 4. Clinical Reasoning Mode

**Description**: Case-based clinical scenario practice

**Features**:
- Progressive case presentation
- Diagnostic decision making
- Clinical reasoning evaluation
- Performance feedback

**Use Case**: Preparing for clinical examinations, practicing diagnostic thinking

---

### 5. OSCE Simulator

**Description**: Structured clinical examination practice

**Features**:
- Realistic examination scenarios
- Examiner interaction simulation
- Performance tracking
- Technique feedback

**Use Case**: Preparing for OSCE exams, practicing examination skills

---

### 6. Study Planner

**Description**: Organize study schedule

**Features**:
- Create study sessions
- Topic organization
- Time allocation
- Progress tracking

**Use Case**: Managing study time, organizing learning schedule

---

### 7. Admin Panel

**Description**: Administrative control interface

**Sections**:

**User Management**:
- View all users
- Change user plans
- Reset usage counters
- Disable/enable accounts

**API Key Management**:
- Add new API keys
- View keys (masked)
- Change key status
- Adjust priority
- Delete keys
- Test keys before adding

**Provider Health Dashboard**:
- View current health status
- See failure logs
- Monitor failover status
- Trigger manual health checks

**Feature Toggles**:
- Enable/disable features globally
- Control feature availability

**Maintenance Control**:
- View maintenance status
- Manually trigger maintenance
- Override automatic maintenance
- Set custom messages

**Audit Logs**:
- View all admin actions
- Filter by admin, action type, date
- Search functionality

**Access**: Admin role required, protected routes


---

## Data Flow Diagrams

### 1. User Authentication Flow

```
User → Frontend Login Form
         ↓
    POST /api/auth/login
         ↓
    Backend Auth Service
         ↓
    Supabase Auth Validation
         ↓
    ┌─── Valid? ───┐
    ↓              ↓
   Yes             No
    ↓              ↓
Get User Plan   Return 401
    ↓
Return Token + User Data
    ↓
Frontend Stores Token
    ↓
Redirect to Chat
```

---

### 2. Chat Message Flow

```
User Types Message → Frontend
         ↓
    POST /api/chat/sessions/{id}/messages
         ↓
    Backend API Gateway
         ↓
    Auth Middleware (verify token)
         ↓
    Rate Limiter Check
         ↓
    ┌─── Within Limits? ───┐
    ↓                      ↓
   Yes                     No
    ↓                      ↓
Chat Service          Return 429 + Upgrade Prompt
    ↓
Check for Slash Command
    ↓
    ┌─── Is Command? ───┐
    ↓                   ↓
   Yes                  No
    ↓                   ↓
Command Service    Check for Documents
    ↓                   ↓
Model Router       ┌─── Has Docs? ───┐
    ↓              ↓                  ↓
Select Provider   Yes                 No
    ↓              ↓                  ↓
Get Active Key  Semantic Search   Direct Prompt
    ↓              ↓                  ↓
Health Check   Add Chunks to Prompt  │
    ↓              └──────────────────┘
    ┌─── Key Healthy? ───┐
    ↓                    ↓
   Yes                   No
    ↓                    ↓
Call Provider      Try Next Key
    ↓                    ↓
    ┌─── Success? ───┐  │
    ↓                ↓  │
   Yes               No │
    ↓                ↓  │
Stream Response  Record Failure
    ↓                ↓
Save Message    Retry (up to 3x)
    ↓                ↓
Update Usage    ┌─── All Failed? ───┐
    ↓           ↓                    ↓
Return to      Yes                   No
Frontend        ↓                    ↓
         Trigger Maintenance    Continue Retry
```

---

### 3. API Key Selection Flow

```
Request Arrives → Model Router
         ↓
    Check User Has Personal Key?
         ↓
    ┌─── Has Key? ───┐
    ↓                ↓
   Yes               No
    ↓                ↓
Use User Key    Query Shared Keys
    ↓                ↓
    │           Filter by Provider + Feature
    │                ↓
    │           Filter by Status = 'active'
    │                ↓
    │           Sort by Priority DESC
    │                ↓
    │           Select Top Key
    │                ↓
    └────────────────┘
         ↓
    Check Health Status
         ↓
    ┌─── Healthy? ───┐
    ↓                ↓
   Yes               No
    ↓                ↓
Decrypt Key     Try Next Key
    ↓                ↓
Use for Call    Repeat Process
         ↓
    ┌─── Call Success? ───┐
    ↓                     ↓
   Yes                    No
    ↓                     ↓
Return Response    Record Failure
                        ↓
                   Increment Failure Count
                        ↓
                   ┌─── Count > Threshold? ───┐
                   ↓                           ↓
                  Yes                          No
                   ↓                           ↓
              Mark Degraded              Continue
                   ↓
              Notify Admin
```

---

### 4. Maintenance Trigger Flow

```
Provider Call Fails → Model Router
         ↓
    Record Failure
         ↓
    Try Next Key
         ↓
    ┌─── More Keys? ───┐
    ↓                  ↓
   Yes                 No
    ↓                  ↓
Retry Call      All Keys Failed
    ↓                  ↓
    │           Maintenance Service
    │                  ↓
    │           Evaluate Severity
    │                  ↓
    │           ┌─── Critical Feature? ───┐
    │           ↓                          ↓
    │          Yes                         No
    │           ↓                          ↓
    │      Enter Hard Maintenance    Enter Soft Maintenance
    │           ↓                          ↓
    │      Update system_flags       Update system_flags
    │           ↓                          ↓
    │      Notify Admins             Notify Admins
    │           ↓                          ↓
    │      Block All Non-Admin       Pause Heavy Features
    │           ↓                          ↓
    │      Display Lock Screen       Display Banner
    │           ↓                          ↓
    └───────────┴──────────────────────────┘
                   ↓
         Admin Can Override
                   ↓
         Exit Maintenance
                   ↓
         Log Override Action
                   ↓
         Notify Other Admins
```

---

### 5. Rate Limiting Flow

```
Request Arrives → Rate Limiter
         ↓
    Get User ID
         ↓
    Check User Role
         ↓
    ┌─── Is Admin? ───┐
    ↓                 ↓
   Yes                No
    ↓                 ↓
Bypass Limits    Get User Plan
    ↓                 ↓
Allow Request    Get Plan Limits
                      ↓
                 Query usage_counters
                      ↓
                 Get Current Usage
                      ↓
                 Check Token Limit
                      ↓
                 ┌─── Within Limit? ───┐
                 ↓                      ↓
                Yes                     No
                 ↓                      ↓
            Check Feature Limit    Return 429
                 ↓                      ↓
            ┌─── Within Limit? ───┐    │
            ↓                      ↓    │
           Yes                     No   │
            ↓                      ↓    │
       Check Request Limit    Return 429
            ↓                      ↓
       ┌─── Within Limit? ───┐    │
       ↓                      ↓    │
      Yes                     No   │
       ↓                      ↓    │
  Allow Request          Return 429
       ↓
  Process Request
       ↓
  Increment Counters
       ↓
  Update usage_counters
```


---

## Admin Control Points

### 1. User Management Control Points

**Location**: Admin Panel → Users

**Controls**:
- **View Users**: List all users with plan and usage stats
- **Change Plan**: Modify user subscription (free/student/pro/admin)
- **Reset Usage**: Zero out daily usage counters for user
- **Disable Account**: Prevent user login and access
- **Enable Account**: Restore user access

**Use Cases**:
- Customer support: Upgrade user manually
- Abuse prevention: Disable problematic accounts
- Testing: Reset usage for testing purposes
- Emergency: Grant temporary admin access

**Audit**: All actions logged with admin_id, timestamp, details

---

### 2. API Key Management Control Points

**Location**: Admin Panel → API Keys

**Controls**:
- **Add Key**: Manually add new provider API key
  - Select provider (Gemini, OpenAI, etc.)
  - Select feature (chat, flashcard, mcq, etc.)
  - Set priority (higher = preferred)
  - Test before saving
- **View Keys**: See all keys (masked for security)
- **Change Status**: Toggle active/degraded/disabled
- **Adjust Priority**: Change selection order
- **Delete Key**: Remove key from pool

**Key Selection Logic**:
1. User personal key (if exists)
2. Highest priority active shared key
3. Next priority on failure
4. Degraded keys skipped unless no alternatives

**Use Cases**:
- Add new provider keys as budget allows
- Rotate keys for security
- Disable compromised keys immediately
- Adjust priority based on quota/cost
- Remove expired or invalid keys

**Security**:
- Keys encrypted at rest (AES-256-GCM)
- Masked in UI (show last 4 chars only)
- Test validation before storage
- All changes logged

---

### 3. Provider Health Control Points

**Location**: Admin Panel → Provider Health

**Controls**:
- **View Status**: Current health per provider/feature
- **View Failures**: Recent failure logs with errors
- **View Failover**: Which key is currently active
- **Manual Check**: Trigger health check immediately
- **View Quota**: Estimated quota remaining (if available)

**Health Monitoring**:
- Automatic checks every 5 minutes  
- Minimal test calls to save quota
- Failure threshold: N failures → degraded
- Degraded keys trigger fallback

**Use Cases**:
- Monitor provider reliability
- Investigate failures
- Verify failover working
- Proactive key management

---

### 4. Feature Toggle Control Points

**Location**: Admin Panel → Features

**Controls**:
- **View Features**: All features with enabled/disabled status
- **Toggle Feature**: Enable/disable globally
- **Set Limits**: Adjust feature-specific rate limits

**Available Toggles**:
- Chat
- Flashcards
- MCQs
- High-yield summaries
- Explanations
- Concept maps
- PDF upload
- Image upload
- Clinical reasoning
- OSCE simulator
- Study planner

**Use Cases**:
- Disable expensive features when quota low
- Enable features as API capacity increases
- A/B testing new features
- Emergency feature shutdown

**Effect**: Disabled features return clear error message to users

---

### 5. Maintenance Mode Control Points

**Location**: Admin Panel → Maintenance

**Controls**:
- **View Status**: Current maintenance level (none/soft/hard)
- **Trigger Soft**: Manually enter soft maintenance
- **Trigger Hard**: Manually enter hard maintenance
- **Override**: Exit automatic maintenance
- **Set Message**: Custom maintenance message for users

**Maintenance Levels**:

**Soft Maintenance**:
- Banner displayed to users
- Heavy features paused (PDF, images)
- Chat and admin access continue
- Use when: Partial degradation, planned maintenance

**Hard Maintenance**:
- Full lock screen displayed
- All non-admin access blocked
- Admin-only access for recovery
- Use when: Total failure, critical issues

**Automatic Triggers**:
- All keys failed for critical feature
- Provider completely unreachable
- Quotas fully exhausted

**Manual Override**:
- Admin can force exit maintenance
- Logged in audit trail
- Other admins notified
- Use when: False positive, manual recovery complete

---

### 6. Audit Log Control Points

**Location**: Admin Panel → Audit Logs

**Controls**:
- **View Logs**: All admin actions with details
- **Filter by Admin**: See specific admin's actions
- **Filter by Action**: See specific action types
- **Filter by Date**: Time range selection
- **Search**: Full-text search in details

**Logged Actions**:
- User plan changes
- Usage resets
- Account disable/enable
- API key additions/deletions
- Key status changes
- Feature toggles
- Maintenance triggers/overrides
- All admin operations

**Retention**: Minimum 90 days

**Use Cases**:
- Compliance and accountability
- Investigate issues
- Track system changes
- Security auditing

---

### 7. Notification Control Points

**Location**: Admin Panel → Notifications (or via service configuration)

**Controls**:
- **Email Recipients**: Configure admin email addresses
- **Webhook URLs**: Configure external integrations
- **Alert Thresholds**: Set when to notify
- **Notification Types**: Enable/disable specific alerts

**Notification Events**:
- API key failures
- Automatic failover
- Maintenance mode triggered
- Admin manual overrides
- Security events
- Quota warnings

**Channels**:
- Email (primary)
- Webhook (Slack, PagerDuty, etc.)


---

## Failure and Maintenance Logic

### Failure Detection

**1. Provider Call Failures**

Detection:
- HTTP errors (4xx, 5xx)
- Network timeouts
- Invalid responses
- Rate limit errors from provider

Response:
- Record failure in provider_health table
- Increment failure_count for key
- Attempt next priority key
- Up to 3 retry attempts

**2. Key Degradation**

Trigger: N consecutive failures (configurable threshold)

Process:
```
Failure Count > Threshold
    ↓
Mark key status = 'degraded'
    ↓
Update api_keys table
    ↓
Notify admins
    ↓
Model Router skips degraded keys
    ↓
Use next priority active key
```

**3. Total Key Failure**

Trigger: All keys for a feature have failed

Process:
```
All Keys Failed
    ↓
Maintenance Service Evaluates
    ↓
Is Critical Feature? (chat, core functions)
    ↓
    ┌─── Yes ───┐         ┌─── No ───┐
    ↓            ↓         ↓          ↓
Hard Maintenance  Soft Maintenance
```

---

### Maintenance Mode Logic

**Soft Maintenance**

**When Triggered**:
- Non-critical feature failures
- Partial key degradation
- Planned maintenance
- Manual admin trigger

**System Behavior**:
- Display banner message to users
- Pause heavy features:
  - PDF processing
  - Image analysis
  - Bulk operations
- Continue light features:
  - Chat (if keys available)
  - Viewing history
  - Admin panel
- Admin access: Full access

**User Experience**:
```
┌─────────────────────────────────────────┐
│ ⚠️  System Maintenance                  │
│ Some features temporarily unavailable   │
│ Chat and core features still working    │
└─────────────────────────────────────────┘
```

**Hard Maintenance**

**When Triggered**:
- All keys failed for critical features
- Provider completely unreachable
- Quotas fully exhausted
- Critical system errors
- Manual admin trigger

**System Behavior**:
- Block all non-admin requests
- Display full lock screen
- Admin-only access for recovery
- All user operations return 503

**User Experience**:
```
┌─────────────────────────────────────────┐
│                                         │
│         🔧 System Maintenance           │
│                                         │
│  We're currently performing maintenance │
│  Please check back soon                 │
│                                         │
│  Estimated restoration: [time]          │
│                                         │
└─────────────────────────────────────────┘
```

---

### Automatic Recovery

**Health Check Recovery**

Process:
```
Periodic Health Check (every 5 minutes)
    ↓
Test degraded keys
    ↓
    ┌─── Success? ───┐
    ↓                ↓
   Yes               No
    ↓                ↓
Mark active    Keep degraded
    ↓                ↓
Notify admins  Continue monitoring
    ↓
If enough keys active
    ↓
Exit maintenance automatically
```

**Manual Recovery**

Admin Actions:
1. Add new API keys
2. Re-enable degraded keys
3. Manual override maintenance
4. Adjust feature toggles

Process:
```
Admin Adds New Key
    ↓
Key Validated
    ↓
Key Stored (encrypted)
    ↓
Health Check Passes
    ↓
Key Available for Use
    ↓
If in maintenance + keys available
    ↓
Suggest exit maintenance
```

---

### Failure Isolation

**Feature-Level Isolation**

Principle: Failure in one feature doesn't affect others

Implementation:
- Keys tagged by feature (chat, flashcard, mcq, etc.)
- Health tracked per feature-provider combination
- Maintenance evaluated per feature
- Fallback independent per feature

Example:
```
MCQ feature keys all fail
    ↓
MCQ feature disabled
    ↓
Chat feature continues normally
    ↓
User sees: "MCQ generation temporarily unavailable"
```

**Provider-Level Isolation**

Principle: Failure of one provider doesn't affect others

Implementation:
- Multiple providers supported (Gemini, OpenAI, OSS)
- Keys tagged by provider
- Fallback to different providers
- Provider-specific health tracking

Example:
```
Gemini quota exhausted
    ↓
Fallback to OpenAI keys
    ↓
If OpenAI also fails
    ↓
Fallback to OSS LLM
    ↓
If all fail
    ↓
Maintenance mode
```

---

### Notification Strategy

**Failure Notifications**

**Key Failure**:
- Trigger: Single key fails
- Recipient: Admins
- Channel: Email
- Content: Key ID, provider, error message
- Urgency: Low (automatic fallback working)

**Degradation**:
- Trigger: Key marked degraded
- Recipient: Admins
- Channel: Email + Webhook
- Content: Key details, failure count, remaining keys
- Urgency: Medium (fallback available but limited)

**Failover**:
- Trigger: Automatic switch to backup key
- Recipient: Admins
- Channel: Email + Webhook
- Content: From key, to key, reason
- Urgency: Medium (system still working)

**Maintenance Triggered**:
- Trigger: Automatic maintenance mode
- Recipient: All admins
- Channel: Email + Webhook + SMS (if configured)
- Content: Level, reason, affected features
- Urgency: High (user impact)

**Manual Override**:
- Trigger: Admin overrides automatic maintenance
- Recipient: Other admins
- Channel: Email + Webhook
- Content: Admin ID, reason, timestamp
- Urgency: High (manual intervention)


---

## API Key Pool Management

### Concept

The API Key Pool is a manually-managed collection of API keys for different AI providers. This design assumes:
- **No automatic key generation**: All keys manually added by admins
- **No automatic rotation**: Keys manually rotated when needed
- **Scarcity mindset**: Keys are precious resources
- **Manual control**: Admins decide when/how to use keys

### Key Structure

Each API key has:
- **provider**: AI service (gemini, openai, ollama, etc.)
- **feature**: Specific use (chat, flashcard, mcq, image, etc.)
- **key_value**: Encrypted API key
- **priority**: Selection order (higher = preferred)
- **status**: active, degraded, disabled
- **failure_count**: Number of consecutive failures
- **last_used_at**: Timestamp of last use

### Key Lifecycle

**1. Addition**

Process:
```
Admin enters key in UI
    ↓
Select provider + feature
    ↓
Set priority
    ↓
System validates key (test call)
    ↓
    ┌─── Valid? ───┐
    ↓              ↓
   Yes             No
    ↓              ↓
Encrypt key    Show error
    ↓
Store in database
    ↓
Log action
    ↓
Key available for use
```

Validation ensures:
- Key format correct
- Key actually works
- Provider accessible
- No duplicate keys

**2. Selection**

Priority order:
1. User personal key (if exists)
2. Highest priority active shared key
3. Next priority on failure
4. Skip degraded keys unless no alternatives

Selection algorithm:
```python
def get_active_key(provider, feature, user_id):
    # Check user personal key first
    user_key = get_user_api_key(user_id)
    if user_key and user_key.provider == provider:
        return user_key
    
    # Get shared keys
    keys = query_keys(
        provider=provider,
        feature=feature,
        status='active'
    ).order_by('priority DESC')
    
    # Return highest priority
    return keys.first()
```

**3. Usage**

Process:
```
Request arrives
    ↓
Model Router selects key
    ↓
Decrypt key
    ↓
Format request for provider
    ↓
Call provider API
    ↓
    ┌─── Success? ───┐
    ↓                ↓
   Yes               No
    ↓                ↓
Update last_used  Record failure
    ↓                ↓
Return response  Increment failure_count
                     ↓
                 Try next key
```

**4. Degradation**

Trigger: failure_count > threshold (e.g., 5)

Process:
```
Failure count exceeds threshold
    ↓
Mark status = 'degraded'
    ↓
Notify admins
    ↓
Model Router skips key
    ↓
Admin investigates
    ↓
    ┌─── Resolution ───┐
    ↓                  ↓
Fix issue        Remove key
    ↓                  ↓
Mark active      Delete from pool
```

**5. Removal**

Reasons:
- Key expired
- Key compromised
- Provider no longer used
- Key consistently failing

Process:
```
Admin deletes key
    ↓
Confirm deletion
    ↓
Remove from database
    ↓
Log action
    ↓
Notify other admins
```

---

### Key Management Strategies

**1. Priority Management**

Strategy: Assign priorities based on cost and quota

Example:
```
Priority 100: Free tier keys (use first)
Priority 50:  Paid tier keys (fallback)
Priority 10:  Expensive keys (last resort)
```

**2. Feature Segmentation**

Strategy: Dedicate keys to specific features

Example:
```
Key A: provider=gemini, feature=chat, priority=100
Key B: provider=gemini, feature=flashcard, priority=100
Key C: provider=gemini, feature=mcq, priority=100
```

Benefits:
- Quota isolation
- Feature-specific optimization
- Better failure isolation

**3. Provider Diversification**

Strategy: Use multiple providers for redundancy

Example:
```
Primary:   Gemini Flash (free tier)
Secondary: OpenAI (paid tier)
Tertiary:  Ollama (self-hosted)
```

Benefits:
- No single point of failure
- Cost optimization
- Quota distribution

**4. User-Supplied Keys**

Strategy: Allow users to provide their own keys

Benefits:
- Unlimited usage for user
- No cost to platform
- User controls their quota

Implementation:
- User adds key in profile
- Key encrypted and stored
- Priority over shared keys
- Fallback to shared if fails

---

### Key Security

**Encryption**

Algorithm: AES-256-GCM

Process:
```python
def encrypt_key(plaintext):
    key = os.environ['ENCRYPTION_KEY']
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return {
        'ciphertext': ciphertext,
        'nonce': cipher.nonce,
        'tag': tag
    }

def decrypt_key(encrypted):
    key = os.environ['ENCRYPTION_KEY']
    cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted['nonce'])
    plaintext = cipher.decrypt_and_verify(
        encrypted['ciphertext'],
        encrypted['tag']
    )
    return plaintext
```

**Storage**:
- Keys encrypted at rest in database
- Encryption key in environment variable
- Never logged or exposed in responses
- Masked in UI (show last 4 chars only)

**Access Control**:
- Only backend can decrypt
- Frontend never sees keys
- Admin UI shows masked values
- Audit log for all key operations

---

### Monitoring and Alerts

**Key Health Metrics**:
- Success rate
- Failure count
- Response time
- Last used timestamp
- Quota remaining (if available)

**Alerts**:
- Key failure → Email to admins
- Key degraded → Email + Webhook
- All keys failed → Email + Webhook + SMS
- New key added → Email to admins
- Key deleted → Email to admins

**Dashboard**:
- Current status per key
- Recent failures
- Usage statistics
- Quota estimates


---

## Rate Limiting and Quota System

### Overview

The rate limiting system enforces plan-based usage limits to:
- Protect against abuse
- Manage API costs
- Encourage plan upgrades
- Ensure fair resource distribution

### Plan Structure

**Free Plan**:
```python
{
    "daily_tokens": 10000,        # ~10 chat messages
    "daily_requests": 20,          # Total API calls
    "pdf_uploads": 0,              # No PDF uploads
    "mcqs_per_day": 5,             # Limited MCQs
    "images_per_day": 0,           # No image analysis
    "flashcards_per_day": 10,      # Limited flashcards
}
```

**Student Plan** ($1.99/month):
```python
{
    "daily_tokens": 50000,         # ~50 chat messages
    "daily_requests": 100,         # More API calls
    "pdf_uploads": 5,              # 5 PDFs per day
    "mcqs_per_day": 50,            # More MCQs
    "images_per_day": 10,          # Image analysis
    "flashcards_per_day": 100,     # More flashcards
}
```

**Pro Plan** ($29.99/month):
```python
{
    "daily_tokens": 200000,        # ~200 chat messages
    "daily_requests": 500,         # High volume
    "pdf_uploads": 50,             # Many PDFs
    "mcqs_per_day": 200,           # High MCQ generation
    "images_per_day": 50,          # High image analysis
    "flashcards_per_day": 500,     # High flashcard generation
}
```

**Admin Plan**:
```python
{
    # All limits set to infinity
    # Admins bypass all rate limiting
}
```

---

### Rate Limiting Algorithm

**Token Bucket Algorithm**

Concept: Each user has a "bucket" of tokens that refills daily

Implementation:
```python
def check_rate_limit(user_id, feature):
    # Get user plan
    user = get_user(user_id)
    
    # Admin bypass
    if user.role in ['super_admin', 'admin']:
        return True
    
    # Get plan limits
    limits = PLAN_LIMITS[user.plan]
    
    # Get current usage
    usage = get_usage_counters(user_id, date=today())
    
    # Check token limit
    if usage.tokens_used >= limits['daily_tokens']:
        return False
    
    # Check feature-specific limit
    feature_key = f"{feature}_per_day"
    if feature_key in limits:
        feature_usage = getattr(usage, f"{feature}s_generated", 0)
        if feature_usage >= limits[feature_key]:
            return False
    
    # Check request limit
    if usage.requests_count >= limits['daily_requests']:
        return False
    
    return True
```

---

### Multi-Level Limiting

**Level 1: Token Limit**

Tracks: Total AI tokens consumed

Purpose: Control API costs

Example:
```
User sends message → Estimate tokens → Check limit
If tokens_used + estimated > daily_tokens:
    Reject with "Daily token limit reached"
```

**Level 2: Feature Limit**

Tracks: Specific feature usage

Purpose: Control expensive operations

Example:
```
User requests MCQ generation
Check mcqs_generated < mcqs_per_day
If exceeded:
    Reject with "Daily MCQ limit reached"
```

**Level 3: Request Limit**

Tracks: Total API requests

Purpose: Prevent abuse

Example:
```
Any API call
Check requests_count < daily_requests
If exceeded:
    Reject with "Daily request limit reached"
```

**All Three Must Pass**:
```python
def can_process_request(user_id, feature, estimated_tokens):
    return (
        check_token_limit(user_id, estimated_tokens) and
        check_feature_limit(user_id, feature) and
        check_request_limit(user_id)
    )
```

---

### Usage Tracking

**Counters Tracked**:
- `tokens_used`: Total AI tokens consumed
- `requests_count`: Total API requests made
- `pdf_uploads`: Number of PDFs uploaded
- `mcqs_generated`: Number of MCQs created
- `images_used`: Number of images analyzed
- `flashcards_generated`: Number of flashcards created

**Tracking Process**:
```
Request processed successfully
    ↓
Calculate tokens used
    ↓
Increment appropriate counters
    ↓
Update usage_counters table
    ↓
    INSERT INTO usage_counters (user_id, date, ...)
    VALUES (?, CURRENT_DATE, ...)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        tokens_used = usage_counters.tokens_used + ?,
        requests_count = usage_counters.requests_count + 1,
        ...
```

**Real-Time Updates**:
- Counters updated immediately after request
- No batching or delays
- Ensures accurate limit enforcement

---

### Daily Reset

**Reset Schedule**: Midnight UTC

**Implementation**:
```python
# Scheduled job (runs at 00:00 UTC)
def reset_daily_counters():
    # Option 1: Delete old records
    delete_usage_counters(date < today())
    
    # Option 2: Zero out counters
    update_usage_counters(
        date=yesterday(),
        set_all_to_zero=True
    )
    
    # Log reset
    log_system_event('daily_reset', timestamp=now())
```

**Scheduler**:
- FastAPI BackgroundTasks
- Or external cron job
- Or Supabase scheduled function

---

### Error Responses

**Token Limit Exceeded**:
```json
{
  "error": {
    "code": "TOKEN_LIMIT_EXCEEDED",
    "message": "You've reached your daily token limit of 10,000.",
    "details": {
      "limit": 10000,
      "used": 10000,
      "reset_at": "2024-01-02T00:00:00Z"
    },
    "action": "upgrade",
    "upgrade_url": "/pricing"
  }
}
```

**Feature Limit Exceeded**:
```json
{
  "error": {
    "code": "MCQ_LIMIT_EXCEEDED",
    "message": "You've reached your daily MCQ limit of 5.",
    "details": {
      "feature": "mcq",
      "limit": 5,
      "used": 5,
      "reset_at": "2024-01-02T00:00:00Z"
    },
    "action": "upgrade",
    "upgrade_url": "/pricing"
  }
}
```

**Request Limit Exceeded**:
```json
{
  "error": {
    "code": "REQUEST_LIMIT_EXCEEDED",
    "message": "You've reached your daily request limit of 20.",
    "details": {
      "limit": 20,
      "used": 20,
      "reset_at": "2024-01-02T00:00:00Z"
    },
    "action": "upgrade",
    "upgrade_url": "/pricing"
  }
}
```

---

### Admin Bypass

**Implementation**:
```python
def check_rate_limit(user_id, feature):
    user = get_user(user_id)
    
    # Admin bypass
    if user.role in ['super_admin', 'admin']:
        return True  # Skip all checks
    
    # Regular limit checks
    return check_limits(user_id, feature)
```

**Rationale**:
- Admins need unlimited access for testing
- Admins need access during maintenance
- Admins need to verify system functionality

**Audit**:
- Admin usage still tracked
- Logged separately for monitoring
- Not counted against limits

---

### Usage Analytics

**User Dashboard**:
- Current usage vs limits
- Usage history (last 7 days)
- Projected usage
- Upgrade recommendations

**Admin Dashboard**:
- Total platform usage
- Usage by plan
- Top users
- Quota burn rate
- Cost projections

**Metrics**:
- Average tokens per user
- Average requests per user
- Feature popularity
- Conversion rate (free → paid)


---

## Security Measures

### 1. Authentication Security

**Supabase Auth Integration**:
- Industry-standard authentication
- Secure password hashing (bcrypt)
- JWT tokens for session management
- Email verification
- Password reset flows

**Session Management**:
- HTTP-only cookies
- SameSite=Strict
- Secure flag in production
- Token expiration (configurable)
- Refresh token rotation

**Password Requirements**:
- Minimum 8 characters
- Complexity requirements (configurable)
- No common passwords
- Rate limiting on login attempts

---

### 2. Authorization Security

**Role-Based Access Control (RBAC)**:

Roles:
- `super_admin`: Full system access
- `admin`: User and key management
- `ops`: Operational monitoring
- `support`: User support functions
- `viewer`: Read-only access

**Admin Verification**:
```python
def verify_admin(user_id):
    # Check admin_allowlist
    user = get_user(user_id)
    allowlist_entry = query_admin_allowlist(email=user.email)
    
    if allowlist_entry and user.role in ADMIN_ROLES:
        return allowlist_entry.role
    
    # Emergency admin check
    if user.email == os.environ.get('SUPER_ADMIN_EMAIL'):
        return 'super_admin'
    
    return None
```

**Route Protection**:
- Admin routes require admin role
- User routes require authentication
- Public routes (login, register) unrestricted

---

### 3. Data Security

**Encryption at Rest**:

API Keys:
- Algorithm: AES-256-GCM
- Key storage: Environment variable
- Never logged or exposed

User Data:
- Supabase handles encryption
- Database-level encryption
- Backup encryption

**Encryption in Transit**:
- HTTPS only in production
- TLS 1.3
- Certificate pinning (optional)

**Row Level Security (RLS)**:

Users table:
```sql
-- Users can read own record
CREATE POLICY users_select_own ON users
  FOR SELECT USING (auth.uid() = id);

-- Admins can read all
CREATE POLICY users_select_admin ON users
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM admin_allowlist 
      WHERE email = (SELECT email FROM users WHERE id = auth.uid())
    )
  );
```

Documents table:
```sql
-- Users can only access own documents
CREATE POLICY documents_own ON documents
  FOR ALL USING (user_id = auth.uid());
```

---

### 4. Input Validation

**Backend Validation**:

Pydantic Models:
```python
from pydantic import BaseModel, EmailStr, constr

class UserRegistration(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    name: constr(min_length=1, max_length=100)

class ChatMessage(BaseModel):
    session_id: UUID
    content: constr(min_length=1, max_length=10000)
```

**SQL Injection Prevention**:
- Parameterized queries only
- Supabase client handles escaping
- No raw SQL from user input

**XSS Prevention**:
- Input sanitization
- Output encoding
- Content Security Policy headers

**File Upload Validation**:
- File type checking
- File size limits
- Virus scanning (optional)
- Secure file storage

---

### 5. Rate Limiting for Security

**Login Rate Limiting**:
- Max 5 attempts per IP per 15 minutes
- Exponential backoff
- Account lockout after 10 failed attempts

**API Rate Limiting**:
- Plan-based limits (see Rate Limiting section)
- IP-based limits for unauthenticated endpoints
- DDoS protection

**Admin Action Rate Limiting**:
- Prevent bulk operations abuse
- Require confirmation for destructive actions
- Audit all admin actions

---

### 6. API Key Security

**Storage**:
- Encrypted at rest (AES-256-GCM)
- Encryption key in environment
- Never in version control
- Never in logs

**Access**:
- Backend only
- Frontend never sees keys
- Admin UI shows masked (last 4 chars)

**Rotation**:
- Manual rotation by admins
- Audit trail for all changes
- Notifications on key changes

**Validation**:
- Test call before storage
- Format validation
- Provider verification

---

### 7. Audit Logging

**What's Logged**:
- All admin actions
- Authentication events
- Authorization failures
- API key operations
- Maintenance mode changes
- Feature toggles
- User plan changes
- Suspicious activity

**Log Format**:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "admin_id": "uuid",
  "admin_email": "admin@example.com",
  "action_type": "change_user_plan",
  "target_type": "user",
  "target_id": "user_uuid",
  "details": {
    "old_plan": "free",
    "new_plan": "pro",
    "reason": "customer support request"
  },
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0..."
}
```

**Retention**:
- Minimum 90 days
- Immutable (append-only)
- Searchable and filterable

---

### 8. CORS Configuration

**Production**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Development**:
```python
allow_origins=["http://localhost:3000"]  # Local frontend only
```

---

### 9. Error Handling Security

**Error Responses**:
- User-friendly messages
- No stack traces to users
- No internal details exposed
- Generic error codes

**Example**:
```json
// Bad (exposes internals)
{
  "error": "Database connection failed: Connection refused at 10.0.0.5:5432"
}

// Good (generic)
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An error occurred. Please try again later."
  }
}
```

**Logging**:
- Full details logged server-side
- Request ID for correlation
- Stack traces in logs only
- Sensitive data redacted

---

### 10. Secrets Management

**Environment Variables**:
- All secrets in environment
- Never in code
- Never in version control
- Different per environment

**Required Secrets**:
```bash
# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Encryption
ENCRYPTION_KEY=...  # 32-byte key for AES-256

# Admin
SUPER_ADMIN_EMAIL=admin@example.com

# Notifications
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...

# Payments (optional)
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
```

**Production Deployment**:
- Heroku config vars
- Netlify environment variables
- Never commit .env files
- Use .env.example for templates

---

### 11. Security Headers

**Recommended Headers**:
```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Trust only specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

### 12. Monitoring and Alerting

**Security Monitoring**:
- Failed login attempts
- Admin action anomalies
- Unusual usage patterns
- API key failures
- Unauthorized access attempts

**Alerts**:
- Email for critical events
- Webhook for integrations
- SMS for emergencies (optional)

**Incident Response**:
- Documented procedures
- Admin contact list
- Escalation paths
- Recovery playbooks


---

## Development Guide

### Local Setup

**Prerequisites**:
- Python 3.11+
- Node.js 18+
- Git
- Supabase account (or local Supabase)

**Backend Setup**:

```bash
# Clone repository
git clone <repository-url>
cd medical-ai-platform

# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required variables:
# - DATABASE_URL
# - SUPABASE_URL
# - SUPABASE_KEY
# - ENCRYPTION_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
# - SUPER_ADMIN_EMAIL

# Run database migrations (if any)
# Set up Supabase tables using database/schema.sql

# Run backend
uvicorn main:app --reload

# Backend now running at http://localhost:8000
```

**Frontend Setup**:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local

# Edit .env.local
# Required variables:
# - NEXT_PUBLIC_API_URL=http://localhost:8000
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY

# Run frontend
npm run dev

# Frontend now running at http://localhost:3000
```

**Database Setup**:

```bash
# Option 1: Supabase Cloud
# 1. Create project at supabase.com
# 2. Run SQL from database/schema.sql in SQL Editor
# 3. Run SQL from database/rls_policies.sql
# 4. Add your email to admin_allowlist table

# Option 2: Local Supabase
# 1. Install Supabase CLI
# 2. supabase init
# 3. supabase start
# 4. Run migrations
```

---

### Development Workflow

**1. Feature Development**:

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# - Backend: backend/services/
# - Frontend: frontend/components/, frontend/pages/
# - Tests: backend/tests/, frontend/tests/

# Run tests
cd backend
pytest

cd frontend
npm test

# Commit changes
git add .
git commit -m "Add feature: description"

# Push and create PR
git push origin feature/your-feature-name
```

**2. Testing**:

```bash
# Backend tests
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run property tests only
pytest tests/property/ -m property_test

# Frontend tests
cd frontend

# Run all tests
npm test

# Run specific test
npm test -- ChatWindow.test.tsx

# Run with coverage
npm test -- --coverage
```

**3. Code Quality**:

```bash
# Backend linting
cd backend
flake8 .
black .
mypy .

# Frontend linting
cd frontend
npm run lint
npm run format
```

---

### Project Structure

```
medical-ai-platform/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── services/               # Business logic services
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── commands.py
│   │   ├── rate_limiter.py
│   │   ├── model_router.py
│   │   ├── health_monitor.py
│   │   ├── maintenance.py
│   │   ├── admin.py
│   │   ├── documents.py
│   │   ├── notifications.py
│   │   ├── clinical.py
│   │   ├── study_planner.py
│   │   ├── payments.py
│   │   └── encryption.py
│   ├── middleware/             # FastAPI middleware
│   │   ├── admin_auth.py
│   │   ├── maintenance.py
│   │   └── feature_toggle.py
│   ├── tests/                  # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── property/
│   ├── database/               # Database scripts
│   │   ├── schema.sql
│   │   └── rls_policies.sql
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment template
│   └── pytest.ini             # Pytest configuration
│
├── frontend/
│   ├── pages/                  # Next.js pages
│   │   ├── index.tsx          # Login/register
│   │   ├── chat.tsx           # Main chat interface
│   │   ├── documents.tsx      # Document management
│   │   ├── profile.tsx        # User profile
│   │   └── admin/             # Admin panel pages
│   ├── components/             # React components
│   │   ├── ChatWindow.tsx
│   │   ├── ChatInput.tsx
│   │   ├── SessionSidebar.tsx
│   │   ├── AdminLayout.tsx
│   │   └── ...
│   ├── lib/                    # Utilities
│   │   └── supabase.ts        # Supabase client
│   ├── tests/                  # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── property/
│   ├── package.json            # Node dependencies
│   ├── .env.local.example     # Environment template
│   └── tsconfig.json          # TypeScript config
│
├── .kiro/                      # Spec files
│   └── specs/
│       └── medical-ai-platform/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
│
├── SYSTEM_GUIDE.md            # This file
└── README.md                  # Project overview
```

---

### Common Development Tasks

**Add New Service**:

1. Create service file: `backend/services/new_service.py`
2. Implement service functions
3. Add tests: `backend/tests/unit/test_new_service.py`
4. Import in `main.py`
5. Create API endpoints if needed

**Add New Feature**:

1. Update requirements.md (if needed)
2. Update design.md (if needed)
3. Implement backend service
4. Create API endpoints
5. Implement frontend components
6. Add tests (unit + property)
7. Update this guide

**Add New Admin Control**:

1. Add function to `admin.py`
2. Add API endpoint in `main.py`
3. Add UI component in `frontend/components/`
4. Add page in `frontend/pages/admin/`
5. Add audit logging
6. Add tests

**Add New Provider**:

1. Create provider file: `backend/services/providers/new_provider.py`
2. Implement provider-specific formatting
3. Add to model router
4. Add health check logic
5. Update admin UI for key management
6. Add tests

---

### Debugging

**Backend Debugging**:

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")

# Use debugger
import pdb; pdb.set_trace()

# Or use VS Code debugger
# Add breakpoint in IDE
```

**Frontend Debugging**:

```typescript
// Console logging
console.log('Debug:', variable);
console.error('Error:', error);

// React DevTools
// Install browser extension

// Network debugging
// Use browser DevTools Network tab
```

**Database Debugging**:

```sql
-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'users';

-- Check user data
SELECT * FROM users WHERE email = 'test@example.com';

-- Check usage counters
SELECT * FROM usage_counters WHERE user_id = 'uuid';

-- Check API keys (encrypted)
SELECT id, provider, feature, status, priority FROM api_keys;
```

---

### Environment Variables Reference

**Backend (.env)**:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Encryption
ENCRYPTION_KEY=64-char-hex-string

# Admin
SUPER_ADMIN_EMAIL=admin@example.com

# Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Payments (optional)
RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx

# Environment
ENVIRONMENT=development  # or production
```

**Frontend (.env.local)**:

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```


---

## Deployment Guide

### Pre-Deployment Checklist

**Local Testing**:
- [ ] All unit tests passing
- [ ] All property tests passing (100+ iterations)
- [ ] All integration tests passing
- [ ] Manual testing of critical flows
- [ ] Admin panel fully functional
- [ ] Rate limiting working
- [ ] Maintenance mode tested
- [ ] API key pool tested
- [ ] Error handling verified

**Security**:
- [ ] All secrets in environment variables
- [ ] No secrets in code or version control
- [ ] HTTPS configured
- [ ] CORS properly configured
- [ ] RLS policies active
- [ ] Admin access verified
- [ ] Audit logging working

**Documentation**:
- [ ] README.md updated
- [ ] API documentation complete
- [ ] Admin guide written
- [ ] Environment variables documented

---

### Production Deployment

**Phase 1: Database (Supabase Cloud)**

1. Create Production Project:
```bash
# Go to supabase.com
# Create new project
# Note: URL and keys
```

2. Run Migrations:
```sql
-- In Supabase SQL Editor
-- Run database/schema.sql
-- Run database/rls_policies.sql
```

3. Configure:
```sql
-- Add admin to allowlist
INSERT INTO admin_allowlist (email, role)
VALUES ('your-email@example.com', 'super_admin');

-- Verify RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

4. Connection Pooling:
```
-- In Supabase Dashboard
-- Settings → Database
-- Enable connection pooling
-- Note: Pooler URL
```

---

**Phase 2: Backend (Heroku)**

1. Create Heroku App:
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Add to git remote
git remote add heroku https://git.heroku.com/your-app-name.git
```

2. Configure Environment:
```bash
# Set all environment variables
heroku config:set DATABASE_URL=postgresql://...
heroku config:set SUPABASE_URL=https://...
heroku config:set SUPABASE_KEY=...
heroku config:set ENCRYPTION_KEY=...
heroku config:set SUPER_ADMIN_EMAIL=...
heroku config:set ENVIRONMENT=production

# Optional: Notifications
heroku config:set SMTP_HOST=...
heroku config:set SMTP_USER=...
heroku config:set SMTP_PASSWORD=...

# Optional: Payments
heroku config:set RAZORPAY_KEY_ID=...
heroku config:set RAZORPAY_KEY_SECRET=...
```

3. Create Procfile:
```bash
# backend/Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

4. Deploy:
```bash
# Push to Heroku
git subtree push --prefix backend heroku main

# Or if using monorepo:
git push heroku main

# Check logs
heroku logs --tail

# Verify health
curl https://your-app-name.herokuapp.com/api/health
```

---

**Phase 3: Frontend (Netlify)**

1. Create Netlify Site:
```bash
# Go to netlify.com
# New site from Git
# Connect repository
# Or use Netlify CLI:
npm install -g netlify-cli
netlify login
netlify init
```

2. Configure Build:
```
Build command: npm run build
Publish directory: .next
```

3. Environment Variables:
```bash
# In Netlify Dashboard → Site settings → Environment variables
NEXT_PUBLIC_API_URL=https://your-app-name.herokuapp.com
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key
```

4. Deploy:
```bash
# Automatic deployment on git push
git push origin main

# Or manual deploy
cd frontend
npm run build
netlify deploy --prod
```

---

**Phase 4: Optional CDN (Cloudflare)**

1. Add Domain to Cloudflare:
```
# Go to cloudflare.com
# Add site
# Update nameservers at domain registrar
```

2. Configure DNS:
```
# A record for backend
your-api.domain.com → Heroku IP

# CNAME for frontend
www.domain.com → your-netlify-site.netlify.app
domain.com → your-netlify-site.netlify.app
```

3. SSL/TLS:
```
# In Cloudflare Dashboard
# SSL/TLS → Full (strict)
# Edge Certificates → Always Use HTTPS
```

4. Caching Rules:
```
# Cache static assets
# Bypass cache for API calls
# Set appropriate TTLs
```

---

### Post-Deployment Verification

**1. Health Checks**:
```bash
# Backend health
curl https://your-api.domain.com/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**2. Authentication Flow**:
- Register new user
- Verify email (if enabled)
- Login
- Access chat interface
- Verify token in requests

**3. Admin Access**:
- Login with admin email
- Access admin panel
- Verify all admin features
- Check audit logs

**4. API Key Management**:
- Add test API key
- Verify encryption
- Test key selection
- Verify health monitoring

**5. Rate Limiting**:
- Test free plan limits
- Verify limit enforcement
- Test upgrade flow
- Verify admin bypass

**6. Maintenance Mode**:
- Trigger soft maintenance
- Verify banner display
- Trigger hard maintenance
- Verify lock screen
- Test admin override

**7. Error Handling**:
- Test invalid inputs
- Test rate limit errors
- Test maintenance errors
- Verify error messages

---

### Monitoring Setup

**1. Uptime Monitoring**:
```
# Use services like:
# - UptimeRobot
# - Pingdom
# - StatusCake

# Monitor endpoints:
# - https://your-api.domain.com/api/health
# - https://your-frontend.domain.com
```

**2. Error Tracking**:
```python
# Backend: Sentry integration
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment="production",
)
```

**3. Log Aggregation**:
```bash
# Heroku logs
heroku logs --tail

# Or use log aggregation service:
# - Papertrail
# - Loggly
# - Datadog
```

**4. Performance Monitoring**:
```
# Monitor:
# - Response times
# - Error rates
# - Database query performance
# - API provider latency
```

---

### Backup and Recovery

**Database Backups**:
```
# Supabase automatic backups
# Settings → Database → Backups
# Configure retention period
# Test restore procedure
```

**Code Backups**:
```bash
# Git repository
# Ensure pushed to remote
git push origin main

# Tag releases
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

**Environment Backups**:
```bash
# Export Heroku config
heroku config --shell > .env.production.backup

# Export Netlify config
netlify env:list > .env.frontend.backup

# Store securely (not in git!)
```

---

### Scaling Considerations

**Horizontal Scaling**:
```
# Heroku dynos
heroku ps:scale web=2

# Or use auto-scaling
# Heroku Dashboard → Resources → Configure Dynos
```

**Database Scaling**:
```
# Supabase
# Upgrade plan for more resources
# Enable connection pooling
# Add read replicas (if needed)
```

**CDN Scaling**:
```
# Cloudflare automatically scales
# Configure caching for static assets
# Use Workers for edge computing (optional)
```

**Future: Kubernetes**:
```yaml
# Prepared for future migration
# See design.md for K8s architecture
# Containerize with Docker
# Deploy to GKE/EKS/AKS
```

---

### Rollback Procedure

**Backend Rollback**:
```bash
# Heroku rollback
heroku releases
heroku rollback v123

# Or redeploy previous version
git checkout v1.0.0
git push heroku main --force
```

**Frontend Rollback**:
```bash
# Netlify rollback
# Dashboard → Deploys → Previous deploy → Publish

# Or redeploy
git checkout v1.0.0
netlify deploy --prod
```

**Database Rollback**:
```sql
-- Restore from backup
-- Supabase Dashboard → Database → Backups → Restore
```

---

### Maintenance Windows

**Planned Maintenance**:
1. Announce maintenance window
2. Enable maintenance mode
3. Perform updates
4. Test thoroughly
5. Disable maintenance mode
6. Monitor for issues

**Emergency Maintenance**:
1. Automatic maintenance triggered
2. Admin notified
3. Investigate issue
4. Apply fix
5. Override maintenance
6. Monitor recovery

---

## Conclusion

This guide provides comprehensive documentation for the Medical AI Platform. For questions or issues:

1. Check this guide first
2. Review spec files (.kiro/specs/)
3. Check code comments
4. Review test files for examples
5. Contact system administrator

**Key Principles to Remember**:
- Scarcity-first: Design for failure
- Backend authority: All logic server-side
- Admin control: Manual management
- Graceful degradation: Maintenance over silent failure
- Local-first: Test locally before deploying

**Next Steps**:
- Complete local development
- Run all tests
- Deploy to production
- Monitor and iterate
- Scale as needed

---

*Last Updated: 2024-01-01*
*Version: 1.0.0*
