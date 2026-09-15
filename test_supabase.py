import requests
import time
from datetime import datetime

# =========================
# SUPABASE SETTINGS
# =========================
SUPABASE_URL = "https://kpbaknudinxnvlgamwql.supabase.co"  # CHANGE THIS
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtwYmFrbnVkaW54bnZsZ2Ftd3FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MDEzMjEsImV4cCI6MjA4OTQ3NzMyMX0.9EdgWi09QnTcrA9RP_z90wUx08ArS-tm-q3myf-ffQY"  # CHANGE THIS

print("?? Testing Supabase Connection...")

# =========================
# SEND TEST DATA
# =========================
def send_test_data():
    try:
        # Simple test data
        test_data = {
            "temperature": 3.5,
            "humidity": 5.0,
            "soil_moisture": 3.0,
            "light_intensity": 7.0,
            "co2_level": 4.0
        }
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/sensor_data",
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"? SUCCESS! Sent to Supabase: {test_data}")
            return True
        else:
            print(f"? FAILED! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"? ERROR: {e}")
        return False

# =========================
# MAIN
# =========================
print("Sending test data...")
print("-" * 50)

if send_test_data():
    print("-" * 50)
    print("?? Test successful!")
    print("?? Check your Supabase dashboard:")
    print(f"   {SUPABASE_URL.replace('/rest/v1', '')}")
    print("   Go to: Table Editor ? sensor_data")
else:
    print("-" * 50)
    print("? Test failed. Check your:")
    print("   1. Supabase URL")
    print("   2. Supabase API Key")
    print("   3. Table exists (sensor_data)")
    print("   4. Internet connection")
