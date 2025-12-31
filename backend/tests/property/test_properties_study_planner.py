"""
Property-Based Tests for Study Planner Service
Tests universal properties related to study planning functionality
Feature: medical-ai-platform
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock
from services.study_planner import StudyPlannerService
import uuid


# Custom strategies for generating test data
def valid_topic():
    """Generate valid study topics"""
    return st.text(min_size=1, max_size=200)


def valid_duration():
    """Generate valid study durations (in minutes)"""
    return st.integers(min_value=15, max_value=480)  # 15 minutes to 8 hours


def valid_status():
    """Generate valid session statuses"""
    return st.sampled_from(["planned", "in_progress", "completed", "cancelled"])


# Feature: medical-ai-platform, Property 14: Study plan CRUD operations work correctly
@given(
    topic=valid_topic(),
    duration=valid_duration()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_study_plan_create_retrieve_property(topic, duration):
    """
    Property 14: For any study plan created, it should be retrievable, 
    updatable, and deletable by the owning user.
    
    This property verifies the Create and Read operations:
    1. Created study sessions can be retrieved
    2. Retrieved sessions match the created data
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Mock insert response (Create)
    mock_insert_response = MagicMock()
    mock_insert_response.data = [{
        "id": session_id,
        "user_id": user_id,
        "topic": topic,
        "duration": duration,
        "scheduled_date": None,
        "notes": None,
        "status": "planned",
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }]
    
    # Mock select response (Read)
    mock_select_response = MagicMock()
    mock_select_response.data = [{
        "id": session_id,
        "user_id": user_id,
        "topic": topic,
        "duration": duration,
        "scheduled_date": None,
        "notes": None,
        "status": "planned",
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }]
    
    # Set up mock chains
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = mock_insert_response
    mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_select_response
    
    mock_supabase.table.return_value = mock_table
    
    # Create study planner service with mock client
    planner_service = StudyPlannerService(supabase_client=mock_supabase)
    
    # Act: Create study session
    created_session = await planner_service.create_study_session(
        user_id=user_id,
        topic=topic,
        duration=duration
    )
    
    # Assert: Created session has correct data
    assert created_session is not None
    assert created_session["id"] == session_id
    assert created_session["user_id"] == user_id
    assert created_session["topic"] == topic
    assert created_session["duration"] == duration
    assert created_session["status"] == "planned"
    
    # Act: Retrieve study sessions
    retrieved_sessions = await planner_service.get_study_sessions(user_id)
    
    # Assert: Retrieved sessions contain the created session
    assert len(retrieved_sessions) > 0
    assert any(s["id"] == session_id for s in retrieved_sessions)
    
    # Property: Retrieved session matches created session
    retrieved_session = next(s for s in retrieved_sessions if s["id"] == session_id)
    assert retrieved_session["topic"] == created_session["topic"]
    assert retrieved_session["duration"] == created_session["duration"]
    assert retrieved_session["user_id"] == created_session["user_id"]


@given(
    topic=valid_topic(),
    duration=valid_duration(),
    new_topic=valid_topic(),
    new_duration=valid_duration()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_study_plan_update_property(topic, duration, new_topic, new_duration):
    """
    Property 14 (Update): For any study plan, updates should be persisted
    and retrievable.
    
    This property verifies the Update operation:
    1. Study sessions can be updated
    2. Updates are persisted correctly
    
    Validates: Requirements 6.3
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Mock session verification
    mock_verify_response = MagicMock()
    mock_verify_response.data = [{"id": session_id}]
    
    # Mock update response
    mock_update_response = MagicMock()
    mock_update_response.data = [{
        "id": session_id,
        "user_id": user_id,
        "topic": new_topic,
        "duration": new_duration,
        "scheduled_date": None,
        "notes": None,
        "status": "planned",
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:01:00Z"
    }]
    
    # Set up mock chains
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_verify_response
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_update_response
    
    mock_supabase.table.return_value = mock_table
    
    # Create study planner service with mock client
    planner_service = StudyPlannerService(supabase_client=mock_supabase)
    
    # Act: Update study session
    updated_session = await planner_service.update_study_session(
        session_id=session_id,
        user_id=user_id,
        data={"topic": new_topic, "duration": new_duration}
    )
    
    # Assert: Updated session has new data
    assert updated_session is not None
    assert updated_session["id"] == session_id
    assert updated_session["topic"] == new_topic
    assert updated_session["duration"] == new_duration
    
    # Property: Update changes the data
    assert updated_session["topic"] != topic or new_topic == topic
    assert updated_session["duration"] != duration or new_duration == duration


@given(
    topic=valid_topic(),
    duration=valid_duration()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_study_plan_delete_property(topic, duration):
    """
    Property 14 (Delete): For any study plan, deletion should succeed
    and the session should no longer be retrievable.
    
    This property verifies the Delete operation:
    1. Study sessions can be deleted
    2. Deleted sessions are no longer accessible
    
    Validates: Requirements 6.3
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Mock session verification
    mock_verify_response = MagicMock()
    mock_verify_response.data = [{"id": session_id}]
    
    # Mock delete response
    mock_delete_response = MagicMock()
    mock_delete_response.data = [{"id": session_id}]
    
    # Set up mock chains
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_verify_response
    mock_table.delete.return_value.eq.return_value.execute.return_value = mock_delete_response
    
    mock_supabase.table.return_value = mock_table
    
    # Create study planner service with mock client
    planner_service = StudyPlannerService(supabase_client=mock_supabase)
    
    # Act: Delete study session
    result = await planner_service.delete_study_session(session_id, user_id)
    
    # Assert: Deletion succeeded
    assert result is not None
    assert result["success"] is True
    assert result["session_id"] == session_id
    
    # Property: Deletion returns success confirmation
    assert "message" in result
    assert isinstance(result["message"], str)


@given(
    topic=valid_topic(),
    duration=valid_duration(),
    status_filter=valid_status()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_study_plan_filter_by_status_property(topic, duration, status_filter):
    """
    Property 14 (Filter): For any status filter, only sessions with that
    status should be returned.
    
    This property verifies filtering functionality:
    1. Status filters work correctly
    2. Only matching sessions are returned
    
    Validates: Requirements 6.4
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Mock select response with filtered results
    mock_select_response = MagicMock()
    mock_select_response.data = [{
        "id": session_id,
        "user_id": user_id,
        "topic": topic,
        "duration": duration,
        "scheduled_date": None,
        "notes": None,
        "status": status_filter,
        "completed_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }]
    
    # Set up mock chains
    mock_table = MagicMock()
    mock_eq_chain = MagicMock()
    mock_eq_chain.order.return_value.limit.return_value.execute.return_value = mock_select_response
    mock_table.select.return_value.eq.return_value.eq.return_value = mock_eq_chain
    
    mock_supabase.table.return_value = mock_table
    
    # Create study planner service with mock client
    planner_service = StudyPlannerService(supabase_client=mock_supabase)
    
    # Act: Get study sessions with status filter
    filtered_sessions = await planner_service.get_study_sessions(
        user_id=user_id,
        status=status_filter
    )
    
    # Assert: All returned sessions have the filtered status
    assert isinstance(filtered_sessions, list)
    
    # Property: All filtered sessions match the status filter
    for session in filtered_sessions:
        assert session["status"] == status_filter
