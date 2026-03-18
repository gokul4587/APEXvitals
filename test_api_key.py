"""Simple 5-line script to test Gemini API key validity."""
import google.generativeai as genai

API_KEY = input("Enter your Gemini API key: ")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("test")
print("✓ Connection Successful" if response else "✗ Connection Failed")
