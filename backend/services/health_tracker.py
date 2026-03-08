"""
Health Tracker Service
Tracks API key health and selects best provider based on health status
Phase 3: Multi-Provider Selection
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import Client

logger = logging.getLogger(__name__)


class HealthTrackerService:
    """Service for tracking API key health and selecting best providers"""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the health tracker service
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
    
    def calculate_health(self, key: Dict[str, Any]) -> str:
        """
        Calculate health status from stats
        
        Args:
            key: Key data with recent_attempts, recent_failures, last_failure_time
            
        Returns:
            Health status: 'healthy', 'recovering', or 'degraded'
        """
        attempts = key.get('recent_attempts', 0)
        failures = key.get('recent_failures', 0)
        
        if attempts < 5:
            return 'healthy'  # Not enough data
        
        failure_rate = failures / attempts
        
        if failure_rate > 0.5:
            # Check if recovering
            last_failure = key.get('last_failure_time')
            if last_failure:
                try:
                    if isinstance(last_failure, str):
                        last_failure_dt = datetime.fromisoformat(last_failure.replace('Z', '+00:00'))
                    else:
                        last_failure_dt = last_failure
                    
                    minutes_ago = (datetime.now(last_failure_dt.tzinfo) - last_failure_dt).total_seconds() / 60
                    if minutes_ago > 10:
                        return 'recovering'
                except Exception as e:
                    logger.warning(f"Error parsing last_failure_time: {e}")
            
            return 'degraded'
        
        return 'healthy'
    
    def health_score(self, key: Dict[str, Any]) -> float:
        """
        Calculate 0-1 health score
        
        Args:
            key: Key data with recent_attempts, recent_successes
            
        Returns:
            Health score between 0.0 and 1.0
        """
        attempts = key.get('recent_attempts', 0)
        successes = key.get('recent_successes', 0)
        
        if attempts == 0:
            return 1.0  # Assume healthy
        
        return successes / attempts
    
    async def get_all_healthy_keys_for_feature(self, feature: str) -> List[Dict[str, Any]]:
        """
        Get ALL active keys for a feature across ALL providers, with health info
        
        Args:
            feature: Feature name (chat, mcq, etc.)
            
        Returns:
            List of keys with health info, sorted by priority DESC
        """
        try:
            # Query ALL providers for this feature
            response = self.supabase.table("api_keys") \
                .select("*") \
                .eq("feature", feature) \
                .eq("status", "active") \
                .order("priority", desc=True) \
                .execute()
            
            if not response.data:
                logger.warning(f"No active keys found for feature: {feature}")
                return []
            
            # Calculate health for each key
            healthy_keys = []
            for key in response.data:
                health = self.calculate_health(key)
                
                # Only include healthy or recovering keys
                if health in ['healthy', 'recovering']:
                    from services.encryption import decrypt_key
                    
                    try:
                        decrypted_key = decrypt_key(key["key_value"])
                        
                        healthy_keys.append({
                            "id": key["id"],
                            "provider": key["provider"],
                            "feature": key["feature"],
                            "key_value": decrypted_key,
                            "priority": key["priority"],
                            "status": key["status"],
                            "health_status": health,
                            "health_score": self.health_score(key),
                            "recent_attempts": key.get("recent_attempts", 0),
                            "recent_successes": key.get("recent_successes", 0),
                            "recent_failures": key.get("recent_failures", 0)
                        })
                    except Exception as decrypt_error:
                        logger.error(f"Failed to decrypt key {key['id']}: {decrypt_error}")
                        continue
            
            logger.info(
                f"Found {len(healthy_keys)} healthy keys for feature '{feature}' "
                f"across {len(set(k['provider'] for k in healthy_keys))} providers"
            )
            
            return healthy_keys
            
        except Exception as e:
            logger.error(f"Failed to get healthy keys: {str(e)}")
            return []
    
    async def select_best_provider(
        self,
        feature: str,
        session_preference: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select best API provider considering:
        1. Session cache preference
        2. Global health status
        3. Priority ranking
        
        Args:
            feature: Feature name
            session_preference: Optional provider name from session cache
            
        Returns:
            Best key dict or None if no keys available
        """
        # Get ALL healthy keys for this feature (all providers)
        healthy_keys = await self.get_all_healthy_keys_for_feature(feature)
        
        if not healthy_keys:
            logger.error(f"No healthy keys available for feature: {feature}")
            return None
        
        # Check session preference
        if session_preference:
            preferred = [k for k in healthy_keys if k['provider'] == session_preference]
            
            if preferred:
                # Check if we should override
                paid_keys = [k for k in healthy_keys if k['provider'] != 'huggingface']
                
                if paid_keys and paid_keys[0]['health_score'] > 0.8:
                    # Paid API recovered, override session
                    logger.info(
                        f"Overriding session preference '{session_preference}' "
                        f"with recovered paid API '{paid_keys[0]['provider']}'"
                    )
                    return paid_keys[0]
                else:
                    # Use session preference
                    logger.info(f"Using session preference: {session_preference}")
                    return preferred[0]
        
        # No preference or preference not healthy
        # Select highest priority healthy key
        if healthy_keys:
            best_key = healthy_keys[0]  # Already sorted by priority
            logger.info(
                f"Selected provider '{best_key['provider']}' for feature '{feature}' "
                f"(priority: {best_key['priority']}, health: {best_key['health_score']:.2f})"
            )
            return best_key
        
        return None
    
    async def update_key_health(
        self,
        key_id: str,
        success: bool,
        response_time_ms: Optional[int] = None
    ) -> None:
        """
        Update health tracking stats for an API key
        
        Args:
            key_id: API key ID
            success: Whether the call succeeded
            response_time_ms: Optional response time in milliseconds
        """
        try:
            # Get current stats
            response = self.supabase.table("api_keys") \
                .select("recent_attempts, recent_successes, recent_failures") \
                .eq("id", key_id) \
                .execute()
            
            if not response.data:
                logger.warning(f"Key {key_id} not found for health update")
                return
            
            current = response.data[0]
            attempts = current.get("recent_attempts", 0) + 1
            successes = current.get("recent_successes", 0) + (1 if success else 0)
            failures = current.get("recent_failures", 0) + (0 if success else 1)
            
            # Calculate health status
            failure_rate = failures / attempts if attempts > 0 else 0
            if failure_rate > 0.5:
                health_status = 'degraded'
            elif failure_rate > 0.2:
                health_status = 'recovering'
            else:
                health_status = 'healthy'
            
            health_score = successes / attempts if attempts > 0 else 1.0
            
            # Update stats
            update_data = {
                "recent_attempts": attempts,
                "recent_successes": successes,
                "recent_failures": failures,
                "health_status": health_status,
                "health_score": health_score
            }
            
            if success:
                update_data["last_success_time"] = datetime.utcnow().isoformat()
            else:
                update_data["last_failure_time"] = datetime.utcnow().isoformat()
            
            self.supabase.table("api_keys") \
                .update(update_data) \
                .eq("id", key_id) \
                .execute()
            
            logger.info(
                f"Updated health for key {key_id}: "
                f"attempts={attempts}, successes={successes}, failures={failures}, "
                f"health={health_status}, score={health_score:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update key health: {str(e)}")
    
    async def reset_health_stats(self, key_id: str) -> None:
        """
        Reset health stats for a key (useful for recovery)
        
        Args:
            key_id: API key ID
        """
        try:
            self.supabase.table("api_keys") \
                .update({
                    "recent_attempts": 0,
                    "recent_successes": 0,
                    "recent_failures": 0,
                    "health_status": "healthy",
                    "health_score": 1.0
                }) \
                .eq("id", key_id) \
                .execute()
            
            logger.info(f"Reset health stats for key {key_id}")
            
        except Exception as e:
            logger.error(f"Failed to reset health stats: {str(e)}")


# Singleton instance
_health_tracker_service: Optional[HealthTrackerService] = None


def get_health_tracker_service(supabase_client: Client) -> HealthTrackerService:
    """Get or create singleton health tracker service instance"""
    global _health_tracker_service
    
    if _health_tracker_service is None or supabase_client is not None:
        _health_tracker_service = HealthTrackerService(supabase_client)
    
    return _health_tracker_service
