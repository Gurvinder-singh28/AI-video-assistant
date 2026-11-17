import os

from groq import Groq

STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
LANG_MAP = {"english": "en", "hinglish": "hi"}

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=6, timeout=180)
    return _client


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    with open(chunk_path, "rb") as f:
        audio = f.read()

    result = _get_client().audio.transcriptions.create(
        file=(os.path.basename(chunk_path), audio),
        model=STT_MODEL,
        language=LANG_MAP.get(language.lower(), "en"),
        response_format="text",
        temperature=0.0,
    )
    text = result if isinstance(result, str) else getattr(result, "text", str(result))
    return text.strip()


def transcribe_all(chunks: list, language: str = "english") -> str:
    parts = []
    for i, chunk_path in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}: {os.path.basename(chunk_path)}", flush=True)
        parts.append(transcribe_chunk(chunk_path, language))
    return " ".join(parts)