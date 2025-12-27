"""
Integration tests for admin endpoints

Requirements: 13.1, 13.3, 2.7
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_admin_can_list_users():
    """
    Test that admin can list users
    
    Requirements: 13.1
    """
    # Mock admin authentication
    with patch('main.require_admin') as mock_require_admin:
        mock_require_admin.return_value = "admin-123"
        
        # Mock admin service - patch where it's imported
        with patch('services.admin.get_admin_service') as mock_admin_service_getter:
            mock_admin_service = AsyncMock()
            mock_admin_service.list_users = AsyncMock(return_value=[
                {
                    "id": "user-1",
                    "email": "user1@example.com",
                    "name": "User One",
                    "plan": "free",
                    "role": None,
                    "disabled": False,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "user-2",
                    "email": "user2@example.com",
                    "name": "User Two",
                    "plan": "student",
                    "role": None,
                    "disabled": False,
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ])
            mock_admin_service_getter.return_value = mock_admin_service
            
            # Make request
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": "Bearer admin-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["email"] == "user1@example.com"
            assert data[1]["email"] == "user2@example.com"


def test_admin_can_change_user_plan():
    """
    Test that admin can change user plan
    
    Requirements: 13.3
    """
    # Mock admin authentication
    with patch('main.require_admin') as mock_require_admin:
        mock_require_admin.return_value = "admin-123"
        
        # Mock admin service - patch where it's imported
        with patch('services.admin.get_admin_service') as mock_admin_service_getter:
            mock_admin_service = AsyncMock()
            mock_admin_service.update_user_plan = AsyncMock(return_value={
                "id": "user-1",
                "email": "user1@example.com",
                "name": "User One",
                "plan": "pro",  # Updated plan
                "role": None,
                "disabled": False,
                "created_at": "2024-01-01T00:00:00Z"
            })
            mock_admin_service_getter.return_value = mock_admin_service
            
            # Make request
            response = client.put(
                "/api/admin/users/user-1/plan",
                json={"plan": "pro"},
                headers={"Authorization": "Bearer admin-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "user-1"
            assert data["plan"] == "pro"
            
            # Verify service was called correctly
            mock_admin_service.update_user_plan.assert_called_once_with(
                admin_id="admin-123",
                user_id="user-1",
                new_plan="pro"
            )


def test_non_admin_cannot_access_admin_endpoints():
    """
    Test that non-admin users cannot access admin endpoints
    
    Requirements: 2.7
    """
    # Mock admin authentication to raise 403
    with patch('main.require_admin') as mock_require_admin:
        from fastapi import HTTPException, status
        mock_require_admin.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
        
        # Try to list users
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer user-token"}
        )
        
        # Verify 403 response
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]


def test_admin_can_reset_user_usage():
    """
    Test that admin can reset user usage counters
    
    Requirements: 13.4
    """
    # Mock admin authentication
    with patch('main.require_admin') as mock_require_admin:
        mock_require_admin.return_value = "admin-123"
        
        # Mock admin service - patch where it's imported
        with patch('services.admin.get_admin_service') as mock_admin_service_getter:
            mock_admin_service = AsyncMock()
            mock_admin_service.reset_user_usage = AsyncMock(return_value={
                "user_id": "user-1",
                "date": "2024-01-01",
                "reset": True,
                "usage": {
                    "tokens_used": 0,
                    "requests_count": 0,
                    "pdf_uploads": 0,
                    "mcqs_generated": 0,
                    "images_used": 0,
                    "flashcards_generated": 0
                }
            })
            mock_admin_service_getter.return_value = mock_admin_service
            
            # Make request
            response = client.post(
                "/api/admin/users/user-1/usage/reset",
                headers={"Authorization": "Bearer admin-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-1"
            assert data["reset"] is True
            
            # Verify service was called correctly
            mock_admin_service.reset_user_usage.assert_called_once_with(
                admin_id="admin-123",
                user_id="user-1"
            )


def test_admin_can_disable_user():
    """
    Test that admin can disable user accounts
    
    Requirements: 13.5
    """
    # Mock admin authentication
    with patch('main.require_admin') as mock_require_admin:
        mock_require_admin.return_value = "admin-123"
        
        # Mock admin service - patch where it's imported
        with patch('services.admin.get_admin_service') as mock_admin_service_getter:
            mock_admin_service = AsyncMock()
            mock_admin_service.disable_user = AsyncMock(return_value={
                "id": "user-1",
                "email": "user1@example.com",
                "name": "User One",
                "plan": "free",
                "role": None,
                "disabled": True,  # Now disabled
                "created_at": "2024-01-01T00:00:00Z"
            })
            mock_admin_service_getter.return_value = mock_admin_service
            
            # Make request
            response = client.post(
                "/api/admin/users/user-1/disable?disabled=true",
                headers={"Authorization": "Bearer admin-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "user-1"
            assert data["disabled"] is True
            
            # Verify service was called correctly
            mock_admin_service.disable_user.assert_called_once_with(
                admin_id="admin-123",
                user_id="user-1",
                disabled=True
            )


def test_admin_can_get_audit_logs():
    """
    Test that admin can retrieve audit logs
    
    Requirements: 19.6
    """
    # Mock admin authentication
    with patch('main.require_admin') as mock_require_admin:
        mock_require_admin.return_value = "admin-123"
        
        # Mock audit service - patch where it's imported
        with patch('services.audit.get_audit_service') as mock_audit_service_getter:
            mock_audit_service = AsyncMock()
            mock_audit_service.get_audit_logs = AsyncMock(return_value=[
                {
                    "id": "log-1",
                    "admin_id": "admin-123",
                    "action_type": "update_plan",
                    "target_type": "user",
                    "target_id": "user-1",
                    "details": {"old_plan": "free", "new_plan": "pro"},
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            ])
            mock_audit_service_getter.return_value = mock_audit_service
            
            # Make request
            response = client.get(
                "/api/admin/audit-logs",
                headers={"Authorization": "Bearer admin-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["action_type"] == "update_plan"
            assert data[0]["admin_id"] == "admin-123"
