"""
Property-based tests for admin authentication middleware

Requirements: 2.6, 2.7
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, patch
from middleware.admin_auth import get_admin_auth_middleware
from fastapi import HTTPException


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    emergency_token=st.text(min_size=10, max_size=100, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_emergency_admin_token_grants_access(user_id, emergency_token):
    """
    Property 4: Emergency admin token grants access
    
    Tests that providing a valid emergency admin token grants admin access
    regardless of user's actual admin status.
    
    Requirements: 2.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock environment variable for emergency token
    with patch.dict('os.environ', {'EMERGENCY_ADMIN_TOKEN': emergency_token}):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that providing the correct emergency token grants access
        has_access = await middleware.verify_admin_access(user_id, emergency_token)
        
        # Property: Emergency token always grants access
        assert has_access is True, "Emergency admin token should grant access"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    wrong_token=st.text(min_size=10, max_size=100, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_wrong_emergency_token_denies_access(user_id, wrong_token):
    """
    Property: Wrong emergency admin token denies access
    
    Tests that providing an incorrect emergency admin token does not grant access.
    
    Requirements: 2.6
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock user lookup - non-admin user
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"email": "user@example.com", "role": None}]
    )
    
    # Mock allowlist lookup - user not in allowlist
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[]
    )
    
    # Set a different emergency token
    correct_token = "correct_emergency_token_12345"
    
    with patch.dict('os.environ', {'EMERGENCY_ADMIN_TOKEN': correct_token}):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that providing wrong token denies access
        has_access = await middleware.verify_admin_access(user_id, wrong_token)
        
        # Property: Wrong emergency token should not grant access
        assert has_access is False, "Wrong emergency token should not grant access"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    user_email=st.emails()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_non_admin_users_cannot_access_admin_routes(user_id, user_email):
    """
    Property 5: Non-admin users cannot access admin routes
    
    Tests that users who are not in the admin allowlist and don't have
    admin role cannot access admin routes.
    
    Requirements: 2.7
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock user lookup - non-admin user
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"email": user_email, "role": None}]
    )
    
    # Mock allowlist lookup - user not in allowlist
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[]
    )
    
    # Clear super admin email
    with patch.dict('os.environ', {'SUPER_ADMIN_EMAIL': ''}, clear=True):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that non-admin user is denied access
        has_access = await middleware.verify_admin_access(user_id)
        
        # Property: Non-admin users should not have access
        assert has_access is False, "Non-admin users should not have admin access"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    user_email=st.emails(),
    admin_role=st.sampled_from(['admin', 'super_admin', 'moderator'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_admin_users_can_access_admin_routes(user_id, user_email, admin_role):
    """
    Property: Admin users can access admin routes
    
    Tests that users who are in the admin allowlist with a valid role
    can access admin routes.
    
    Requirements: 2.2, 2.7
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock user lookup - admin user with role
    mock_user_response = Mock(
        data=[{"email": user_email, "role": admin_role}]
    )
    
    # Mock allowlist lookup - user in allowlist with role
    mock_allowlist_response = Mock(
        data=[{"role": admin_role}]
    )
    
    # Set up mock to return different responses for different table calls
    def mock_table_call(table_name):
        mock_table = Mock()
        if table_name == "users":
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_user_response
        elif table_name == "admin_allowlist":
            mock_table.select.return_value.eq.return_value.execute.return_value = mock_allowlist_response
        return mock_table
    
    mock_supabase.table.side_effect = mock_table_call
    
    # Clear super admin email
    with patch.dict('os.environ', {'SUPER_ADMIN_EMAIL': ''}, clear=True):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that admin user has access
        has_access = await middleware.verify_admin_access(user_id)
        
        # Property: Admin users should have access
        assert has_access is True, "Admin users should have admin access"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00')),
    super_admin_email=st.emails()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_super_admin_email_grants_access(user_id, super_admin_email):
    """
    Property: SUPER_ADMIN_EMAIL environment variable grants access
    
    Tests that users whose email matches SUPER_ADMIN_EMAIL have admin access.
    
    Requirements: 2.4
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock user lookup - user with super admin email
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"email": super_admin_email, "role": None}]
    )
    
    with patch.dict('os.environ', {'SUPER_ADMIN_EMAIL': super_admin_email}):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that super admin email grants access
        has_access = await middleware.verify_admin_access(user_id)
        
        # Property: Super admin email should grant access
        assert has_access is True, "SUPER_ADMIN_EMAIL should grant admin access"


@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters='\x00'))
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_require_admin_raises_403_for_non_admin(user_id):
    """
    Property: require_admin raises 403 for non-admin users
    
    Tests that the require_admin method raises HTTPException with 403 status
    for non-admin users.
    
    Requirements: 2.7
    """
    # Mock Supabase client
    mock_supabase = Mock()
    
    # Mock user lookup - non-admin user
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[{"email": "user@example.com", "role": None}]
    )
    
    # Mock allowlist lookup - user not in allowlist
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[]
    )
    
    # Mock request
    mock_request = Mock()
    mock_request.headers.get.return_value = None
    
    with patch.dict('os.environ', {'SUPER_ADMIN_EMAIL': ''}, clear=True):
        middleware = get_admin_auth_middleware(mock_supabase)
        
        # Verify that require_admin raises HTTPException with 403
        with pytest.raises(HTTPException) as exc_info:
            await middleware.require_admin(mock_request, user_id)
        
        # Property: Non-admin access should raise 403
        assert exc_info.value.status_code == 403, "Non-admin access should return 403"
        assert "Admin privileges required" in exc_info.value.detail
