import os
import shutil
import tempfile
import threading
import traceback
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

# Compatibility shim for LangChain version mismatches (harmless if not needed)
try:
    import langchain
    for _name, _val in (("verbose", False), ("debug", False), ("llm_cache", None)):
        if not hasattr(langchain, _name):
            setattr(langchain, _name, _val)
except ImportError:
    pass

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

app = FastAPI(title="AI Video Analyser")

ALLOWED = {".mp3", ".mp4", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".webm", ".mpeg"}
MAX_MB = 200
MAX_JOBS = 20

JOBS: dict[str, dict] = {}
CHAINS: dict[str, object] = {}
ORDER: list[str] = []
LOCK = threading.Lock()   # Whisper is not thread-safe -> one job at a time


def _remember(job_id: str) -> None:
    ORDER.append(job_id)
    while len(ORDER) > MAX_JOBS:
        old = ORDER.pop(0)
        JOBS.pop(old, None)
        CHAINS.pop(old, None)


def _friendly_error(e: Exception) -> str:
    msg = f"{type(e).__name__}: {e}"
    low = msg.lower()
    if "429" in msg or "rate limit" in low:
        return ("Groq rate limit reached (free tier). Wait a minute and try again, "
                "or try a shorter file.")
    if "413" in msg or "request too large" in low:
        return "This request is too large for Groq's free tier limit. Try a shorter file."
    if "401" in msg or "invalid_api_key" in low or "unauthorized" in low:
        return "Groq rejected the API key. Check GROQ_API_KEY in your .env file."
    if "model_not_found" in low or "does not exist" in low:
        return ("The selected Groq model is not available for your key. "
        "Remove GROQ_MODEL from .env to auto-select, or run list_groq_models.py.")
    return msg


def _work(job_id: str, path: str, language: str) -> None:
    job = JOBS[job_id]
    try:
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY is missing. Add it to the .env file and restart the server.")

        with LOCK:
            job["stage"] = 0
            chunks = process_input(path)

            job["stage"] = 1
            transcript = transcribe_all(chunks, language)
            print("TRANSCRIPT:", transcript[:200], flush=True)
            if not transcript.strip():
                raise ValueError("No speech detected in this file.")

            job["stage"] = 2
            title = generate_title(transcript)
            summary = summarize(transcript)

            job["stage"] = 3
            action_items = extract_action_items(transcript)
            decisions = extract_key_decisions(transcript)
            questions = extract_questions(transcript)

            job["stage"] = 4
            CHAINS[job_id] = build_rag_chain(transcript)

        job["result"] = {
            "session_id": job_id,
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
        }
        job["stage"] = 5
        job["status"] = "done"

    except Exception as e:
        traceback.print_exc()
        job["status"] = "error"
        job["error"] = _friendly_error(e)

    finally:
        shutil.rmtree(Path(path).parent, ignore_errors=True)


@app.post("/api/analyse")
async def analyse(file: UploadFile = File(...), language: str = Form("english")):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type. Use: {', '.join(sorted(ALLOWED))}")

    language = language.lower()
    if language not in {"english", "hinglish"}:
        raise HTTPException(400, "Invalid language")

    tmp_dir = Path(tempfile.mkdtemp(prefix="avu_"))
    path = tmp_dir / f"upload{ext}"
    size = 0
    try:
        with open(path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_MB * 1024 * 1024:
                    raise HTTPException(413, f"File is larger than {MAX_MB}MB")
                out.write(chunk)
    except HTTPException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "stage": 0}
    _remember(job_id)
    threading.Thread(target=_work, args=(job_id, str(path), language), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found or expired")

    out = {"status": job["status"], "stage": job["stage"]}
    if job["status"] == "done":
        out["result"] = job["result"]
    if job["status"] == "error":
        out["error"] = job.get("error", "Unknown error")
    return out


class ChatIn(BaseModel):
    session_id: str
    question: str


@app.post("/api/chat")
def chat(body: ChatIn):
    chain = CHAINS.get(body.session_id)
    if chain is None:
        raise HTTPException(404, "Session expired. Please analyse the file again.")
    try:
        return {"answer": ask_question(chain, body.question)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, _friendly_error(e))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")