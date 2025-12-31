"""
Unit Tests for Clinical Service
Tests specific functionality of clinical reasoning service
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.clinical import ClinicalService, get_clinical_service
import uuid
import json


@pytest.mark.asyncio
async def test_create_clinical_case_basic():
    """Test basic clinical case creation"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Mock model router response
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": json.dumps({
            "chief_complaint": "Chest pain",
            "stages": [
                {"stage": 1, "title": "Chief Complaint", "content": "Patient presents with chest pain", "question": "What would you like to know?"},
                {"stage": 2, "title": "History", "content": "Pain started 2 hours ago", "question": "What examination would you perform?"}
            ]
        }),
        "tokens_used": 150
    })
    
    # Mock session creation
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id}]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_session_response
    
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await clinical_service.create_clinical_case(user_id, specialty="cardiology")
    
    # Assert
    assert result is not None
    assert result["case_id"] == session_id
    assert result["chief_complaint"] == "Chest pain"
    assert len(result["stages"]) == 2
    assert result["current_stage"] == 0
    assert result["user_id"] == user_id


@pytest.mark.asyncio
async def test_present_case_progressively_first_stage():
    """Test presenting the first stage of a case"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    case_data = {
        "user_id": user_id,
        "case_type": "clinical_reasoning",
        "chief_complaint": "Chest pain",
        "stages": [
            {"stage": 1, "title": "Chief Complaint", "content": "Patient presents with chest pain", "question": "What next?"},
            {"stage": 2, "title": "History", "content": "Pain started 2 hours ago", "question": "What examination?"}
        ],
        "current_stage": 0
    }
    
    # Mock session verification
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id}]
    
    # Mock messages response
    mock_messages_response = MagicMock()
    mock_messages_response.data = [{
        "id": str(uuid.uuid4()),
        "content": json.dumps(case_data)
    }]
    
    # Set up mock chains
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_session_response
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_messages_response
    
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act
    result = await clinical_service.present_case_progressively(session_id, user_id)
    
    # Assert
    assert result["current_stage"] == 0
    assert result["stage_data"]["stage"] == 1
    assert result["stage_data"]["title"] == "Chief Complaint"
    assert result["has_more_stages"] is True
    assert result["completed"] is False


@pytest.mark.asyncio
async def test_present_case_progressively_completed():
    """Test presenting a completed case"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    case_data = {
        "user_id": user_id,
        "case_type": "clinical_reasoning",
        "chief_complaint": "Chest pain",
        "stages": [
            {"stage": 1, "title": "Stage 1", "content": "Content 1", "question": "Q1?"},
            {"stage": 2, "title": "Stage 2", "content": "Content 2", "question": "Q2?"}
        ],
        "current_stage": 2  # Beyond last stage
    }
    
    # Mock responses
    mock_session_response = MagicMock()
    mock_session_response.data = [{"id": session_id}]
    
    mock_messages_response = MagicMock()
    mock_messages_response.data = [{
        "id": str(uuid.uuid4()),
        "content": json.dumps(case_data)
    }]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_session_response
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_messages_response
    
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act
    result = await clinical_service.present_case_progressively(session_id, user_id)
    
    # Assert
    assert result["completed"] is True
    assert result["stage_data"] is None
    assert result["has_more_stages"] is False


@pytest.mark.asyncio
async def test_evaluate_clinical_reasoning():
    """Test evaluation of clinical reasoning response"""
    # Arrange
    mock_supabase = MagicMock()
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    case_data = {
        "chief_complaint": "Chest pain",
        "stages": [
            {"stage": 1, "title": "Chief Complaint", "content": "Patient with chest pain", "question": "What's your differential?"}
        ],
        "performance_data": {}
    }
    
    # Mock messages response
    mock_messages_response = MagicMock()
    mock_messages_response.data = [{
        "id": message_id,
        "content": json.dumps(case_data)
    }]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_messages_response
    
    # Mock update
    mock_update_response = MagicMock()
    mock_update_response.data = [{"id": message_id}]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
    
    # Mock model router
    mock_router = MagicMock()
    mock_router.select_provider = AsyncMock(return_value="gemini")
    mock_router.execute_with_fallback = AsyncMock(return_value={
        "success": True,
        "content": json.dumps({
            "score": 85,
            "evaluation": "Good differential diagnosis",
            "feedback": ["Considered major causes", "Could add more detail"],
            "model_answer": "Should include MI, PE, aortic dissection..."
        }),
        "tokens_used": 100
    })
    
    clinical_service = ClinicalService(supabase_client=mock_supabase)
    
    # Act
    with patch('services.model_router.get_model_router_service', return_value=mock_router):
        result = await clinical_service.evaluate_clinical_reasoning(
            session_id, user_id, "My differential includes MI and PE", 0
        )
    
    # Assert
    assert result["score"] == 85
    assert "evaluation" in result
    assert "feedback" in result
    assert "model_answer" in result


def test_get_clinical_service_singleton():
    """Test that get_clinical_service returns singleton instance"""
    mock_supabase = MagicMock()
    service1 = get_clinical_service(mock_supabase)
    service2 = get_clinical_service()
    assert service1 is service2
