"""
Seed HuggingFace API keys to Supabase database
Reads keys from .env and inserts them into api_keys table
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def seed_hf_keys():
    """Seed HuggingFace keys for all features"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)
    
    if not hf_api_key:
        print("❌ Error: HUGGINGFACE_API_KEY must be set in .env")
        sys.exit(1)
    
    print(f"🔑 HuggingFace API Key: {hf_api_key[:10]}...")
    print(f"🌐 Supabase URL: {supabase_url}")
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Features to seed
    features = [
        'chat', 
        'flashcard', 
        'mcq', 
        'highyield', 
        'explain', 
        'map', 
        'clinical', 
        'osce', 
        'image'
    ]
    
    print(f"\n📝 Seeding HuggingFace keys for {len(features)} features...")
    
    success_count = 0
    error_count = 0
    
    for feature in features:
        try:
            # Check if key already exists
            existing = supabase.table("api_keys").select("*").eq("provider", "huggingface").eq("feature", feature).eq("key_value", hf_api_key).execute()
            
            if existing.data:
                # Update existing key
                supabase.table("api_keys").update({
                    "status": "active",
                    "priority": 100,
                    "health_status": "healthy",
                    "health_score": 1.0,
                    "recent_attempts": 0,
                    "recent_successes": 0,
                    "recent_failures": 0
                }).eq("provider", "huggingface").eq("feature", feature).eq("key_value", hf_api_key).execute()
                
                print(f"  ✓ Updated HuggingFace key for feature: {feature}")
            else:
                # Insert new key
                supabase.table("api_keys").insert({
                    "provider": "huggingface",
                    "feature": feature,
                    "key_value": hf_api_key,
                    "priority": 100,
                    "status": "active",
                    "health_status": "healthy",
                    "health_score": 1.0,
                    "recent_attempts": 0,
                    "recent_successes": 0,
                    "recent_failures": 0
                }).execute()
                
                print(f"  ✓ Inserted HuggingFace key for feature: {feature}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to seed key for {feature}: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully seeded: {success_count}/{len(features)} features")
    if error_count > 0:
        print(f"❌ Failed: {error_count}/{len(features)} features")
    
    # Verify
    print(f"\n{'='*60}")
    print("📊 Verification - Current HuggingFace keys in database:")
    print(f"{'='*60}")
    
    try:
        result = supabase.table("api_keys").select("provider, feature, priority, status, health_status").eq("provider", "huggingface").order("feature").execute()
        
        if result.data:
            print(f"\n{'Feature':<15} {'Priority':<10} {'Status':<10} {'Health':<10}")
            print("-" * 60)
            for row in result.data:
                print(f"{row['feature']:<15} {row['priority']:<10} {row['status']:<10} {row['health_status']:<10}")
            print(f"\nTotal: {len(result.data)} keys")
        else:
            print("No HuggingFace keys found in database")
    except Exception as e:
        print(f"❌ Failed to verify: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✅ Seeding complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 HuggingFace API Keys Seeder")
    print("="*60 + "\n")
    
    seed_hf_keys()
