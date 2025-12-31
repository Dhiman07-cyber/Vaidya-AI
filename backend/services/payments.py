"""
Payment Service
Handles Razorpay integration for subscriptions and payments
Requirements: 24.1, 24.2, 24.3, 24.4, 24.6, 24.7
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from supabase import Client, create_client
from dotenv import load_dotenv
import hmac
import hashlib

# Load environment variables
load_dotenv()


class PaymentService:
    """Payment service for managing subscriptions and payments via Razorpay"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize the payment service
        
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
        
        # Razorpay configuration
        self.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
        self.razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    
    async def create_subscription(
        self,
        user_id: str,
        plan: str,
        razorpay_subscription_id: str
    ) -> Dict[str, Any]:
        """
        Create a new subscription record
        
        Args:
            user_id: User's unique identifier
            plan: Subscription plan (student, pro)
            razorpay_subscription_id: Razorpay subscription ID
            
        Returns:
            Dict containing subscription data
            
        Raises:
            Exception: If subscription creation fails
            
        Requirements: 24.1, 24.2
        """
        try:
            # Calculate subscription period (30 days)
            now = datetime.now(timezone.utc)
            period_end = now + timedelta(days=30)
            
            subscription_data = {
                "user_id": user_id,
                "plan": plan,
                "razorpay_subscription_id": razorpay_subscription_id,
                "status": "active",
                "current_period_start": now.isoformat(),
                "current_period_end": period_end.isoformat()
            }
            
            response = self.supabase.table("subscriptions").insert(subscription_data).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception("Failed to create subscription")
            
            return response.data[0]
        except Exception as e:
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    async def handle_payment_webhook(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Razorpay webhook notifications
        
        Verifies webhook signature and processes payment events.
        Updates user plan on successful payment.
        
        Args:
            payload: Webhook payload from Razorpay
            signature: Webhook signature for verification
            
        Returns:
            Dict containing processing result
            
        Raises:
            Exception: If webhook processing fails
            
        Requirements: 24.3, 24.6
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload, signature):
                raise Exception("Invalid webhook signature")
            
            event = payload.get("event")
            
            if event == "payment.captured":
                # Payment successful
                payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
                
                razorpay_payment_id = payment_entity.get("id")
                amount = payment_entity.get("amount")  # Amount in paise
                subscription_id = payment_entity.get("subscription_id")
                
                # Get subscription details
                subscription_response = self.supabase.table("subscriptions")\
                    .select("*")\
                    .eq("razorpay_subscription_id", subscription_id)\
                    .execute()
                
                if not subscription_response.data or len(subscription_response.data) == 0:
                    raise Exception("Subscription not found")
                
                subscription = subscription_response.data[0]
                user_id = subscription["user_id"]
                plan = subscription["plan"]
                
                # Record payment
                payment_data = {
                    "user_id": user_id,
                    "subscription_id": subscription["id"],
                    "razorpay_payment_id": razorpay_payment_id,
                    "amount": amount,
                    "currency": "INR",
                    "status": "success"
                }
                
                self.supabase.table("payments").insert(payment_data).execute()
                
                # Update user plan (Requirement 24.3)
                self.supabase.table("users")\
                    .update({"plan": plan})\
                    .eq("id", user_id)\
                    .execute()
                
                return {
                    "success": True,
                    "message": "Payment processed successfully",
                    "user_id": user_id,
                    "plan": plan
                }
            
            elif event == "subscription.cancelled":
                # Subscription cancelled
                subscription_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
                razorpay_subscription_id = subscription_entity.get("id")
                
                # Update subscription status
                self.supabase.table("subscriptions")\
                    .update({"status": "cancelled"})\
                    .eq("razorpay_subscription_id", razorpay_subscription_id)\
                    .execute()
                
                return {
                    "success": True,
                    "message": "Subscription cancelled"
                }
            
            else:
                return {
                    "success": True,
                    "message": f"Event {event} acknowledged"
                }
                
        except Exception as e:
            raise Exception(f"Failed to handle payment webhook: {str(e)}")
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Subscription identifier
            user_id: User's unique identifier (for ownership verification)
            
        Returns:
            Cancellation confirmation
            
        Raises:
            Exception: If cancellation fails
            
        Requirements: 24.7
        """
        try:
            # Verify subscription belongs to user
            subscription_response = self.supabase.table("subscriptions")\
                .select("*")\
                .eq("id", subscription_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not subscription_response.data or len(subscription_response.data) == 0:
                raise Exception("Subscription not found or does not belong to user")
            
            subscription = subscription_response.data[0]
            
            # Update subscription status
            self.supabase.table("subscriptions")\
                .update({"status": "cancelled"})\
                .eq("id", subscription_id)\
                .execute()
            
            # Note: In production, you would also call Razorpay API to cancel the subscription
            # razorpay_client.subscription.cancel(subscription["razorpay_subscription_id"])
            
            return {
                "success": True,
                "message": "Subscription cancelled successfully",
                "subscription_id": subscription_id
            }
        except Exception as e:
            raise Exception(f"Failed to cancel subscription: {str(e)}")
    
    async def check_expired_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Check for expired subscriptions and downgrade users
        
        This should be run as a scheduled job (e.g., daily).
        
        Returns:
            List of users whose plans were downgraded
            
        Requirements: 24.4
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            # Get expired subscriptions
            expired_response = self.supabase.table("subscriptions")\
                .select("*")\
                .eq("status", "active")\
                .lt("current_period_end", now)\
                .execute()
            
            downgraded_users = []
            
            if expired_response.data:
                for subscription in expired_response.data:
                    user_id = subscription["user_id"]
                    
                    # Update subscription status
                    self.supabase.table("subscriptions")\
                        .update({"status": "expired"})\
                        .eq("id", subscription["id"])\
                        .execute()
                    
                    # Downgrade user to free plan (Requirement 24.4)
                    self.supabase.table("users")\
                        .update({"plan": "free"})\
                        .eq("id", user_id)\
                        .execute()
                    
                    downgraded_users.append({
                        "user_id": user_id,
                        "previous_plan": subscription["plan"],
                        "subscription_id": subscription["id"]
                    })
            
            return downgraded_users
        except Exception as e:
            raise Exception(f"Failed to check expired subscriptions: {str(e)}")
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature
        
        Args:
            payload: Webhook payload
            signature: Signature from Razorpay
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.razorpay_webhook_secret:
            # In development, skip signature verification if secret not set
            return True
        
        try:
            import json
            payload_str = json.dumps(payload, separators=(',', ':'))
            
            expected_signature = hmac.new(
                self.razorpay_webhook_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False


# Singleton instance for easy import
_payment_service_instance = None


def get_payment_service(supabase_client: Optional[Client] = None) -> PaymentService:
    """
    Get or create the payment service instance
    
    Args:
        supabase_client: Optional Supabase client for dependency injection
        
    Returns:
        PaymentService instance
    """
    global _payment_service_instance
    if _payment_service_instance is None or supabase_client is not None:
        _payment_service_instance = PaymentService(supabase_client)
    return _payment_service_instance
