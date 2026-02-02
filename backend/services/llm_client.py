from google import genai
from backend.core.config import GOOGLE_API_KEY, GEMINI_MODEL
import requests
from typing import Dict, Any

client = genai.Client(api_key=GOOGLE_API_KEY)

def call_gemini(
    system_instruction: str,
    user_message: str,
    model: str = GEMINI_MODEL,
    temperature: float = 0.6,
) -> str:
    resp = client.models.generate_content(
        model=model,
        contents=[
            {"role": "user", "parts": [user_message]},
        ],
        config={
            "system_instruction": system_instruction,
            "temperature": temperature,
        },
    )
    return resp.text

def google_web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Perform a Google web search using SerpAPI."""
    search_url = "https://serpapi.com/search"
    params = {
        "q": query,
        "num": num_results,
        "api_key": GOOGLE_API_KEY  # Using the same API key if it's also for SerpAPI
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
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

        # Extract text content from HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        # Limit content length to prevent overly large inputs
        max_length = 2000  # characters
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return text
    except Exception as e:
        return f"Error fetching content from {url}: {str(e)}"
