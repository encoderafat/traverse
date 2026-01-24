from google import genai
from core.config import GOOGLE_API_KEY, GEMINI_MODEL

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
