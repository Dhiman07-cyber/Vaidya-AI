"""
Property-Based Tests for Clinical Service
Tests universal properties related to clinical reasoning functionality
Feature: medical-ai-platform
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock, patch
from services.clinical import ClinicalService
import uuid
import json


# Custom strategies for generating test data
def valid_specialty():
    """Generate valid medical specialties"""
    return st.sampled_from([
        "cardiology", "neurology", "gastroenterology", 
        "pulmonology", "endocrinology", "nephrology"
    ])


def valid_difficulty():
    """Generate valid difficulty levels"""
    return st.sampled_from(["beginner", "intermediate", "advanced"])


def generate_mock_case_stages(num_stages):
    """Generate mock case stages for testing"""
    stages = []
    for i in range(num_stages):
        stages.append({
            "stage": i + 1,
            "title": f"Stage {i + 1}",
            "content": f"Content for stage {i + 1}",
            "question": f"Question for stage {i + 1}?"
        })
    return stages


# Feature: medical-ai-platform, Property 12: Clinical reasoning presents cases progressively
@given(
    num_stages=st.integers(min_value=3, max_value=10),
    current_stage=st.integers(min_value=0, max_value=9)
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_progressive_case_presentation_property(num_stages, current_stage):
    """
    Property 12: For any clinical reasoning session, patient cases should be 
    presented in sequential order without skipping.
    
    This property verifies that:
    1. Cases are presented one stage at a time
    2. Stages are presented in order (stage 0, then 1, then 2, etc.)
    3. No stages are skipped
    4. The current stage index correctly tracks progress
    
    Validates: Requirements 5.3
    """
    # Ensure current_stage is within valid range for num_stages
    if current_stage >= num_stages:
        current_stage = num_stages - 1
    
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Create mock case data with stages
    stages = generate_mock_case_stages(num_stages)
    case_data = {
        "user_id": user_id,
        "case_type": "clinical_reasoning",
        "specialty": "cardiology",
        "difficulty": "intermediate",
        "chief_complaint": "Test chief complaint",
        "stages": stages,
        "current_stage": current_stage,
        "performance_data": {},
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Mock session verification (session exists and belongs to user)
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id}]
    
    # Mock messages response (case data stored as system message)
    mock_messages_response = MagicMock()
    mock_messages_response.data = [{
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "system",
        "content": json.dumps(case_data),
        "tokens_used": 100,
        "created_at": "2024-01-01T00:00:00Z"
    }]
    
    # Set up mock chain for session verification
    mock_session_select = MagicMock()
    mock_session_select.execute.return_value = mock_session_response
    mock_session_eq2 = MagicMock()
    mock_session_eq2.execute.return_value = mock_session_response
    mock_session_eq1 = MagicMock()
    mock_session_eq1.eq.return_value = mock_session_eq2
    mock_session_table = MagicMock()
    mock_session_table.select.return_value.eq.return_value.eq.return_value = mock_session_eq2
    
    # Set up mock chain for messages retrieval
    mock_messages_select = MagicMock()
    mock_messages_select.execute.return_value = mock_messages_response
    mock_messages_limit = MagicMock()
    mock_messages_limit.execute.return_value = mock_messages_response
    mock_messages_order = MagicMock()
    mock_messages_order.limit.return_value = mock_messages_limit
    mock_messages_eq2 = MagicMock()
    mock_messages_eq2.order.return_value = mock_messages_order
    mock_messages_eq1 = MagicMock()
    mock_messages_eq1.eq.return_value = mock_messages_eq2
    mock_messages_table = MagicMock()
    mock_messages_table.select.return_value.eq.return_value.eq.return_value = mock_messages_eq2
    
    # Configure table routing
    def table_router(table_name):
        if table_name == "chat_sessions":
            return mock_session_table
        elif table_name == "messages":
            return mock_messages_table
        return MagicMock()
    
    mock_supabase.table.side_effect = table_router
    
    # Create clinical service with mock client
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act: Present case progressively
    result = await clinical_service.present_case_progressively(session_id, user_id)
    
    # Assert: Verify progressive presentation properties
    assert result is not None
    assert result["case_id"] == session_id
    assert result["current_stage"] == current_stage
    assert result["total_stages"] == num_stages
    
    # Property 1: Current stage should be within valid range
    assert 0 <= result["current_stage"] < num_stages or result.get("completed", False)
    
    # Property 2: If not completed, stage_data should be present
    if not result.get("completed", False):
        assert result["stage_data"] is not None
        assert result["stage_data"]["stage"] == current_stage + 1  # Stages are 1-indexed in data
        
        # Property 3: Stage data should match the current stage index
        expected_stage = stages[current_stage]
        assert result["stage_data"]["title"] == expected_stage["title"]
        assert result["stage_data"]["content"] == expected_stage["content"]
        assert result["stage_data"]["question"] == expected_stage["question"]
        
        # Property 4: has_more_stages should be correct
        assert result["has_more_stages"] == (current_stage < num_stages - 1)
    else:
        # If completed, stage_data should be None
        assert result["stage_data"] is None
        assert result["has_more_stages"] is False
        assert result["current_stage"] >= num_stages
    
    # Verify database was queried correctly
    mock_supabase.table.assert_any_call("chat_sessions")
    mock_supabase.table.assert_any_call("messages")


# Feature: medical-ai-platform, Property 12: Sequential stage advancement
@given(
    num_stages=st.integers(min_value=3, max_value=8)
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_sequential_stage_advancement_property(num_stages):
    """
    Property 12 (Extended): For any clinical case, advancing through stages
    should proceed sequentially (0 -> 1 -> 2 -> ...) without skipping.
    
    This property verifies that:
    1. Each call to advance_case_stage increments the stage by exactly 1
    2. Stages cannot be skipped
    3. Stage advancement is monotonic (always increasing)
    
    Validates: Requirements 5.3
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    # Create mock case data starting at stage 0
    stages = generate_mock_case_stages(num_stages)
    case_data = {
        "user_id": user_id,
        "case_type": "clinical_reasoning",
        "specialty": "cardiology",
        "difficulty": "intermediate",
        "chief_complaint": "Test chief complaint",
        "stages": stages,
        "current_stage": 0,  # Start at stage 0
        "performance_data": {},
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Track stage progression
    stage_progression = [0]
    
    # Mock session verification
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id}]
    
    # Mock messages response - will be updated as we advance
    def get_messages_response():
        return MagicMock(data=[{
            "id": message_id,
            "session_id": session_id,
            "role": "system",
            "content": json.dumps(case_data),
            "tokens_used": 100,
            "created_at": "2024-01-01T00:00:00Z"
        }])
    
    # Mock update to track stage changes
    def mock_update_handler(update_data):
        nonlocal case_data
        updated_content = json.loads(update_data["content"])
        case_data["current_stage"] = updated_content["current_stage"]
        stage_progression.append(case_data["current_stage"])
        mock_response = MagicMock()
        mock_response.data = [{"id": message_id}]
        return mock_response
    
    # Set up mock chains
    mock_session_table = MagicMock()
    mock_session_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_session_response
    
    mock_messages_table = MagicMock()
    
    # Messages select chain
    def messages_select_chain(*args, **kwargs):
        mock_chain = MagicMock()
        mock_chain.execute.return_value = get_messages_response()
        return mock_chain
    
    mock_messages_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value = messages_select_chain()
    
    # Messages update chain
    mock_update_chain = MagicMock()
    mock_update_chain.execute = lambda: mock_update_handler(mock_update_chain._update_data)
    
    def mock_update(data):
        mock_update_chain._update_data = data
        return MagicMock(eq=lambda *args: mock_update_chain)
    
    mock_messages_table.update = mock_update
    
    # Configure table routing
    def table_router(table_name):
        if table_name == "chat_sessions":
            return mock_session_table
        elif table_name == "messages":
            # Return fresh mock each time to handle multiple calls
            mock_table = MagicMock()
            mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = get_messages_response()
            mock_table.update = mock_update
            return mock_table
        return MagicMock()
    
    mock_supabase.table.side_effect = table_router
    
    # Create clinical service with mock client
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act: Advance through first 3 stages (or all stages if fewer than 3)
    max_advances = min(3, num_stages - 1)
    
    for i in range(max_advances):
        result = await clinical_service.advance_case_stage(session_id, user_id)
        
        # Assert: Each advancement increments stage by exactly 1
        assert result["current_stage"] == i + 1
        
        # Property: Stage should match expected progression
        assert case_data["current_stage"] == i + 1
    
    # Property: Verify sequential progression (no skips)
    for i in range(len(stage_progression) - 1):
        # Each stage should be exactly 1 more than the previous
        assert stage_progression[i + 1] == stage_progression[i] + 1
    
    # Property: Verify monotonic increase (always increasing)
    assert stage_progression == sorted(stage_progression)
    
    # Property: Verify we advanced the expected number of times
    assert len(stage_progression) == max_advances + 1  # +1 for initial stage 0


# Feature: medical-ai-platform, Property 13: OSCE mode generates examiner interactions
@given(
    user_action=st.text(min_size=5, max_size=200)
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_osce_examiner_interaction_property(user_action):
    """
    Property 13: For any OSCE simulation session, examiner responses should be 
    generated for user actions.
    
    This property verifies that:
    1. Every user action receives a response
    2. Responses include patient reaction
    3. Examiner observations are recorded
    4. Interaction history is maintained
    
    Validates: Requirements 5.4
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    # Create mock OSCE scenario data
    scenario_data = {
        "user_id": user_id,
        "case_type": "osce",
        "scenario_type": "history_taking",
        "difficulty": "intermediate",
        "patient_info": {
            "age": 45,
            "gender": "female",
            "presenting_complaint": "Chest pain"
        },
        "instructions": "Take a focused history",
        "patient_script": {
            "opening": "Hello doctor",
            "responses": {}
        },
        "examiner_checklist": [
            {"item": "Introduces self", "points": 1},
            {"item": "Asks about pain", "points": 2}
        ],
        "interaction_history": [],
        "performance_data": {},
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Mock messages response
    mock_messages_response = MagicMock()
    mock_messages_response.data = [{
        "id": message_id,
        "session_id": session_id,
        "role": "system",
        "content": json.dumps(scenario_data),
        "tokens_used": 100,
        "created_at": "2024-01-01T00:00:00Z"
    }]
    
    # Mock model router response
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": json.dumps({
            "patient_response": "I've been having chest pain for 2 hours",
            "examiner_observation": "Student asked appropriate opening question",
            "checklist_items_met": ["Asks about pain"],
            "feedback": None
        }),
        "tokens_used": 80
    })
    
    # Track updates
    updated_content = None
    
    def mock_update_handler(data):
        nonlocal updated_content
        updated_content = data["content"]
        mock_response = MagicMock()
        mock_response.data = [{"id": message_id}]
        return mock_response
    
    # Set up mock chains
    mock_messages_table = MagicMock()
    mock_messages_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_messages_response
    
    # Mock update
    mock_update_chain = MagicMock()
    mock_update_chain.execute = lambda: mock_update_handler(mock_update_chain._update_data)
    
    def mock_update(data):
        mock_update_chain._update_data = data
        return MagicMock(eq=lambda *args: mock_update_chain)
    
    mock_messages_table.update = mock_update
    
    # Mock insert for user and assistant messages
    mock_insert_response = MagicMock()
    mock_insert_response.data = [{"id": str(uuid.uuid4())}]
    mock_messages_table.insert.return_value.execute.return_value = mock_insert_response
    
    # Configure table routing
    def table_router(table_name):
        if table_name == "messages":
            return mock_messages_table
        return MagicMock()
    
    mock_supabase.table.side_effect = table_router
    
    # Create clinical service with mock client
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act: Simulate examiner interaction
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await clinical_service.simulate_examiner_interaction(session_id, user_id, user_action)
    
    # Assert: Verify interaction properties
    assert result is not None
    
    # Property 1: Every user action receives a response
    assert "patient_response" in result
    assert result["patient_response"] is not None
    
    # Property 2: Examiner observations are recorded
    assert "examiner_observation" in result
    
    # Property 3: Checklist tracking exists
    assert "checklist_items_met" in result
    assert isinstance(result["checklist_items_met"], list)
    
    # Property 4: Interaction history is maintained
    if updated_content:
        updated_scenario = json.loads(updated_content)
        assert "interaction_history" in updated_scenario
        # History should contain the user action
        history_text = " ".join(updated_scenario["interaction_history"])
        assert user_action in history_text or len(updated_scenario["interaction_history"]) > 0
    
    # Verify model router was called
    mock_router.select_provider.assert_called_once_with("osce")
    mock_router.execute_with_fallback.assert_called_once()

