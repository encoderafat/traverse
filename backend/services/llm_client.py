from google import genai
from google.genai import types
from core.config import GOOGLE_API_KEY, GEMINI_MODEL, SERPAPI_API_KEY
import requests
from typing import Dict, Any
from bs4 import BeautifulSoup

client = genai.Client(api_key=GOOGLE_API_KEY)

def call_gemini(
    system_instruction: str,
    user_message: str,
    model: str = GEMINI_MODEL,
    temperature: float = 0.6,
) -> str:
    response = client.models.generate_content(
        model=model,
        contents=types.Part.from_text(text=user_message),
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        ),
    )
    return response.text


def google_web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Perform a Google web search using SerpAPI."""
    search_url = "https://serpapi.com/search"
    params = {
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_API_KEY
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error in google_web_search: {e}")
        # Return a mock response in case of error
        return {
            "results": [
                {
                    "title": f"Mock result for {query}",
                    "link": "https://example.com",
                    "snippet": f"This is a mock result for the query: {query}"
                }
            ]
        }

def web_fetch(url: str) -> str:
    """Fetch content from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # Limit content length to prevent overly large inputs
        max_length = 2000  # characters
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return text
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"
