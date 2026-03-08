"""
Test script for hybrid implementation system
Tests health tracking, provider selection, and fallback logic
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_health_tracker():
    """Test health tracker service"""
    logger.info("\n=== Testing Health Tracker ===")
    
    from services.health_tracker import get_health_tracker_service
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    health_tracker = get_health_tracker_service(supabase)
    
    # Test 1: Get all healthy keys for a feature
    logger.info("\nTest 1: Get all healthy keys for 'mcq' feature")
    keys = await health_tracker.get_all_healthy_keys_for_feature("mcq")
    logger.info(f"Found {len(keys)} healthy keys")
    for key in keys:
        logger.info(
            f"  - {key['provider']}: priority={key['priority']}, "
            f"health={key['health_score']:.2f}, status={key['health_status']}"
        )
    
    # Test 2: Select best provider (no preference)
    logger.info("\nTest 2: Select best provider (no preference)")
    best_key = await health_tracker.select_best_provider("mcq")
    if best_key:
        logger.info(
            f"Selected: {best_key['provider']} "
            f"(priority={best_key['priority']}, health={best_key['health_score']:.2f})"
        )
    else:
        logger.warning("No best key selected")
    
    # Test 3: Select with session preference
    logger.info("\nTest 3: Select best provider (prefer huggingface)")
    best_key = await health_tracker.select_best_provider("mcq", session_preference="huggingface")
    if best_key:
        logger.info(
            f"Selected: {best_key['provider']} "
            f"(priority={best_key['priority']}, health={best_key['health_score']:.2f})"
        )
    else:
        logger.warning("No best key selected")
    
    logger.info("\n✓ Health tracker tests complete")


async def test_model_router():
    """Test model router with health-based selection"""
    logger.info("\n=== Testing Model Router ===")
    
    from services.model_router import get_model_router_service
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    router = get_model_router_service(supabase)
    
    # Test 1: Simple API call
    logger.info("\nTest 1: Simple API call (no preference)")
    result = await router.execute_with_fallback(
        provider="openrouter",  # May be overridden
        feature="chat",
        prompt="What is diabetes? (one sentence)",
        max_retries=2
    )
    
    logger.info(f"Success: {result['success']}")
    if result['success']:
        logger.info(f"Provider used: {result.get('provider_used', 'unknown')}")
        logger.info(f"Content: {result['content'][:100]}...")
        logger.info(f"Tokens: {result['tokens_used']}")
        logger.info(f"Attempts: {result['attempts']}")
    else:
        logger.error(f"Error: {result['error']}")
    
    # Test 2: With session preference
    logger.info("\nTest 2: API call with session preference (huggingface)")
    result = await router.execute_with_fallback(
        provider="openrouter",
        feature="chat",
        prompt="What is hypertension? (one sentence)",
        session_preference="huggingface",
        max_retries=2
    )
    
    logger.info(f"Success: {result['success']}")
    if result['success']:
        logger.info(f"Provider used: {result.get('provider_used', 'unknown')}")
        logger.info(f"Content: {result['content'][:100]}...")
        logger.info(f"Used fallback model: {result.get('used_fallback_model', False)}")
    else:
        logger.error(f"Error: {result['error']}")
    
    logger.info("\n✓ Model router tests complete")


async def test_huggingface_provider():
    """Test HuggingFace provider with database key"""
    logger.info("\n=== Testing HuggingFace Provider ===")
    
    from services.providers.huggingface import get_huggingface_provider
    from services.model_router import get_model_router_service
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    router = get_model_router_service(supabase)
    
    # Get HF key from database
    hf_key = await router.get_active_key("huggingface", "chat")
    
    if not hf_key:
        logger.error("No HuggingFace key found in database")
        return
    
    logger.info(f"Found HF key: {hf_key['id']}")
    
    # Test call
    hf_provider = get_huggingface_provider()
    result = await hf_provider.call_huggingface(
        api_key=hf_key["key_value"],
        feature="chat",
        prompt="What is the capital of France? (one word)",
        max_tokens=50
    )
    
    logger.info(f"Success: {result['success']}")
    if result['success']:
        logger.info(f"Model: {result.get('model', 'unknown')}")
        logger.info(f"Content: {result['content']}")
    else:
        logger.error(f"Error: {result['error']}")
    
    logger.info("\n✓ HuggingFace provider tests complete")


async def test_health_updates():
    """Test health tracking updates"""
    logger.info("\n=== Testing Health Updates ===")
    
    from services.health_tracker import get_health_tracker_service
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    health_tracker = get_health_tracker_service(supabase)
    
    # Get a key to test with
    keys = await health_tracker.get_all_healthy_keys_for_feature("chat")
    if not keys:
        logger.error("No keys found for testing")
        return
    
    test_key = keys[0]
    logger.info(f"Testing with key: {test_key['id']} (provider: {test_key['provider']})")
    
    # Simulate success
    logger.info("\nSimulating successful API call...")
    await health_tracker.update_key_health(
        key_id=test_key['id'],
        success=True,
        response_time_ms=500
    )
    
    # Simulate failure
    logger.info("Simulating failed API call...")
    await health_tracker.update_key_health(
        key_id=test_key['id'],
        success=False,
        response_time_ms=1000
    )
    
    # Check updated stats
    response = supabase.table("api_keys") \
        .select("recent_attempts, recent_successes, recent_failures, health_status, health_score") \
        .eq("id", test_key['id']) \
        .execute()
    
    if response.data:
        stats = response.data[0]
        logger.info(f"\nUpdated stats:")
        logger.info(f"  Attempts: {stats['recent_attempts']}")
        logger.info(f"  Successes: {stats['recent_successes']}")
        logger.info(f"  Failures: {stats['recent_failures']}")
        logger.info(f"  Health status: {stats['health_status']}")
        logger.info(f"  Health score: {stats['health_score']:.2f}")
    
    logger.info("\n✓ Health update tests complete")


async def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("HYBRID SYSTEM TEST SUITE")
    logger.info("=" * 60)
    
    try:
        await test_health_tracker()
        await test_huggingface_provider()
        await test_health_updates()
        await test_model_router()
        
        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
