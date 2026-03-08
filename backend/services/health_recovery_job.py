"""
Health Recovery Background Job
Periodically checks degraded keys for recovery and resets stats
Phase 4: Health Tracking
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from supabase import Client, create_client
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class HealthRecoveryJob:
    """Background job for checking and recovering degraded API keys"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the health recovery job
        
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
        
        self.running = False
        self.check_interval = 300  # 5 minutes
    
    async def check_degraded_keys(self) -> None:
        """
        Check all degraded keys and reset stats if they've been idle long enough
        """
        try:
            # Get all degraded keys
            response = self.supabase.table("api_keys") \
                .select("*") \
                .eq("health_status", "degraded") \
                .execute()
            
            if not response.data:
                logger.debug("No degraded keys found")
                return
            
            logger.info(f"Checking {len(response.data)} degraded keys for recovery")
            
            now = datetime.utcnow()
            recovery_threshold = timedelta(minutes=15)  # 15 minutes idle = recovery
            
            for key in response.data:
                last_failure = key.get("last_failure_time")
                
                if not last_failure:
                    # No failure time recorded, reset immediately
                    await self._reset_key_health(key["id"], key["provider"], key["feature"])
                    continue
                
                try:
                    if isinstance(last_failure, str):
                        last_failure_dt = datetime.fromisoformat(last_failure.replace('Z', '+00:00'))
                    else:
                        last_failure_dt = last_failure
                    
                    # Remove timezone info for comparison
                    if last_failure_dt.tzinfo:
                        last_failure_dt = last_failure_dt.replace(tzinfo=None)
                    
                    time_since_failure = now - last_failure_dt
                    
                    if time_since_failure > recovery_threshold:
                        # Key has been idle long enough, reset health
                        await self._reset_key_health(key["id"], key["provider"], key["feature"])
                        logger.info(
                            f"Reset health for key {key['id']} (provider: {key['provider']}, "
                            f"feature: {key['feature']}) - idle for {time_since_failure.total_seconds() / 60:.1f} minutes"
                        )
                    else:
                        remaining = recovery_threshold - time_since_failure
                        logger.debug(
                            f"Key {key['id']} still degraded - {remaining.total_seconds() / 60:.1f} minutes until recovery"
                        )
                
                except Exception as e:
                    logger.error(f"Error processing key {key['id']}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error checking degraded keys: {str(e)}")
    
    async def _reset_key_health(self, key_id: str, provider: str, feature: str) -> None:
        """
        Reset health stats for a key
        
        Args:
            key_id: API key ID
            provider: Provider name
            feature: Feature name
        """
        try:
            self.supabase.table("api_keys") \
                .update({
                    "recent_attempts": 0,
                    "recent_successes": 0,
                    "recent_failures": 0,
                    "health_status": "healthy",
                    "health_score": 1.0,
                    "failure_count": 0
                }) \
                .eq("id", key_id) \
                .execute()
            
            logger.info(f"Reset health stats for key {key_id} (provider: {provider}, feature: {feature})")
            
        except Exception as e:
            logger.error(f"Failed to reset health stats for key {key_id}: {str(e)}")
    
    async def run(self) -> None:
        """
        Run the health recovery job continuously
        """
        self.running = True
        logger.info(f"Health recovery job started (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_degraded_keys()
            except Exception as e:
                logger.error(f"Error in health recovery job: {str(e)}")
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)
    
    def stop(self) -> None:
        """Stop the health recovery job"""
        self.running = False
        logger.info("Health recovery job stopped")


# Global job instance
_health_recovery_job: Optional[HealthRecoveryJob] = None


def get_health_recovery_job(supabase_client: Optional[Client] = None) -> HealthRecoveryJob:
    """Get or create singleton health recovery job instance"""
    global _health_recovery_job
    
    if _health_recovery_job is None or supabase_client is not None:
        _health_recovery_job = HealthRecoveryJob(supabase_client)
    
    return _health_recovery_job


async def start_health_recovery_job() -> None:
    """Start the health recovery background job"""
    job = get_health_recovery_job()
    await job.run()


if __name__ == "__main__":
    # Run the job standalone
    asyncio.run(start_health_recovery_job())
