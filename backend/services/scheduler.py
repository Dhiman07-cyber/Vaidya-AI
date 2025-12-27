"""
Scheduler Service
Handles scheduled jobs like daily counter resets
Requirements: 9.4
"""
import os
from typing import Optional
from datetime import date, datetime, timezone
from supabase import Client, create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Scheduler:
    """Scheduler service for managing scheduled tasks"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the scheduler service
        
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
    
    async def reset_daily_counters(self) -> dict:
        """
        Reset daily usage counters at midnight UTC
        
        This function is designed to be called by a scheduled job (e.g., cron)
        at midnight UTC each day. It doesn't delete old records, allowing for
        historical usage tracking, but ensures new day starts with fresh counters.
        
        Returns:
            Dict with reset statistics (counters_reset count)
            
        Requirements: 9.4
        """
        try:
            today = date.today()
            
            # Note: We don't delete old usage_counters records to maintain history
            # The rate limiter automatically creates new records for today when needed
            # This function is mainly for verification and logging purposes
            
            # Get count of users with usage records from previous days
            # (to track how many users will get fresh counters today)
            yesterday = date.today().replace(day=date.today().day - 1) if date.today().day > 1 else date.today()
            
            response = self.supabase.table("usage_counters")\
                .select("user_id", count="exact")\
                .lt("date", str(today))\
                .execute()
            
            previous_day_users = response.count if hasattr(response, 'count') else 0
            
            return {
                "reset_date": str(today),
                "reset_time": datetime.now(timezone.utc).isoformat(),
                "users_with_previous_usage": previous_day_users,
                "status": "success",
                "message": f"Daily counters reset for {today}. Users will get fresh counters on next request."
            }
            
        except Exception as e:
            return {
                "reset_date": str(date.today()),
                "reset_time": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "message": f"Failed to reset daily counters: {str(e)}"
            }


# Singleton instance for easy import
_scheduler_instance = None


def get_scheduler(supabase_client: Optional[Client] = None) -> Scheduler:
    """
    Get or create the scheduler service instance
    
    Args:
        supabase_client: Optional Supabase client for dependency injection
        
    Returns:
        Scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None or supabase_client is not None:
        _scheduler_instance = Scheduler(supabase_client)
    return _scheduler_instance
