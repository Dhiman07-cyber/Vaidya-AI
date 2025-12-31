"""
Integration Tests for Clinical Tools
Tests the complete flow of clinical reasoning and OSCE features
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from main import app
import uuid
import json


client = TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    user_id = str(uuid.uuid4())
    
    async def mock_get_current_user_id(authorization):
        return user_id
    
    return user_id, mock_get_current_user_id


@pytest.fixture
def mock_clinical_service():
    """Mock clinical service"""
    mock_service = MagicMock()
    
    # Mock create_clinical_case
    mock_service.create_clinical_case = AsyncMock(return_value={
        "case_id": str(uuid.uuid4()),
        "chief_complaint": "Chest pain",
        "stages": [
            {"stage": 1, "title": "Chief Complaint", "content": "Patient with chest pain", "question": "What next?"},
            {"stage": 2, "title": "History", "content": "Pain for 2 hours", "question": "Examination?"}
        ],
        "current_stage": 0,
        "user_id": str(uuid.uuid4())
    })
    
    # Mock present_case_progressively
    mock_service.present_case_progressively = AsyncMock(return_value={
        "case_id": str(uuid.uuid4()),
        "current_stage": 0,
        "stage_data": {"stage": 1, "title": "Chief Complaint", "content": "Patient with chest pain", "question": "What next?"},
        "has_more_stages": True,
        "total_stages": 2,
        "completed": False
    })
    
    # Mock advance_case_stage
    mock_service.advance_case_stage = AsyncMock(return_value={
        "case_id": str(uuid.uuid4()),
        "current_stage": 1,
        "stage_data": {"stage": 2, "title": "History", "content": "Pain for 2 hours", "question": "Examination?"},
        "has_more_stages": False,
        "total_stages": 2,
        "completed": False
    })
    
    # Mock evaluate_clinical_reasoning
    mock_service.evaluate_clinical_reasoning = AsyncMock(return_value={
        "score": 85,
        "evaluation": "Good differential diagnosis",
        "feedback": ["Considered major causes", "Could add more detail"],
        "model_answer": "Should include MI, PE, aortic dissection"
    })
    
    # Mock create_osce_scenario
    mock_service.create_osce_scenario = AsyncMock(return_value={
        "scenario_id": str(uuid.uuid4()),
        "scenario_type": "history_taking",
        "patient_info": {"age": 45, "gender": "female", "presenting_complaint": "Chest pain"},
        "instructions": "Take a focused history",
        "user_id": str(uuid.uuid4())
    })
    
    # Mock simulate_examiner_interaction
    mock_service.simulate_examiner_interaction = AsyncMock(return_value={
        "patient_response": "I've been having chest pain for 2 hours",
        "examiner_observation": "Student asked appropriate question",
        "checklist_items_met": ["Asks about pain"],
        "feedback": None
    })
    
    # Mock get_osce_performance
    mock_service.get_osce_performance = AsyncMock(return_value={
        "scenario_id": str(uuid.uuid4()),
        "score": 85.0,
        "earned_points": 17,
        "total_points": 20,
        "checklist_items_completed": 8,
        "total_checklist_items": 10
    })
    
    return mock_service


def test_create_clinical_case_flow(mock_auth_user, mock_clinical_service):
    """
    Test creating a clinical reasoning case
    
    Requirements: 5.1, 5.3
    """
    user_id, mock_get_user = mock_auth_user
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.post(
                "/api/clinical/reasoning",
                json={"specialty": "cardiology", "difficulty": "intermediate"},
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 201
    data = response.json()
    assert "case_id" in data
    assert "chief_complaint" in data
    assert data["current_stage"] == 0
    assert data["total_stages"] == 2
    
    # Verify service was called correctly
    mock_clinical_service.create_clinical_case.assert_called_once()
    call_args = mock_clinical_service.create_clinical_case.call_args
    assert call_args.kwargs["user_id"] == user_id
    assert call_args.kwargs["specialty"] == "cardiology"
    assert call_args.kwargs["difficulty"] == "intermediate"


def test_get_clinical_case_stage(mock_auth_user, mock_clinical_service):
    """
    Test retrieving current stage of a clinical case
    
    Requirements: 5.3
    """
    user_id, mock_get_user = mock_auth_user
    case_id = str(uuid.uuid4())
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.get(
                f"/api/clinical/reasoning/{case_id}",
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
    assert "current_stage" in data
    assert "stage_data" in data
    assert data["has_more_stages"] is True
    assert data["completed"] is False


def test_advance_clinical_case_stage(mock_auth_user, mock_clinical_service):
    """
    Test advancing to next stage of clinical case
    
    Requirements: 5.3
    """
    user_id, mock_get_user = mock_auth_user
    case_id = str(uuid.uuid4())
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.post(
                f"/api/clinical/reasoning/{case_id}/advance",
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_stage"] == 1
    assert "stage_data" in data


def test_evaluate_clinical_reasoning_flow(mock_auth_user, mock_clinical_service):
    """
    Test evaluating a clinical reasoning response
    
    Requirements: 5.5
    """
    user_id, mock_get_user = mock_auth_user
    case_id = str(uuid.uuid4())
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.post(
                f"/api/clinical/reasoning/{case_id}/evaluate",
                json={
                    "user_response": "My differential includes MI, PE, and aortic dissection",
                    "stage": 0
                },
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "evaluation" in data
    assert "feedback" in data
    assert "model_answer" in data
    assert data["score"] == 85


def test_create_osce_scenario_flow(mock_auth_user, mock_clinical_service):
    """
    Test creating an OSCE scenario
    
    Requirements: 5.2, 5.4
    """
    user_id, mock_get_user = mock_auth_user
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.post(
                "/api/clinical/osce",
                json={"scenario_type": "history_taking", "difficulty": "intermediate"},
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 201
    data = response.json()
    assert "scenario_id" in data
    assert "scenario_type" in data
    assert data["scenario_type"] == "history_taking"
    assert "patient_info" in data
    assert "instructions" in data


def test_osce_interaction_flow(mock_auth_user, mock_clinical_service):
    """
    Test OSCE patient/examiner interaction
    
    Requirements: 5.4
    """
    user_id, mock_get_user = mock_auth_user
    scenario_id = str(uuid.uuid4())
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.post(
                f"/api/clinical/osce/{scenario_id}/interact",
                json={"user_action": "Hello, I'm Dr. Smith. Can you tell me about your chest pain?"},
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert "patient_response" in data
    assert "examiner_observation" in data
    assert "checklist_items_met" in data
    assert isinstance(data["checklist_items_met"], list)


def test_get_osce_performance(mock_auth_user, mock_clinical_service):
    """
    Test retrieving OSCE performance summary
    
    Requirements: 5.5
    """
    user_id, mock_get_user = mock_auth_user
    scenario_id = str(uuid.uuid4())
    
    with patch('main.get_current_user_id', mock_get_user):
        with patch('services.clinical.get_clinical_service', return_value=mock_clinical_service):
            response = client.get(
                f"/api/clinical/osce/{scenario_id}/performance",
                headers={"Authorization": "Bearer test_token"}
            )
    
    assert response.status_code == 200
    data = response.json()
    assert "scenario_id" in data
    assert "score" in data
    assert "earned_points" in data
    assert "total_points" in data
    assert data["score"] == 85.0


def test_clinical_case_unauthorized():
    """Test that clinical endpoints require authentication"""
    response = client.post(
        "/api/clinical/reasoning",
        json={"specialty": "cardiology", "difficulty": "intermediate"}
    )
    
    assert response.status_code == 401


def test_osce_unauthorized():
    """Test that OSCE endpoints require authentication"""
    response = client.post(
        "/api/clinical/osce",
        json={"scenario_type": "history_taking", "difficulty": "intermediate"}
    )
    
    assert response.status_code == 401
