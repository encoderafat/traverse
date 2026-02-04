import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    print("Error: SERPAPI_API_KEY is not set in your .env file.")
    exit(1)

# Test query
query = "test search"
search_url = "https://serpapi.com/search"
params = {
    "q": query,
    "api_key": SERPAPI_API_KEY,
    "engine": "google",
    "num": 1 # Only request one result for a quick check
}

print(f"Checking SerpAPI key with query: '{query}'...")

try:
    response = requests.get(search_url, params=params, timeout=10)
    response.raise_for_status() # Raise an exception for HTTP errors

    data = response.json()

    if "error" in data:
        print(f"SerpAPI returned an error: {data['error']}")
    elif "organic_results" in data and len(data["organic_results"]) > 0:
        print("SerpAPI key is working! Received organic results.")
        print(f"Example result title: {data['organic_results'][0]['title']}")
    else:
        print("SerpAPI key might be working, but no organic results were returned for the test query.")
        print("Raw response (first 500 chars):", str(data)[:500])

except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    if e.response.status_code == 401:
        print("This usually means your API key is invalid or unauthorized.")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to SerpAPI. Check your internet connection or SerpAPI's status.")
except requests.exceptions.Timeout:
    print("Error: The request to SerpAPI timed out.")
except requests.exceptions.RequestException as e:
    print(f"An unexpected error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred during JSON parsing or data handling: {e}")

print("\n--- Test Complete ---")
