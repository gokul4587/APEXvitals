from google import genai
import os

# 1. Paste your key directly here just for this test
TEST_KEY = "YOUR_KEY_HERE"

try:
    client = genai.Client(api_key=TEST_KEY.strip())
    # We use 'gemini-1.5-flash' because it's the most widely enabled model
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents="Echo test: Is the APEXVITALS brain online?"
    )
    print(f"✅ SUCCESS: {response.text}")
except Exception as e:
    print(f"❌ FAILED: {e}")