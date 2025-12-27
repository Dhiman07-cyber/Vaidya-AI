"""
Admin Authentication Middleware
Verifies admin access for protected admin routes

Requirements: 2.2, 2.6, 2.7
"""
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from supabase import Client, create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AdminAuthMiddleware:
    """Middleware for verifying admin access"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize admin auth middleware
        
        Args:
            supabase_client: Optional Supabase client for dependency injection
        """
        if supabase_client:
            self.supabase = supabase_client
        else:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
            self.supabase = create_client(supabase_url, supabase_key)
    
    async def verify_admin_access(self, user_id: str, token: Optional[str] = None) -> bool:
        """
        Verify if a user has admin access
        
        Checks:
        1. Emergency admin token (if provided)
        2. Admin allowlist table for email and role
        
        Args:
            user_id: User's unique identifier
            token: Optional emergency admin token
            
        Returns:
            True if user has admin access, False otherwise
            
        Requirements: 2.2, 2.6, 2.7
        """
        try:
            # Check emergency admin token first (Requirement 2.6)
            if token:
                emergency_token = os.getenv("EMERGENCY_ADMIN_TOKEN")
                if emergency_token and token == emergency_token:
                    return True
            
            # Get user email and role
            user_response = self.supabase.table("users").select("email, role").eq("id", user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                return False
            
            user_email = user_response.data[0]["email"]
            user_role = user_response.data[0].get("role")
            
            # Check SUPER_ADMIN_EMAIL environment variable (Requirement 2.4)
            super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
            if super_admin_email and user_email == super_admin_email:
                return True
            
            # Check admin_allowlist table (Requirement 2.2)
            allowlist_response = self.supabase.table("admin_allowlist")\
                .select("role")\
                .eq("email", user_email)\
                .execute()
            
            if allowlist_response.data and len(allowlist_response.data) > 0:
                allowlist_role = allowlist_response.data[0]["role"]
                # User must be in allowlist AND have a role
                if allowlist_role and user_role:
                    return True
            
            return False
        except Exception as e:
            # Log error but don't expose details
            print(f"Admin access verification error: {str(e)}")
            return False
    
    async def require_admin(self, request: Request, user_id: str) -> None:
        """
        Require admin access for a request
        
        Raises HTTPException with 403 status if user is not admin
        
        Args:
            request: FastAPI request object
            user_id: User's unique identifier
            
        Raises:
            HTTPException: 403 Forbidden if user is not admin
            
        Requirements: 2.7
        """
        # Check for emergency admin token in headers
        emergency_token = request.headers.get("X-Emergency-Admin-Token")
        
        is_admin = await self.verify_admin_access(user_id, emergency_token)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )


# Singleton instance
_admin_auth_middleware_instance = None


def get_admin_auth_middleware(supabase_client: Optional[Client] = None) -> AdminAuthMiddleware:
    """
    Get or create admin auth middleware instance
    
    Args:
        supabase_client: Optional Supabase client for dependency injection
        
    Returns:
        AdminAuthMiddleware instance
    """
    global _admin_auth_middleware_instance
    if _admin_auth_middleware_instance is None or supabase_client is not None:
        _admin_auth_middleware_instance = AdminAuthMiddleware(supabase_client)
    return _admin_auth_middleware_instance
