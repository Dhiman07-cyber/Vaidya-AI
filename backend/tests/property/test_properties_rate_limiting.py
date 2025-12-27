"""
Property-based tests for rate limiting service
Tests universal properties that should hold for all valid inputs
Requirements: 9.2, 9.3, 9.5, 9.6
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock
from datetime import date
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.rate_limiter import RateLimiter, PLAN_LIMITS


# Custom strategies for generating valid test data
@st.composite
def valid_user_id(draw):
    """Generate valid UUID-like user IDs"""
    return draw(st.uuids()).hex


@st.composite
def valid_plan(draw):
    """Generate valid user plans"""
    return draw(st.sampled_from(['free', 'student', 'pro', 'admin']))


@st.composite
def valid_admin_role(draw):
    """Generate valid admin roles"""
    return draw(st.sampled_from(['super_admin', 'admin', 'ops', 'support', 'viewer']))


@st.composite
def valid_feature(draw):
    """Generate valid feature names"""
    return draw(st.sampled_from(['chat', 'mcq', 'flashcard', 'pdf', 'image']))


@st.composite
def valid_usage_data(draw, plan):
    """Generate valid usage data within or exceeding plan limits"""
    limits = PLAN_LIMITS[plan]
    
    # Generate usage that might be within or over limits
    return {
        'tokens_used': draw(st.integers(min_value=0, max_value=int(limits['daily_tokens'] * 1.5) if limits['daily_tokens'] != float('inf') else 100000)),
        'requests_count': draw(st.integers(min_value=0, max_value=int(limits['daily_requests'] * 1.5) if limits['daily_requests'] != float('inf') else 1000)),
        'pdf_uploads': draw(st.integers(min_value=0, max_value=int(limits['pdf_uploads'] * 1.5) if limits['pdf_uploads'] != float('inf') else 100)),
        'mcqs_generated': draw(st.integers(min_value=0, max_value=int(limits['mcqs_per_day'] * 1.5) if limits['mcqs_per_day'] != float('inf') else 500)),
        'images_used': draw(st.integers(min_value=0, max_value=int(limits['images_per_day'] * 1.5) if limits['images_per_day'] != float('inf') else 100)),
        'flashcards_generated': draw(st.integers(min_value=0, max_value=int(limits['flashcards_per_day'] * 1.5) if limits['flashcards_per_day'] != float('inf') else 1000)),
    }


# Feature: medical-ai-platform, Property 21: Rate limits are checked before processing
@given(
    user_id=valid_user_id(),
    plan=valid_plan(),
    feature=valid_feature(),
    role=st.one_of(st.none(), valid_admin_role()),
    data=st.data()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_rate_limits_checked_before_processing(user_id, plan, feature, role, data):
    """
    Property 21: For any user request, the system should check current usage 
    against plan limits before processing the request.
    
    Validates: Requirements 9.2
    """
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Mock user table response
    user_data = {
        "plan": plan,
        "role": role
    }
    mock_user_response = MagicMock()
    mock_user_response.data = [user_data]
    
    # Generate usage data for this plan using st.data()
    usage_data = data.draw(valid_usage_data(plan))
    
    # Mock usage_counters table response
    mock_usage_response = MagicMock()
    mock_usage_response.data = [{
        "id": "usage-id-123",
        "user_id": user_id,
        "date": str(date.today()),
        **usage_data
    }]
    
    # Set up mock table calls
    def mock_table_select(table_name):
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_eq2 = MagicMock()
        
        if table_name == "users":
            mock_eq.execute.return_value = mock_user_response
            mock_select.eq.return_value = mock_eq
        elif table_name == "usage_counters":
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq
        
        mock_table.select.return_value = mock_select
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_select
    
    # Create rate limiter with mock client
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit(user_id, feature)
    
    # Property: Rate limit check should always return a boolean
    assert isinstance(result, bool), f"Rate limit check should return boolean, got {type(result)}"
    
    # Property: The check should have queried the user table
    assert any(call[0][0] == "users" for call in mock_supabase.table.call_args_list), \
        "Rate limit check should query users table"
    
    # Property: The check should have queried usage_counters table (unless admin bypass)
    if role not in ["super_admin", "admin", "ops"]:
        assert any(call[0][0] == "usage_counters" for call in mock_supabase.table.call_args_list), \
            "Rate limit check should query usage_counters table for non-admin users"


# Feature: medical-ai-platform, Property 22: Requests over limit are rejected
@given(
    user_id=valid_user_id(),
    plan=st.sampled_from(['free', 'student', 'pro']),  # Exclude admin (infinite limits)
    feature=valid_feature()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_requests_over_limit_rejected(user_id, plan, feature):
    """
    Property 22: For any user request that would exceed plan limits, 
    the request should be rejected with a clear error message.
    
    Validates: Requirements 9.3
    """
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Mock user table response (non-admin user)
    user_data = {
        "plan": plan,
        "role": None
    }
    mock_user_response = MagicMock()
    mock_user_response.data = [user_data]
    
    # Get plan limits
    limits = PLAN_LIMITS[plan]
    
    # Create usage data that EXCEEDS limits
    # We'll exceed at least one limit to ensure rejection
    usage_data = {
        'tokens_used': int(limits['daily_tokens'] + 1),  # Over token limit
        'requests_count': int(limits['daily_requests'] + 1),  # Over request limit
        'pdf_uploads': int(limits['pdf_uploads'] + 1) if limits['pdf_uploads'] > 0 else 0,
        'mcqs_generated': int(limits['mcqs_per_day'] + 1) if limits['mcqs_per_day'] > 0 else 0,
        'images_used': int(limits['images_per_day'] + 1) if limits['images_per_day'] > 0 else 0,
        'flashcards_generated': int(limits['flashcards_per_day'] + 1) if limits['flashcards_per_day'] > 0 else 0,
    }
    
    # Mock usage_counters table response
    mock_usage_response = MagicMock()
    mock_usage_response.data = [{
        "id": "usage-id-123",
        "user_id": user_id,
        "date": str(date.today()),
        **usage_data
    }]
    
    # Set up mock table calls
    def mock_table_select(table_name):
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_eq2 = MagicMock()
        
        if table_name == "users":
            mock_eq.execute.return_value = mock_user_response
            mock_select.eq.return_value = mock_eq
        elif table_name == "usage_counters":
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq
        
        mock_table.select.return_value = mock_select
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_select
    
    # Create rate limiter with mock client
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit(user_id, feature)
    
    # Property: Request should be rejected (return False) when over limit
    assert result is False, \
        f"Request should be rejected when usage exceeds limits. Plan: {plan}, Usage: {usage_data}, Limits: {limits}"


# Feature: medical-ai-platform, Property 24: Admin users bypass rate limits
@given(
    user_id=valid_user_id(),
    plan=valid_plan(),
    admin_role=st.sampled_from(['super_admin', 'admin', 'ops']),  # Admin roles that bypass
    feature=valid_feature()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_admin_users_bypass_rate_limits(user_id, plan, admin_role, feature):
    """
    Property 24: For any user with admin role, requests should never be 
    rejected due to rate limits.
    
    Validates: Requirements 9.5
    """
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Mock user table response with admin role
    user_data = {
        "plan": plan,
        "role": admin_role
    }
    mock_user_response = MagicMock()
    mock_user_response.data = [user_data]
    
    # Create usage data that would normally EXCEED limits
    # Even with massive usage, admin should bypass
    usage_data = {
        'tokens_used': 999999999,
        'requests_count': 999999999,
        'pdf_uploads': 999999999,
        'mcqs_generated': 999999999,
        'images_used': 999999999,
        'flashcards_generated': 999999999,
    }
    
    # Mock usage_counters table response
    mock_usage_response = MagicMock()
    mock_usage_response.data = [{
        "id": "usage-id-123",
        "user_id": user_id,
        "date": str(date.today()),
        **usage_data
    }]
    
    # Set up mock table calls
    def mock_table_select(table_name):
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_eq2 = MagicMock()
        
        if table_name == "users":
            mock_eq.execute.return_value = mock_user_response
            mock_select.eq.return_value = mock_eq
        elif table_name == "usage_counters":
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq
        
        mock_table.select.return_value = mock_select
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_select
    
    # Create rate limiter with mock client
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit(user_id, feature)
    
    # Property: Admin users should ALWAYS pass rate limit checks
    assert result is True, \
        f"Admin users should bypass rate limits. Role: {admin_role}, Result: {result}"


# Feature: medical-ai-platform, Property 25: Multi-level rate limiting
@given(
    user_id=valid_user_id(),
    plan=st.sampled_from(['free', 'student', 'pro']),  # Exclude admin
    feature=valid_feature()
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_multi_level_rate_limiting(user_id, plan, feature):
    """
    Property 25: For any request, the system should enforce limits at token level, 
    feature level, and plan level (all three must pass).
    
    Validates: Requirements 9.6
    """
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Mock user table response (non-admin)
    user_data = {
        "plan": plan,
        "role": None
    }
    mock_user_response = MagicMock()
    mock_user_response.data = [user_data]
    
    # Get plan limits
    limits = PLAN_LIMITS[plan]
    
    # Test Case 1: Token limit exceeded (should fail)
    usage_over_tokens = {
        'tokens_used': int(limits['daily_tokens'] + 1),
        'requests_count': 0,
        'pdf_uploads': 0,
        'mcqs_generated': 0,
        'images_used': 0,
        'flashcards_generated': 0,
    }
    
    mock_usage_response = MagicMock()
    mock_usage_response.data = [{
        "id": "usage-id-123",
        "user_id": user_id,
        "date": str(date.today()),
        **usage_over_tokens
    }]
    
    def mock_table_select(table_name):
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_eq2 = MagicMock()
        
        if table_name == "users":
            mock_eq.execute.return_value = mock_user_response
            mock_select.eq.return_value = mock_eq
        elif table_name == "usage_counters":
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq
        
        mock_table.select.return_value = mock_select
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_select
    
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    result = await rate_limiter.check_rate_limit(user_id, feature)
    
    # Property: Should fail when token limit exceeded
    assert result is False, \
        f"Should reject when token limit exceeded. Tokens used: {usage_over_tokens['tokens_used']}, Limit: {limits['daily_tokens']}"
    
    # Test Case 2: Request limit exceeded (should fail)
    usage_over_requests = {
        'tokens_used': 0,
        'requests_count': int(limits['daily_requests'] + 1),
        'pdf_uploads': 0,
        'mcqs_generated': 0,
        'images_used': 0,
        'flashcards_generated': 0,
    }
    
    mock_usage_response.data = [{
        "id": "usage-id-123",
        "user_id": user_id,
        "date": str(date.today()),
        **usage_over_requests
    }]
    
    mock_supabase.table.side_effect = mock_table_select
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    result = await rate_limiter.check_rate_limit(user_id, feature)
    
    # Property: Should fail when request limit exceeded
    assert result is False, \
        f"Should reject when request limit exceeded. Requests: {usage_over_requests['requests_count']}, Limit: {limits['daily_requests']}"
    
    # Test Case 3: Feature-specific limit exceeded (should fail for that feature)
    if feature == 'mcq' and limits['mcqs_per_day'] > 0:
        usage_over_feature = {
            'tokens_used': 0,
            'requests_count': 0,
            'pdf_uploads': 0,
            'mcqs_generated': int(limits['mcqs_per_day'] + 1),
            'images_used': 0,
            'flashcards_generated': 0,
        }
        
        mock_usage_response.data = [{
            "id": "usage-id-123",
            "user_id": user_id,
            "date": str(date.today()),
            **usage_over_feature
        }]
        
        mock_supabase.table.side_effect = mock_table_select
        rate_limiter = RateLimiter(supabase_client=mock_supabase)
        result = await rate_limiter.check_rate_limit(user_id, feature)
        
        # Property: Should fail when feature-specific limit exceeded
        assert result is False, \
            f"Should reject when MCQ limit exceeded. MCQs: {usage_over_feature['mcqs_generated']}, Limit: {limits['mcqs_per_day']}"


# Feature: medical-ai-platform, Property 20: Usage tracking is comprehensive
@given(
    user_id=valid_user_id(),
    tokens=st.integers(min_value=0, max_value=10000),
    feature=st.one_of(st.none(), valid_feature())
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_usage_tracking_comprehensive(user_id, tokens, feature):
    """
    Property 20: For any user request, all applicable usage metrics 
    (tokens_used, requests_count, feature-specific counters) should be 
    incremented correctly.
    
    Validates: Requirements 9.1
    """
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    today = str(date.today())
    
    # Initial usage data
    initial_usage = {
        'id': 'usage-id-123',
        'user_id': user_id,
        'date': today,
        'tokens_used': 100,
        'requests_count': 5,
        'pdf_uploads': 2,
        'mcqs_generated': 3,
        'images_used': 1,
        'flashcards_generated': 4,
    }
    
    # Mock existing usage counter
    mock_usage_response = MagicMock()
    mock_usage_response.data = [initial_usage.copy()]
    
    # Mock update response
    mock_update_response = MagicMock()
    mock_update_response.data = [{'id': 'usage-id-123'}]
    
    # Track what update was called with
    update_data_captured = {}
    
    def mock_table_operations(table_name):
        mock_table = MagicMock()
        
        if table_name == "usage_counters":
            # Mock select chain
            mock_select = MagicMock()
            mock_eq1 = MagicMock()
            mock_eq2 = MagicMock()
            mock_eq2.execute.return_value = mock_usage_response
            mock_eq1.eq.return_value = mock_eq2
            mock_select.eq.return_value = mock_eq1
            mock_table.select.return_value = mock_select
            
            # Mock update chain
            def capture_update(data):
                update_data_captured.update(data)
                mock_update = MagicMock()
                mock_eq_update = MagicMock()
                mock_eq_update.execute.return_value = mock_update_response
                mock_update.eq.return_value = mock_eq_update
                return mock_update
            
            mock_table.update.side_effect = capture_update
        
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_operations
    
    # Create rate limiter with mock client
    rate_limiter = RateLimiter(supabase_client=mock_supabase)
    
    # Increment usage
    await rate_limiter.increment_usage(user_id, tokens, feature)
    
    # Property 1: tokens_used should be incremented by the specified amount
    assert 'tokens_used' in update_data_captured, \
        "tokens_used should be updated"
    assert update_data_captured['tokens_used'] == initial_usage['tokens_used'] + tokens, \
        f"tokens_used should be incremented by {tokens}. Expected: {initial_usage['tokens_used'] + tokens}, Got: {update_data_captured['tokens_used']}"
    
    # Property 2: requests_count should always be incremented by 1
    assert 'requests_count' in update_data_captured, \
        "requests_count should be updated"
    assert update_data_captured['requests_count'] == initial_usage['requests_count'] + 1, \
        f"requests_count should be incremented by 1. Expected: {initial_usage['requests_count'] + 1}, Got: {update_data_captured['requests_count']}"
    
    # Property 3: Feature-specific counters should be incremented when feature is specified
    if feature == 'mcq':
        assert 'mcqs_generated' in update_data_captured, \
            "mcqs_generated should be updated for mcq feature"
        assert update_data_captured['mcqs_generated'] == initial_usage['mcqs_generated'] + 1, \
            f"mcqs_generated should be incremented by 1"
    elif feature == 'flashcard':
        assert 'flashcards_generated' in update_data_captured, \
            "flashcards_generated should be updated for flashcard feature"
        assert update_data_captured['flashcards_generated'] == initial_usage['flashcards_generated'] + 1, \
            f"flashcards_generated should be incremented by 1"
    elif feature == 'pdf':
        assert 'pdf_uploads' in update_data_captured, \
            "pdf_uploads should be updated for pdf feature"
        assert update_data_captured['pdf_uploads'] == initial_usage['pdf_uploads'] + 1, \
            f"pdf_uploads should be incremented by 1"
    elif feature == 'image':
        assert 'images_used' in update_data_captured, \
            "images_used should be updated for image feature"
        assert update_data_captured['images_used'] == initial_usage['images_used'] + 1, \
            f"images_used should be incremented by 1"
    
    # Property 4: Database update should be called
    mock_supabase.table.assert_any_call("usage_counters")


# Feature: medical-ai-platform, Property 23: Daily counters reset at midnight UTC
@given(
    num_users=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=100)
@pytest.mark.property_test
@pytest.mark.asyncio
async def test_property_daily_counters_reset(num_users):
    """
    Property 23: For any user, after the daily reset job runs, 
    all usage counters for the current date should be zero.
    
    Note: The reset job doesn't delete old records (for history tracking),
    but ensures new requests create fresh counters for the new day.
    
    Validates: Requirements 9.4
    """
    # Import here to avoid circular dependency
    from services.scheduler import Scheduler
    
    # Create mock Supabase client
    mock_supabase = MagicMock()
    
    today = str(date.today())
    
    # Mock the count query for previous day users
    mock_count_response = MagicMock()
    mock_count_response.count = num_users
    mock_count_response.data = []
    
    # Set up mock chain for select query
    mock_execute = MagicMock()
    mock_execute.execute.return_value = mock_count_response
    mock_lt = MagicMock()
    mock_lt.lt.return_value = mock_execute
    mock_select = MagicMock()
    mock_select.select.return_value = mock_lt
    mock_supabase.table.return_value = mock_select
    
    # Create scheduler with mock client
    scheduler = Scheduler(supabase_client=mock_supabase)
    
    # Run the reset job
    result = await scheduler.reset_daily_counters()
    
    # Property 1: Reset should complete successfully
    assert result is not None, "Reset should return a result"
    assert result["status"] == "success", f"Reset should succeed, got status: {result['status']}"
    
    # Property 2: Reset should record the date
    assert result["reset_date"] == today, \
        f"Reset date should be today ({today}), got: {result['reset_date']}"
    
    # Property 3: Reset should record the time
    assert "reset_time" in result, "Reset should record the time"
    assert result["reset_time"] is not None, "Reset time should not be None"
    
    # Property 4: Reset should track previous day users
    assert "users_with_previous_usage" in result, \
        "Reset should track users with previous usage"
    assert result["users_with_previous_usage"] == num_users, \
        f"Should track {num_users} users, got: {result['users_with_previous_usage']}"
    
    # Property 5: Database query should be called to check previous usage
    mock_supabase.table.assert_called_with("usage_counters")
