# config.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL_CONFIG = {
    "primary": {
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "client": Groq(api_key=os.getenv("GROQ_API_KEY"))
    },
    "github_fallback": {
        "provider": "github",
        "model_id": "openai/gpt-4o",
        "api_url": "https://models.github.ai/inference/chat/completions"
    }
}

MODEL_PREFERENCE_ORDER = ["primary", "github_fallback"]