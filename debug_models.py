"""Debug script to list all available Gemini models for your API key."""
import google.generativeai as genai

API_KEY = input("Enter your Gemini API key: ")
genai.configure(api_key=API_KEY)

print("\n=== AVAILABLE MODELS ===\n")
for m in genai.list_models():
    print(f"  {m.name}")

print("\n=== TESTING MODEL INIT ===\n")

# Try different model name formats
test_names = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-pro',
    'gemini-1.5-flash-001',
    'gemini-1.5-flash-002',
    'gemini-1.5-pro-001',
    'gemini-1.5-pro-002',
]

for name in test_names:
    try:
        model = genai.GenerativeModel(name)
        response = model.generate_content("test")
        print(f"✓ {name} - WORKS")
    except Exception as e:
        print(f"✗ {name} - {type(e).__name__}: {str(e)[:50]}")
