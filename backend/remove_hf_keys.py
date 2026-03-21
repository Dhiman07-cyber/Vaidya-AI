"""
Remove all HuggingFace API keys from Supabase database
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def remove_hf_keys():
    """Remove all HuggingFace keys from database"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)
    
    print(f"🌐 Supabase URL: {supabase_url}")
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    print(f"\n{'='*60}")
    print("📊 Current HuggingFace keys in database:")
    print(f"{'='*60}")
    
    # Show current keys before deletion
    try:
        result = supabase.table("api_keys").select("provider, feature, priority, status, health_status, created_at").eq("provider", "huggingface").order("feature").execute()
        
        if result.data:
            print(f"\n{'Feature':<15} {'Priority':<10} {'Status':<10} {'Health':<10}")
            print("-" * 60)
            for row in result.data:
                print(f"{row['feature']:<15} {row['priority']:<10} {row['status']:<10} {row['health_status']:<10}")
            print(f"\nTotal: {len(result.data)} keys found")
        else:
            print("\n⚠️  No HuggingFace keys found in database")
            print("\n✅ Nothing to remove!")
            return
    except Exception as e:
        print(f"❌ Failed to fetch keys: {str(e)}")
        sys.exit(1)
    
    # Confirm deletion
    print(f"\n{'='*60}")
    confirm = input("⚠️  Are you sure you want to DELETE all HuggingFace keys? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Deletion cancelled")
        return
    
    # Delete all HuggingFace keys
    print(f"\n🗑️  Deleting HuggingFace keys...")
    
    try:
        delete_result = supabase.table("api_keys").delete().eq("provider", "huggingface").execute()
        
        print(f"✅ Successfully deleted all HuggingFace keys")
        
    except Exception as e:
        print(f"❌ Failed to delete keys: {str(e)}")
        sys.exit(1)
    
    # Verify deletion
    print(f"\n{'='*60}")
    print("📊 Verification - Remaining HuggingFace keys:")
    print(f"{'='*60}")
    
    try:
        verify_result = supabase.table("api_keys").select("*").eq("provider", "huggingface").execute()
        
        if verify_result.data:
            print(f"\n⚠️  Warning: {len(verify_result.data)} HuggingFace keys still remain")
        else:
            print("\n✅ All HuggingFace keys successfully removed")
    except Exception as e:
        print(f"❌ Failed to verify: {str(e)}")
    
    # Show remaining keys by provider
    print(f"\n{'='*60}")
    print("📊 Remaining keys by provider:")
    print(f"{'='*60}")
    
    try:
        all_keys = supabase.table("api_keys").select("provider").execute()
        
        if all_keys.data:
            providers = {}
            for key in all_keys.data:
                provider = key['provider']
                providers[provider] = providers.get(provider, 0) + 1
            
            print(f"\n{'Provider':<20} {'Count':<10}")
            print("-" * 60)
            for provider, count in sorted(providers.items()):
                print(f"{provider:<20} {count:<10}")
            print(f"\nTotal keys: {len(all_keys.data)}")
        else:
            print("\n⚠️  No API keys found in database")
    except Exception as e:
        print(f"❌ Failed to fetch remaining keys: {str(e)}")
    
    print(f"\n{'='*60}")
    print("✅ Removal complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🗑️  HuggingFace API Keys Remover")
    print("="*60 + "\n")
    
    remove_hf_keys()
