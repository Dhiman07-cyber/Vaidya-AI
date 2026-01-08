#!/usr/bin/env python3
"""
Script to exit maintenance mode
Usage: python exit_maintenance.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def exit_maintenance_mode():
    """Exit maintenance mode by updating system_flags"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Check current maintenance status
        response = supabase.table("system_flags")\
            .select("flag_value")\
            .eq("flag_name", "maintenance_mode")\
            .execute()
        
        if response.data and len(response.data) > 0:
            current_status = response.data[0]["flag_value"]
            print(f"Current maintenance mode: {current_status}")
            
            if current_status == "off":
                print("✅ System is already out of maintenance mode")
                return
        
        # Update to exit maintenance mode
        response = supabase.table("system_flags")\
            .update({"flag_value": "off"})\
            .eq("flag_name", "maintenance_mode")\
            .execute()
        
        print("✅ Successfully exited maintenance mode")
        print("\nYou can now:")
        print("1. Restart the backend server")
        print("2. Test the study tools again")
        print("3. Monitor in Admin Panel → Model Usage")
        
    except Exception as e:
        print(f"❌ Error exiting maintenance mode: {e}")


if __name__ == "__main__":
    print("Exiting maintenance mode...")
    print("="*60)
    exit_maintenance_mode()
