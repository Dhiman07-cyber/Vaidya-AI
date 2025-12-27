"""
Maintenance Service

Manages system maintenance mode and triggers.
Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.8, 12.9
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from supabase import Client
from services.notifications import get_notification_service

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Service for managing system maintenance mode"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def evaluate_maintenance_trigger(
        self,
        feature: str,
        failures: int
    ) -> Optional[str]:
        """
        Evaluate if maintenance mode should be triggered
        
        Args:
            feature: Feature that experienced failures
            failures: Number of consecutive failures
            
        Returns:
            Maintenance level to trigger (soft, hard) or None
            
        Requirements: 12.1, 12.2, 12.3
        """
        # Get all keys for this feature
        keys_result = self.supabase.table("api_keys") \
            .select("id, status, provider") \
            .eq("feature", feature) \
            .execute()
        
        if not keys_result.data:
            # No keys configured for this feature
            logger.warning(f"No API keys configured for feature: {feature}")
            return "soft"
        
        # Count active and degraded keys
        active_keys = sum(1 for k in keys_result.data if k["status"] == "active")
        degraded_keys = sum(1 for k in keys_result.data if k["status"] == "degraded")
        
        # If all keys are failed/disabled (no active or degraded keys)
        if active_keys == 0 and degraded_keys == 0:
            logger.error(f"All keys failed for feature: {feature}")
            return "hard"
        
        # If only degraded keys remain (no active keys)
        if active_keys == 0 and degraded_keys > 0:
            logger.warning(f"Only degraded keys remain for feature: {feature}")
            return "soft"
        
        # If we have active keys but high failure rate
        if failures >= 5:
            logger.warning(f"High failure rate for feature: {feature}")
            return "soft"
        
        # No maintenance needed
        return None
    
    async def enter_maintenance(
        self,
        level: str,
        reason: str,
        feature: Optional[str] = None,
        triggered_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enter maintenance mode
        
        Args:
            level: Maintenance level (soft or hard)
            reason: Reason for entering maintenance
            feature: Optional feature that triggered maintenance
            triggered_by: Optional admin ID if manually triggered
            
        Returns:
            Dict with maintenance status
            
        Requirements: 12.4, 12.5, 12.6
        """
        if level not in ["soft", "hard"]:
            raise ValueError(f"Invalid maintenance level: {level}. Must be 'soft' or 'hard'")
        
        # Check if already in maintenance
        current_status = await self.get_maintenance_status()
        if current_status["in_maintenance"]:
            logger.warning(f"Already in {current_status['level']} maintenance mode")
            # If upgrading from soft to hard, allow it
            if current_status["level"] == "soft" and level == "hard":
                logger.info("Upgrading from soft to hard maintenance")
            else:
                return current_status
        
        # Create maintenance record
        maintenance_data = {
            "level": level,
            "reason": reason,
            "feature": feature,
            "triggered_by": triggered_by,
            "triggered_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        # Store in system_flags table
        flag_name = "maintenance_mode"
        flag_value = maintenance_data
        
        # Check if flag exists
        existing_flag = self.supabase.table("system_flags") \
            .select("id") \
            .eq("flag_name", flag_name) \
            .execute()
        
        if existing_flag.data:
            # Update existing flag
            self.supabase.table("system_flags") \
                .update({
                    "flag_value": str(flag_value),
                    "updated_at": datetime.now().isoformat(),
                    "updated_by": triggered_by
                }) \
                .eq("flag_name", flag_name) \
                .execute()
        else:
            # Insert new flag
            self.supabase.table("system_flags") \
                .insert({
                    "flag_name": flag_name,
                    "flag_value": str(flag_value),
                    "updated_by": triggered_by,
                    "updated_at": datetime.now().isoformat()
                }) \
                .execute()
        
        logger.info(f"Entered {level} maintenance mode: {reason}")
        
        # Send notification to admins (Requirement 12.9)
        try:
            notification_service = get_notification_service()
            await notification_service.notify_maintenance_triggered(
                level=level,
                reason=reason,
                feature=feature
            )
        except Exception as notif_error:
            logger.warning(f"Failed to send maintenance notification: {str(notif_error)}")
        
        return {
            "in_maintenance": True,
            "level": level,
            "reason": reason,
            "feature": feature,
            "triggered_by": triggered_by,
            "triggered_at": maintenance_data["triggered_at"]
        }
    
    async def exit_maintenance(
        self,
        exited_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exit maintenance mode
        
        Args:
            exited_by: Optional admin ID who exited maintenance
            
        Returns:
            Dict with updated maintenance status
            
        Requirements: 12.8
        """
        # Get current maintenance status
        current_status = await self.get_maintenance_status()
        
        if not current_status["in_maintenance"]:
            logger.info("Not in maintenance mode, nothing to exit")
            return {
                "in_maintenance": False,
                "message": "Not in maintenance mode"
            }
        
        # Update system_flags to mark maintenance as inactive
        flag_name = "maintenance_mode"
        
        # Get current flag value
        flag_result = self.supabase.table("system_flags") \
            .select("flag_value") \
            .eq("flag_name", flag_name) \
            .execute()
        
        if flag_result.data:
            # Parse and update the flag value
            import ast
            flag_value = ast.literal_eval(flag_result.data[0]["flag_value"])
            flag_value["is_active"] = False
            flag_value["exited_at"] = datetime.now().isoformat()
            flag_value["exited_by"] = exited_by
            
            self.supabase.table("system_flags") \
                .update({
                    "flag_value": str(flag_value),
                    "updated_at": datetime.now().isoformat(),
                    "updated_by": exited_by
                }) \
                .eq("flag_name", flag_name) \
                .execute()
        
        logger.info("Exited maintenance mode")
        
        # Send notification if manually exited by admin
        if exited_by:
            try:
                notification_service = get_notification_service()
                await notification_service.notify_admin_override(
                    admin_id=exited_by,
                    action="exit_maintenance",
                    details={
                        "previous_level": current_status.get("level"),
                        "previous_reason": current_status.get("reason")
                    }
                )
            except Exception as notif_error:
                logger.warning(f"Failed to send exit notification: {str(notif_error)}")
        
        return {
            "in_maintenance": False,
            "message": "Maintenance mode exited",
            "exited_by": exited_by,
            "exited_at": datetime.now().isoformat()
        }
    
    async def get_maintenance_status(self) -> Dict[str, Any]:
        """
        Get current maintenance status
        
        Returns:
            Dict with maintenance status information
            
        Requirements: 12.4
        """
        # Query system_flags table
        flag_name = "maintenance_mode"
        result = self.supabase.table("system_flags") \
            .select("flag_value, updated_at") \
            .eq("flag_name", flag_name) \
            .execute()
        
        if not result.data:
            # No maintenance flag exists
            return {
                "in_maintenance": False,
                "level": None,
                "reason": None,
                "feature": None,
                "triggered_by": None,
                "triggered_at": None
            }
        
        # Parse flag value
        import ast
        try:
            flag_value = ast.literal_eval(result.data[0]["flag_value"])
            
            # Check if maintenance is active
            is_active = flag_value.get("is_active", False)
            
            if not is_active:
                return {
                    "in_maintenance": False,
                    "level": None,
                    "reason": None,
                    "feature": None,
                    "triggered_by": None,
                    "triggered_at": None
                }
            
            return {
                "in_maintenance": True,
                "level": flag_value.get("level"),
                "reason": flag_value.get("reason"),
                "feature": flag_value.get("feature"),
                "triggered_by": flag_value.get("triggered_by"),
                "triggered_at": flag_value.get("triggered_at")
            }
        except Exception as e:
            logger.error(f"Failed to parse maintenance flag: {str(e)}")
            return {
                "in_maintenance": False,
                "level": None,
                "reason": None,
                "feature": None,
                "triggered_by": None,
                "triggered_at": None
            }


# Singleton instance
_maintenance_service_instance: Optional[MaintenanceService] = None


def get_maintenance_service(supabase_client: Client) -> MaintenanceService:
    """Get or create maintenance service instance"""
    global _maintenance_service_instance
    if _maintenance_service_instance is None:
        _maintenance_service_instance = MaintenanceService(supabase_client)
    return _maintenance_service_instance
