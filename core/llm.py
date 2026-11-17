import os
from functools import lru_cache

import httpx
from langchain_groq import ChatGroq

# Best first. The first one available to your API key is used.
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# Models on Groq that are not chat/text models
_SKIP = ("whisper", "guard", "tts", "orpheus", "compound", "embed", "safeguard")


@lru_cache(maxsize=1)
def pick_model() -> str:
    """Choose a chat model your Groq key can actually use (cached after the first call)."""
    forced = os.getenv("GROQ_MODEL")
    if forced:
        return forced

    try:
        r = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            timeout=15,
        )
        r.raise_for_status()
        available = {m["id"] for m in r.json().get("data", [])}

        for model in PREFERRED_MODELS:
            if model in available:
                print(f"Using Groq model: {model}", flush=True)
                return model

        for model in sorted(available):
            if not any(s in model.lower() for s in _SKIP):
                print(f"Using Groq model (auto-picked): {model}", flush=True)
                return model
    except Exception as e:
        print(f"Could not list Groq models ({e}). Falling back to {PREFERRED_MODELS[0]}", flush=True)

    return PREFERRED_MODELS[0]


def get_llm(temperature: float = 0.3):
    """One shared Groq client for the whole project.
    max_retries makes the client wait and retry automatically on 429 rate limits."""
    return ChatGroq(
        model=pick_model(),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature,
        max_retries=6,
        timeout=90,
    )