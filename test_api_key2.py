import os
from google import genai
from dotenv import load_dotenv

# Load the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the modern v1 Client
client = genai.Client(api_key=api_key)

try:
    print("--- 🔍 DISCOVERING AUTHORIZED MODELS ---")
    
    # In the 2026 v1 SDK, the attribute is 'supported_generation_methods'
    for model in client.models.list():
        # Using getattr is the 'Safe' way to handle evolving SDKs
        methods = getattr(model, 'supported_generation_methods', [])
        
        # We check for 'generateContent' to see if it's a chat/text model
        if 'generateContent' in methods:
            print(f"✅ Found: {model.name}")

    print("\n--- 🧠 INITIALIZING BRAIN TEST ---")
    
    # We use the full name format required by the v1 SDK
    # Ensure the hyphen is present: gemini-1.5-flash
    response = client.models.generate_content(
        model="gemini-3-flash-preview", 
        contents="Echo check: Is POD-C initialized and ready for APEXVITALS?"
    )
    
    print(f"🚀 SUCCESS: {response.text}")

except Exception as e:
    print(f"❌ HANDSHAKE FAILED: {e}")