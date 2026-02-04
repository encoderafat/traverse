import os
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file (assuming it's in the project root)
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY is not set in your .env file.")
    exit(1)

if not GEMINI_MODEL:
    print("Error: GEMINI_MODEL is not set in your .env file.")
    print("Please set a valid Gemini model, e.g., 'gemini-pro', 'gemini-1.5-flash'.")
    exit(1)

print(f"Checking Google API Key and Gemini model '{GEMINI_MODEL}'...")

try:
    # Initialize the client with the API key
    client = genai.Client(api_key=GOOGLE_API_KEY)

    # Make a simple test call to the Gemini API
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=types.Part.from_text(text="Hello, Gemini!"),
        config=types.GenerateContentConfig(
            temperature=0.0,
        ),
    )

    if response.text:
        print("Google API Key is working! Received a response from Gemini.")
        print(f"Gemini's response: '{response.text.strip()}'")
    else:
        print("Google API Key might be working, but no text response was received.")
        print(f"Raw response: {response}")

except genai.errors.APIError as e:
    print(f"Google Generative AI API Error: {e.code} - {e.message}")
    if e.code == 401:
        print("This usually means your GOOGLE_API_KEY is invalid or unauthorized.")
    elif e.code == 400:
        print("This might mean your GEMINI_MODEL is incorrect or unavailable.")
    else:
        print("Please check your GOOGLE_API_KEY and GEMINI_MODEL configuration.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("\n--- Test Complete ---")
