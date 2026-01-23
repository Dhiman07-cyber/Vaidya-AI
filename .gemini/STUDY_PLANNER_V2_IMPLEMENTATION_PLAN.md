# Study Planner V2 - Premium Scheduling Engine Implementation Plan

## Executive Summary

This document provides the complete implementation plan for the Study Planner V2 scheduling engine with:
- Day-only temporary swaps (IDEA 1)
- Multi-slot allocation (IDEA 2)
- Ad-hoc completion (IDEA 3)
- Flexible start/continue (IDEA 4)
- Full concurrency, audit, and idempotency support

---

## Part 1: Database Migrations

### 1.1 New Tables Required

We need exactly **3 new tables** to support the scheduling engine:

| Table | Purpose |
|-------|---------|
| `study_plan_entry_versions` | Audit trail for undo, metrics, and compliance |
| `session_swap_requests` | Workflow state for swap/replace operations |
| `session_overrides` | Ephemeral day-only overrides without mutating templates |

### 1.2 Migration SQL

```sql
-- ============================================================================
-- STUDY PLANNER V2 - SCHEDULING ENGINE MIGRATIONS
-- Run after COMPLETE_DATABASE_SCHEMA.sql
-- ============================================================================

-- 1. Audit & Version History Table
-- Purpose: Track every mutation for undo capability and audit compliance
CREATE TABLE IF NOT EXISTS public.study_plan_entry_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entry_id UUID NOT NULL REFERENCES public.study_plan_entries(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  action TEXT NOT NULL CHECK(action IN (
    'create', 'update', 'delete', 'reschedule', 'skip', 
    'complete', 'swap', 'split', 'override_apply', 'override_remove',
    'start', 'continue_now', 'manual_complete'
  )),
  actor TEXT NOT NULL CHECK(actor IN ('user', 'system', 'ai')),
  reason TEXT,
  payload_before JSONB,
  payload_after JSONB,
  client_request_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_entry_versions_entry_id ON public.study_plan_entry_versions(entry_id);
CREATE INDEX idx_entry_versions_user_created ON public.study_plan_entry_versions(user_id, created_at DESC);
CREATE INDEX idx_entry_versions_client_request ON public.study_plan_entry_versions(user_id, client_request_id) 
  WHERE client_request_id IS NOT NULL;

-- 2. Session Swap Requests Table
-- Purpose: Manage swap/replace workflow with preview → confirm → apply states
CREATE TABLE IF NOT EXISTS public.session_swap_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  missed_entry_id UUID NOT NULL REFERENCES public.study_plan_entries(id) ON DELETE CASCADE,
  target_entry_id UUID REFERENCES public.study_plan_entries(id) ON DELETE SET NULL,
  target_date DATE,
  target_start_time TIME,
  target_end_time TIME,
  strategy TEXT NOT NULL CHECK(strategy IN (
    'swap', 'replace_and_reschedule_target', 'split_if_needed', 
    'temporary_day_only', 'force_replace'
  )),
  is_temporary BOOLEAN NOT NULL DEFAULT false,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
    'pending', 'previewed', 'applied', 'rejected', 'expired', 'cancelled'
  )),
  preview_payload JSONB,
  resolution JSONB,
  client_request_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  applied_at TIMESTAMPTZ
);

CREATE INDEX idx_swap_requests_user_status ON public.session_swap_requests(user_id, status);
CREATE INDEX idx_swap_requests_expires ON public.session_swap_requests(expires_at) WHERE status = 'pending';
CREATE INDEX idx_swap_requests_client_request ON public.session_swap_requests(user_id, client_request_id)
  WHERE client_request_id IS NOT NULL;

-- 3. Session Overrides Table  
-- Purpose: Day-only temporary overrides that don't mutate templates
CREATE TABLE IF NOT EXISTS public.session_overrides (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  override_date DATE NOT NULL,
  original_entry_id UUID NOT NULL REFERENCES public.study_plan_entries(id) ON DELETE CASCADE,
  override_type TEXT NOT NULL CHECK(override_type IN (
    'swap', 'replace', 'skip', 'extend', 'split', 'ad_hoc'
  )),
  override_payload JSONB NOT NULL,
  swap_target_entry_id UUID REFERENCES public.study_plan_entries(id) ON DELETE SET NULL,
  applied BOOLEAN NOT NULL DEFAULT false,
  completed BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  cleanup_policy TEXT NOT NULL DEFAULT 'auto' CHECK(cleanup_policy IN ('auto', 'manual'))
);

CREATE INDEX idx_session_overrides_user_date ON public.session_overrides(user_id, override_date);
CREATE INDEX idx_session_overrides_original_entry ON public.session_overrides(original_entry_id);
CREATE INDEX idx_session_overrides_cleanup ON public.session_overrides(expires_at, applied) 
  WHERE cleanup_policy = 'auto';

-- 4. Idempotency Keys Table (for operations beyond swap requests)
CREATE TABLE IF NOT EXISTS public.idempotency_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  client_request_id TEXT NOT NULL,
  operation TEXT NOT NULL,
  request_hash TEXT,
  response_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
  UNIQUE(user_id, client_request_id, operation)
);

CREATE INDEX idx_idempotency_keys_expires ON public.idempotency_keys(expires_at);

-- 5. Add timezone column to users if not exists
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'timezone'
  ) THEN
    ALTER TABLE public.users ADD COLUMN timezone TEXT DEFAULT 'Asia/Kolkata';
  END IF;
END $$;

-- 6. Add is_generated_instance column to study_plan_entries if not exists
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'study_plan_entries' AND column_name = 'is_generated_instance'
  ) THEN
    ALTER TABLE public.study_plan_entries ADD COLUMN is_generated_instance BOOLEAN DEFAULT false;
  END IF;
END $$;

-- 7. Add actual_duration_minutes column for manual completion tracking
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'study_plan_entries' AND column_name = 'actual_duration_minutes'
  ) THEN
    ALTER TABLE public.study_plan_entries ADD COLUMN actual_duration_minutes INTEGER;
  END IF;
END $$;

-- 8. Enable RLS on new tables
ALTER TABLE public.study_plan_entry_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_swap_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;

-- 9. RLS Policies for new tables
CREATE POLICY entry_versions_select_own ON public.study_plan_entry_versions 
  FOR SELECT USING (user_id = auth.uid());
CREATE POLICY entry_versions_insert_own ON public.study_plan_entry_versions 
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY swap_requests_select_own ON public.session_swap_requests 
  FOR SELECT USING (user_id = auth.uid());
CREATE POLICY swap_requests_insert_own ON public.session_swap_requests 
  FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY swap_requests_update_own ON public.session_swap_requests 
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY session_overrides_select_own ON public.session_overrides 
  FOR SELECT USING (user_id = auth.uid());
CREATE POLICY session_overrides_insert_own ON public.session_overrides 
  FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY session_overrides_update_own ON public.session_overrides 
  FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY session_overrides_delete_own ON public.session_overrides 
  FOR DELETE USING (user_id = auth.uid());

CREATE POLICY idempotency_keys_all_own ON public.idempotency_keys 
  FOR ALL USING (user_id = auth.uid());

-- 10. Updated_at triggers for new tables
CREATE TRIGGER update_swap_requests_updated_at 
  BEFORE UPDATE ON public.session_swap_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Part 2: Core Backend Service Architecture

### 2.1 File Structure

```
backend/services/
├── study_planner_v2/
│   ├── __init__.py
│   ├── scheduler.py           # Main scheduling engine
│   ├── conflict_detector.py   # Overlap detection
│   ├── swap_manager.py        # Swap/replace operations
│   ├── override_manager.py    # Day-only overrides
│   ├── session_manager.py     # Start/continue/complete
│   ├── multi_slot_allocator.py  # Multi-hour allocation
│   ├── audit_logger.py        # Version tracking
│   ├── calendar_renderer.py   # Merge entries + overrides
│   ├── models.py              # Pydantic models
│   └── constants.py           # Configuration
```

### 2.2 Core Constants

```python
# backend/services/study_planner_v2/constants.py

SLOT_UNIT_MINUTES = 60  # 1-hour slots
MAX_SEARCH_WINDOW_DAYS = 14  # For overflow scheduling
ADVISORY_LOCK_TIMEOUT_MS = 5000
MAX_CONCURRENT_SESSIONS = 1  # Per user at a time
OVERRIDE_EXPIRY_HOURS = 36  # Cleanup after 1.5 days
VERSION_RETENTION_MONTHS = 12
```

---

## Part 3: API Endpoints Specification

### 3.1 Session Management APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/sessions` | POST | Create session (idempotent) |
| `/v1/sessions/{id}` | PATCH | Update single session |
| `/v1/sessions/{id}` | DELETE | Delete session |
| `/v1/sessions/{id}/start` | POST | Start session now |
| `/v1/sessions/{id}/continue_now` | POST | Continue remaining time |
| `/v1/sessions/{id}/mark_completed` | POST | Manual completion |

### 3.2 Swap/Replace APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/sessions/{id}/preview-swap` | POST | Generate swap preview |
| `/v1/session_swap_requests/{id}/apply` | POST | Apply previewed swap |
| `/v1/sessions/{missed_id}/replace` | POST | Quick replace flow |

### 3.3 Multi-slot APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/sessions/allocate_multislot` | POST | Allocate contiguous hours |
| `/v1/sessions/{id}/split` | POST | Split long session |

### 3.4 Calendar APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/calendar` | GET | Merged view (entries + overrides) |
| `/v1/calendar/availability` | GET | Check slot availability |

---

## Part 4: Core Transaction Patterns

### 4.1 Advisory Lock Pattern

```python
async def with_user_lock(self, user_id: str, operation):
    """Execute operation with per-user advisory lock"""
    async with self.db.transaction() as tx:
        # Acquire advisory lock
        await tx.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            str(user_id)
        )
        return await operation(tx)
```

### 4.2 Overlap Detection Query

```sql
-- Canonical overlap detection
SELECT id, subject, start_time, end_time, status
FROM public.study_plan_entries
WHERE user_id = :user_id
  AND scheduled_date = :date
  AND status IN ('planned', 'in_progress')
  AND NOT (end_time <= :start_time OR start_time >= :end_time)
FOR UPDATE;
```

### 4.3 Idempotency Check

```python
async def check_idempotency(self, user_id: str, client_request_id: str, operation: str):
    """Return cached response if request already processed"""
    result = await self.db.query(
        """SELECT response_payload FROM idempotency_keys 
           WHERE user_id = $1 AND client_request_id = $2 AND operation = $3
           AND expires_at > NOW()""",
        user_id, client_request_id, operation
    )
    return result[0]['response_payload'] if result else None
```

---

## Part 5: Key Flow Implementations

### 5.1 Day-Only Temporary Swap Flow

```
User clicks "Swap Today Only" for missed Math (9-10) with Science (10-11)
    │
    ▼
POST /v1/sessions/{math_id}/preview-swap
    ├─ Acquire advisory lock
    ├─ SELECT ... FOR UPDATE on both entries
    ├─ Validate entries exist and are swappable
    ├─ Generate preview diff
    └─ Create session_swap_requests (status='previewed')
    │
    ▼
User reviews preview modal
    │
    ▼
POST /v1/session_swap_requests/{id}/apply
    ├─ Acquire advisory lock
    ├─ Verify swap_request still valid
    ├─ Create session_overrides for today:
    │   ├─ Override 1: Math slot → Science content
    │   └─ Override 2: Science slot → Math content
    ├─ Update swap_request status='applied'
    ├─ Write study_plan_entry_versions (audit)
    └─ Return success + override details
    │
    ▼
Calendar renders today with overrides
    │
    ▼
User completes swapped sessions
    ├─ Mark original entries with completed_at
    ├─ Write audit versions
    └─ Mark overrides as completed
    │
    ▼
Next day: Calendar shows original layout with completion ticks
```

### 5.2 Continue Now Flow

```
User clicks "Continue Now" at 9:20 for 9:00-10:00 Math
    │
    ▼
POST /v1/sessions/{id}/continue_now
    ├─ Acquire advisory lock
    ├─ Calculate: elapsed = 20min, remaining = 40min
    ├─ If remaining <= 0: return error with mark_completed suggestion
    ├─ Check for conflicts in remaining time window
    ├─ Create child instance:
    │   ├─ parent_entry_id = original entry
    │   ├─ start_time = NOW
    │   ├─ end_time = NOW + 40min
    │   ├─ is_generated_instance = true
    │   └─ status = 'in_progress'
    ├─ Write audit version
    └─ Return child instance
```

### 5.3 Multi-Slot Allocation Flow

```
User requests 2-hour Math block starting at 9:00
    │
    ▼
POST /v1/sessions/allocate_multislot
    ├─ Acquire advisory lock
    ├─ Check slots 9:00-10:00 and 10:00-11:00
    │   ├─ Both free → Create single entry (9:00-11:00)
    │   └─ Partial → Return 409 with per-slot availability
    ├─ Write audit version
    └─ Return created entry or availability report
```

---

## Part 6: Calendar Rendering Rules

```python
async def get_calendar(self, user_id: str, start: date, end: date):
    # 1. Get all entries in range
    entries = await self.get_entries(user_id, start, end)
    
    # 2. Get active overrides in range
    overrides = await self.get_overrides(user_id, start, end)
    
    # 3. Build override map by date and original_entry_id
    override_map = {}
    for override in overrides:
        key = (override['override_date'], override['original_entry_id'])
        override_map[key] = override
    
    # 4. Merge entries with overrides
    result = []
    for entry in entries:
        key = (entry['scheduled_date'], entry['id'])
        if key in override_map:
            # Apply override payload instead of original
            override = override_map[key]
            rendered = self.apply_override(entry, override)
            rendered['is_temporary_swap'] = True
        else:
            rendered = entry
            rendered['is_temporary_swap'] = False
        result.append(rendered)
    
    return result
```

---

## Part 7: Error Codes & Messages

| Code | Error | User Message |
|------|-------|--------------|
| 409 | CONFLICT_DETECTED | "This slot conflicts with {subject} from {time}. Choose another time or swap." |
| 409 | PARTIAL_AVAILABILITY | "Slot 1 available, Slot 2 occupied by {subject}. Split or choose another time." |
| 400 | NO_REMAINING_TIME | "Session time has passed. Would you like to mark it as completed?" |
| 400 | INVALID_SWAP_TARGET | "Cannot swap with an in-progress or completed session." |
| 404 | ENTRY_NOT_FOUND | "Study session not found or access denied." |
| 409 | CONCURRENT_MODIFICATION | "This session was modified. Please refresh and try again." |
| 429 | TOO_MANY_SWAPS | "Maximum swap limit reached for today. Try again tomorrow." |

---

## Part 8: Frontend Components Required

1. **SwapPreviewModal** - Shows before/after with "TEMPORARY" badge
2. **ContinueNowDialog** - Shows remaining time and options
3. **MultiSlotAllocator** - Visual slot selection with availability
4. **MarkCompletedDialog** - Manual completion with duration input
5. **ConflictResolutionPanel** - Shows conflicts with resolution options

---

## Part 9: Rollout Checklist

- [ ] Deploy migrations to staging
- [ ] Update COMPLETE_DATABASE_SCHEMA.sql
- [ ] Implement backend services behind `planner_v2` feature flag
- [ ] Enable preview-only flows first
- [ ] Run property-based concurrency tests
- [ ] Enable apply for small cohort
- [ ] Monitor conflict metrics
- [ ] Progressive rollout
- [ ] Remove old code after validation

---

## Part 10: Test Requirements Summary

1. **Unit Tests**: Overlap detection, slot-finding, split logic
2. **Integration Tests**: Temporary swap flow, continue_now, multi-slot
3. **Concurrency Tests**: 200 concurrent creates, concurrent swaps
4. **E2E Tests**: Preview flows, ad-hoc start, force-create

---

*Next: See STUDY_PLANNER_V2_BACKEND_CODE.py for implementation*
