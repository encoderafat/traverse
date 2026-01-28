# backend/core/config.py

import os
from dotenv import load_dotenv

# Load .env file (backend/.env)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Make sure it exists in your backend .env file."
    )

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. "
        "Make sure it exists in your backend .env file."
    )

if not GEMINI_MODEL:
    raise RuntimeError(
        "GEMINI_MODEL is not set. "
        "Make sure it exists in your backend .env file."
    )
