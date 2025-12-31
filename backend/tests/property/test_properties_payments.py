"""
Property-Based Tests for Payment Service
Tests universal properties related to payment and subscription functionality
Feature: medical-ai-platform
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import MagicMock, AsyncMock
from services.payments import PaymentService
import uuid


# Custom strategies for generating test data
def valid_plan():
    """Generate valid subscription plans"""
    return st.sampled_from(["student", "pro"])


def valid_amount():
    """Generate valid payment amounts in paise (100 paise = 1 INR)"""
    return st.integers(min_value=10000, max_value=1000000)  # 100 to 10000 INR


# Feature: medical-ai-platform, Property 57: Payment success updates user plan
@given(
    plan=valid_plan(),
    amount=valid_amount()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_payment_success_updates_plan_property(plan, amount):
    """
    Property 57: For any successful payment webhook from Razorpay, 
    the user's plan should be updated to the purchased plan.
    
    This property verifies that:
    1. Successful payments trigger plan updates
    2. User plan matches the subscription plan
    3. Payment is recorded in the database
    
    Validates: Requirements 24.3
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    subscription_id = str(uuid.uuid4())
    razorpay_subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
    razorpay_payment_id = f"pay_{uuid.uuid4().hex[:14]}"
    
    # Mock subscription lookup
    mock_subscription_response = MagicMock()
    mock_subscription_response.data = [{
        "id": subscription_id,
        "user_id": user_id,
        "plan": plan,
        "razorpay_subscription_id": razorpay_subscription_id,
        "status": "active"
    }]
    
    # Mock payment insert
    mock_payment_insert_response = MagicMock()
    mock_payment_insert_response.data = [{
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "subscription_id": subscription_id,
        "razorpay_payment_id": razorpay_payment_id,
        "amount": amount,
        "status": "success"
    }]
    
    # Mock user update
    mock_user_update_response = MagicMock()
    mock_user_update_response.data = [{
        "id": user_id,
        "plan": plan
    }]
    
    # Track what plan was set
    updated_plan = None
    
    def mock_user_update(data):
        nonlocal updated_plan
        updated_plan = data.get("plan")
        return MagicMock(eq=lambda *args: MagicMock(execute=lambda: mock_user_update_response))
    
    # Set up mock chains
    mock_subscriptions_table = MagicMock()
    mock_subscriptions_table.select.return_value.eq.return_value.execute.return_value = mock_subscription_response
    
    mock_payments_table = MagicMock()
    mock_payments_table.insert.return_value.execute.return_value = mock_payment_insert_response
    
    mock_users_table = MagicMock()
    mock_users_table.update = mock_user_update
    
    def table_router(table_name):
        if table_name == "subscriptions":
            return mock_subscriptions_table
        elif table_name == "payments":
            return mock_payments_table
        elif table_name == "users":
            return mock_users_table
        return MagicMock()
    
    mock_supabase.table.side_effect = table_router
    
    # Create payment service with mock client
    payment_service = PaymentService(supabase_client=mock_supabase)
    
    # Create webhook payload
    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": razorpay_payment_id,
                    "amount": amount,
                    "subscription_id": razorpay_subscription_id
                }
            }
        }
    }
    
    # Act: Handle payment webhook (skip signature verification in test)
    result = await payment_service.handle_payment_webhook(webhook_payload, "test_signature")
    
    # Assert: Payment processed successfully
    assert result is not None
    assert result["success"] is True
    assert result["user_id"] == user_id
    assert result["plan"] == plan
    
    # Property: User plan was updated to match subscription plan
    assert updated_plan == plan
    
    # Property: Payment was recorded
    mock_payments_table.insert.assert_called_once()


# Feature: medical-ai-platform, Property 58: Subscription expiry downgrades plan
@given(
    original_plan=valid_plan()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_subscription_expiry_downgrades_plan_property(original_plan):
    """
    Property 58: For any subscription that expires, the user's plan 
    should be downgraded to "free".
    
    This property verifies that:
    1. Expired subscriptions are detected
    2. User plan is downgraded to free
    3. Subscription status is updated to expired
    
    Validates: Requirements 24.4
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    subscription_id = str(uuid.uuid4())
    
    # Mock expired subscription lookup
    mock_expired_response = MagicMock()
    mock_expired_response.data = [{
        "id": subscription_id,
        "user_id": user_id,
        "plan": original_plan,
        "status": "active",
        "current_period_end": "2023-01-01T00:00:00Z"  # Past date
    }]
    
    # Mock subscription update
    mock_subscription_update_response = MagicMock()
    mock_subscription_update_response.data = [{
        "id": subscription_id,
        "status": "expired"
    }]
    
    # Mock user update
    mock_user_update_response = MagicMock()
    mock_user_update_response.data = [{
        "id": user_id,
        "plan": "free"
    }]
    
    # Track what plan was set
    downgraded_plan = None
    
    def mock_user_update(data):
        nonlocal downgraded_plan
        downgraded_plan = data.get("plan")
        return MagicMock(eq=lambda *args: MagicMock(execute=lambda: mock_user_update_response))
    
    # Set up mock chains
    mock_subscriptions_table = MagicMock()
    
    # For select query
    mock_select_chain = MagicMock()
    mock_select_chain.execute.return_value = mock_expired_response
    mock_subscriptions_table.select.return_value.eq.return_value.lt.return_value = mock_select_chain
    
    # For update query
    mock_subscriptions_table.update.return_value.eq.return_value.execute.return_value = mock_subscription_update_response
    
    mock_users_table = MagicMock()
    mock_users_table.update = mock_user_update
    
    def table_router(table_name):
        if table_name == "subscriptions":
            return mock_subscriptions_table
        elif table_name == "users":
            return mock_users_table
        return MagicMock()
    
    mock_supabase.table.side_effect = table_router
    
    # Create payment service with mock client
    payment_service = PaymentService(supabase_client=mock_supabase)
    
    # Act: Check expired subscriptions
    downgraded_users = await payment_service.check_expired_subscriptions()
    
    # Assert: User was downgraded
    assert len(downgraded_users) > 0
    assert downgraded_users[0]["user_id"] == user_id
    assert downgraded_users[0]["previous_plan"] == original_plan
    
    # Property: User plan was downgraded to "free"
    assert downgraded_plan == "free"
    
    # Property: Subscription status was updated to "expired"
    mock_subscriptions_table.update.assert_called()


@given(
    plan=valid_plan()
)
@settings(max_examples=100)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_subscription_creation_property(plan):
    """
    Property: For any subscription creation, the subscription should be
    stored with correct plan and active status.
    
    Validates: Requirements 24.1, 24.2
    """
    # Arrange: Create mock Supabase client
    mock_supabase = MagicMock()
    
    # Generate test IDs
    user_id = str(uuid.uuid4())
    subscription_id = str(uuid.uuid4())
    razorpay_subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
    
    # Mock subscription insert
    mock_insert_response = MagicMock()
    mock_insert_response.data = [{
        "id": subscription_id,
        "user_id": user_id,
        "plan": plan,
        "razorpay_subscription_id": razorpay_subscription_id,
        "status": "active"
    }]
    
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = mock_insert_response
    mock_supabase.table.return_value = mock_table
    
    # Create payment service with mock client
    payment_service = PaymentService(supabase_client=mock_supabase)
    
    # Act: Create subscription
    subscription = await payment_service.create_subscription(
        user_id=user_id,
        plan=plan,
        razorpay_subscription_id=razorpay_subscription_id
    )
    
    # Assert: Subscription created with correct data
    assert subscription is not None
    assert subscription["user_id"] == user_id
    assert subscription["plan"] == plan
    assert subscription["razorpay_subscription_id"] == razorpay_subscription_id
    
    # Property: New subscriptions are always created with "active" status
    assert subscription["status"] == "active"
