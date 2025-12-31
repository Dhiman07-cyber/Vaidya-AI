"""
Study Planner Service
Handles study session management and planning
Requirements: 6.1, 6.2, 6.3, 6.4
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from supabase import Client, create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class StudyPlannerService:
    """Study planner service for managing study sessions"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the study planner service
        
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
    
    async def create_study_session(
        self,
        user_id: str,
        topic: str,
        duration: int,
        scheduled_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new study session
        
        Args:
            user_id: User's unique identifier
            topic: Study topic/subject
            duration: Duration in minutes
            scheduled_date: Optional scheduled date (ISO format)
            notes: Optional notes about the session
            
        Returns:
            Dict containing session data (id, user_id, topic, duration, etc.)
            
        Raises:
            Exception: If session creation fails
            
        Requirements: 6.1, 6.2
        """
        try:
            session_data = {
                "user_id": user_id,
                "topic": topic,
                "duration": duration,
                "scheduled_date": scheduled_date,
                "notes": notes,
                "status": "planned",  # planned, in_progress, completed, cancelled
                "completed_at": None
            }
            
            response = self.supabase.table("study_sessions").insert(session_data).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception("Failed to create study session")
            
            return response.data[0]
        except Exception as e:
            raise Exception(f"Failed to create study session: {str(e)}")
    
    async def get_study_sessions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get study sessions for a user
        
        Args:
            user_id: User's unique identifier
            status: Optional filter by status (planned, in_progress, completed, cancelled)
            limit: Maximum number of sessions to return
            
        Returns:
            List of study session dictionaries ordered by scheduled_date
            
        Raises:
            Exception: If retrieval fails
            
        Requirements: 6.1, 6.4
        """
        try:
            query = self.supabase.table("study_sessions")\
                .select("*")\
                .eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            
            response = query.order("scheduled_date", desc=False)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get study sessions: {str(e)}")
    
    async def update_study_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a study session
        
        Args:
            session_id: Study session identifier
            user_id: User's unique identifier (for ownership verification)
            data: Dictionary of fields to update
            
        Returns:
            Updated session data
            
        Raises:
            Exception: If update fails or session doesn't belong to user
            
        Requirements: 6.3
        """
        try:
            # Verify session belongs to user
            session_response = self.supabase.table("study_sessions")\
                .select("id")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_response.data or len(session_response.data) == 0:
                raise Exception("Study session not found or does not belong to user")
            
            # Update the session
            response = self.supabase.table("study_sessions")\
                .update(data)\
                .eq("id", session_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception("Failed to update study session")
            
            return response.data[0]
        except Exception as e:
            raise Exception(f"Failed to update study session: {str(e)}")
    
    async def delete_study_session(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Delete a study session
        
        Args:
            session_id: Study session identifier
            user_id: User's unique identifier (for ownership verification)
            
        Returns:
            Deletion confirmation
            
        Raises:
            Exception: If deletion fails or session doesn't belong to user
            
        Requirements: 6.3
        """
        try:
            # Verify session belongs to user
            session_response = self.supabase.table("study_sessions")\
                .select("id")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_response.data or len(session_response.data) == 0:
                raise Exception("Study session not found or does not belong to user")
            
            # Delete the session
            response = self.supabase.table("study_sessions")\
                .delete()\
                .eq("id", session_id)\
                .execute()
            
            return {
                "success": True,
                "message": "Study session deleted successfully",
                "session_id": session_id
            }
        except Exception as e:
            raise Exception(f"Failed to delete study session: {str(e)}")
    
    async def mark_session_completed(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Mark a study session as completed
        
        Args:
            session_id: Study session identifier
            user_id: User's unique identifier
            
        Returns:
            Updated session data
            
        Raises:
            Exception: If update fails
            
        Requirements: 6.4
        """
        try:
            update_data = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
            return await self.update_study_session(session_id, user_id, update_data)
        except Exception as e:
            raise Exception(f"Failed to mark session as completed: {str(e)}")


# Singleton instance for easy import
_study_planner_instance = None


def get_study_planner_service(supabase_client: Optional[Client] = None) -> StudyPlannerService:
    """
    Get or create the study planner service instance
    
    Args:
        supabase_client: Optional Supabase client for dependency injection
        
    Returns:
        StudyPlannerService instance
    """
    global _study_planner_instance
    if _study_planner_instance is None or supabase_client is not None:
        _study_planner_instance = StudyPlannerService(supabase_client)
    return _study_planner_instance
