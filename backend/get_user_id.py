"""
Helper script to get your user ID from the database
Usage: python get_user_id.py your.email@example.com
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def get_user_id(email: str):
    """Get user ID by email"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Query users table
        result = supabase.table("users").select("id, email, name, role, plan").eq("email", email).execute()
        
        if not result.data:
            print(f"❌ No user found with email: {email}")
            sys.exit(1)
        
        user = result.data[0]
        
        print("\n" + "="*60)
        print("✅ User Found")
        print("="*60)
        print(f"User ID:  {user['id']}")
        print(f"Email:    {user['email']}")
        print(f"Name:     {user.get('name', 'N/A')}")
        print(f"Role:     {user.get('role', 'user')}")
        print(f"Plan:     {user.get('plan', 'free')}")
        print("="*60)
        print(f"\n📋 Copy this User ID for the document processor:")
        print(f"   {user['id']}")
        print("\n💡 Usage:")
        print(f'   python process_document_offline.py "document.pdf" --user-id {user["id"]}')
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_user_id.py your.email@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    get_user_id(email)
