"""
Integration tests for API key management endpoints

Requirements: 14.2, 14.4, 10.1
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def mock_admin_auth():
    """Mock admin authentication"""
    with patch('main.require_admin') as mock:
        mock.return_value = AsyncMock(return_value="admin-123")
        yield mock


@pytest.fixture
def mock_admin_service():
    """Mock admin service"""
    with patch('services.admin.get_admin_service') as mock:
        service = Mock()
        service.add_api_key = AsyncMock()
        service.list_api_keys = AsyncMock()
        service.update_key_status = AsyncMock()
        service.delete_api_key = AsyncMock()
        service.test_api_key = AsyncMock()
        mock.return_value = service
        yield service


def test_admin_can_add_api_key(mock_admin_auth, mock_admin_service):
    """
    Test that admin can add an API key
    
    Requirements: 14.2
    """
    # Mock the add_api_key response
    mock_admin_service.add_api_key.return_value = {
        "id": "key-123",
        "provider": "gemini",
        "feature": "chat",
        "key_value": "encrypted_key_value",
        "priority": 5,
        "status": "active",
        "failure_count": 0,
        "last_used_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    # Make request
    response = client.post(
        "/api/admin/api-keys",
        json={
            "provider": "gemini",
            "feature": "chat",
            "key": "AIzaSyTest123456789",
            "priority": 5
        },
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "gemini"
    assert data["feature"] == "chat"
    assert data["priority"] == 5
    assert data["status"] == "active"
    
    # Verify service was called
    mock_admin_service.add_api_key.assert_called_once()


def test_key_is_encrypted_in_database(mock_admin_auth, mock_admin_service):
    """
    Test that API key is encrypted before storage
    
    Requirements: 10.1
    """
    # Mock the add_api_key to verify encryption
    mock_admin_service.add_api_key.return_value = {
        "id": "key-123",
        "provider": "gemini",
        "feature": "chat",
        "key_value": "encrypted_base64_string_not_plaintext",
        "priority": 0,
        "status": "active",
        "failure_count": 0,
        "last_used_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    # Make request with plaintext key
    plaintext_key = "AIzaSyPlaintextKey123456789"
    response = client.post(
        "/api/admin/api-keys",
        json={
            "provider": "gemini",
            "feature": "chat",
            "key": plaintext_key,
            "priority": 0
        },
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 201
    data = response.json()
    
    # Key value in response should be encrypted (not plaintext)
    assert data["key_value"] != plaintext_key
    assert data["key_value"] == "encrypted_base64_string_not_plaintext"


def test_admin_can_update_key_status(mock_admin_auth, mock_admin_service):
    """
    Test that admin can update API key status
    
    Requirements: 14.4
    """
    # Mock the update_key_status response
    mock_admin_service.update_key_status.return_value = {
        "id": "key-123",
        "provider": "gemini",
        "feature": "chat",
        "key_value": "encrypted_key_value",
        "priority": 5,
        "status": "disabled",
        "failure_count": 0,
        "last_used_at": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    # Make request
    response = client.put(
        "/api/admin/api-keys/key-123",
        json={"status": "disabled"},
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "disabled"
    
    # Verify service was called
    mock_admin_service.update_key_status.assert_called_once()


def test_admin_can_list_api_keys(mock_admin_auth, mock_admin_service):
    """
    Test that admin can list all API keys
    
    Requirements: 14.2
    """
    # Mock the list_api_keys response
    mock_admin_service.list_api_keys.return_value = [
        {
            "id": "key-1",
            "provider": "gemini",
            "feature": "chat",
            "key_value": "encrypted_1",
            "priority": 10,
            "status": "active",
            "failure_count": 0,
            "last_used_at": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "key-2",
            "provider": "openai",
            "feature": "chat",
            "key_value": "encrypted_2",
            "priority": 5,
            "status": "active",
            "failure_count": 0,
            "last_used_at": None,
            "created_at": "2024-01-02T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z"
        }
    ]
    
    # Make request
    response = client.get(
        "/api/admin/api-keys",
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["provider"] == "gemini"
    assert data[1]["provider"] == "openai"


def test_admin_can_delete_api_key(mock_admin_auth, mock_admin_service):
    """
    Test that admin can delete an API key
    
    Requirements: 14.6
    """
    # Mock the delete_api_key response
    mock_admin_service.delete_api_key.return_value = {
        "deleted": True,
        "key_id": "key-123"
    }
    
    # Make request
    response = client.delete(
        "/api/admin/api-keys/key-123",
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert data["key_id"] == "key-123"
    
    # Verify service was called
    mock_admin_service.delete_api_key.assert_called_once()


def test_admin_can_test_api_key(mock_admin_auth, mock_admin_service):
    """
    Test that admin can test an API key before storage
    
    Requirements: 14.7
    """
    # Mock the test_api_key response
    mock_admin_service.test_api_key.return_value = {
        "valid": True,
        "message": "API key format appears valid"
    }
    
    # Make request
    response = client.post(
        "/api/admin/api-keys/test",
        json={
            "key": "AIzaSyTest123456789",
            "provider": "gemini"
        },
        headers={"Authorization": "Bearer admin-token"}
    )
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "valid" in data["message"].lower()


def test_non_admin_cannot_access_api_key_endpoints(mock_admin_service):
    """
    Test that non-admin users cannot access API key endpoints
    
    Requirements: 2.7
    """
    # Mock require_admin to raise HTTPException
    from fastapi import HTTPException, status
    
    with patch('main.require_admin') as mock_auth:
        mock_auth.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Admin access required"}}
        )
        
        # Try to list API keys
        response = client.get(
            "/api/admin/api-keys",
            headers={"Authorization": "Bearer user-token"}
        )
        
        # Should be forbidden
        assert response.status_code == 403
