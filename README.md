# 🎬 AI Video Analyser

Upload any audio or video recording and get a **transcript, smart summary, action items, key decisions and open questions**, then **chat with your content** using RAG.

🔗 **Live demo:** https://ai-video-assistant-1-rzaz.onrender.com
*(Hosted on a free plan, so the first load after inactivity can take about a minute.)*

<!-- Add a screenshot: put an image in the repo (e.g. docs/screenshot.png) and use: -->
<!-- ![AI Video Analyser](docs/screenshot.png) -->

---

## ✨ Features

- **Transcription** with Whisper (`whisper-large-v3-turbo`) via the Groq API
- **English and Hinglish** audio support
- **Smart summary** with a title and bullet points
- **Action items** with owner and deadline
- **Key decisions** and **open questions**
- **Chat with your recording**: RAG over the transcript, answers grounded only in what was said
- **Progress tracking** with real pipeline stages
- Copy or download the full analysis as a `.txt` file
- Responsive, modern dark UI built with plain HTML, CSS and JavaScript

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Uvicorn |
| Frontend | HTML, CSS, vanilla JavaScript |
| Speech-to-text | Groq Whisper API (`whisper-large-v3-turbo`) |
| LLM | Groq (`openai/gpt-oss-120b`, auto-selected from the models your key can use) |
| Orchestration | LangChain (LCEL) |
| Vector store | ChromaDB |
| Embeddings | `all-MiniLM-L6-v2` via ONNX (no PyTorch needed) |
| Audio processing | FFmpeg (via `imageio-ffmpeg`) |
| Deployment | Render |

## 🔄 How It Works

```
Upload file
   │
   ▼
FFmpeg → mono 16 kHz WAV → split into 10-minute chunks
   │
   ▼
Groq Whisper → full transcript
   │
   ├─► Title + summary (map-reduce summarisation)
   ├─► Action items / key decisions / open questions
   └─► Chunk → embed → ChromaDB → RAG chain
                                      │
                                      ▼
                              Chat with the recording
```

The server runs analysis as a background job. The browser polls `/api/status/{job_id}` and shows the current stage until results are ready.

## 📁 Project Structure

```
AI-video-assistant/
├── core/
│   ├── llm.py            # Groq LLM client + automatic model selection
│   ├── transcriber.py    # Groq Whisper speech-to-text
│   ├── summarizer.py     # Title + map-reduce summary
│   ├── extractor.py      # Action items, decisions, open questions
│   ├── rag_engine.py     # RAG chain for chat
│   └── vector_store.py   # ChromaDB + ONNX embeddings
├── utils/
│   └── audio_processor.py  # FFmpeg convert + chunk audio
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── server.py             # FastAPI app (API + serves the UI)
├── main.py               # Optional command-line version of the pipeline
├── requirements.txt
└── runtime.txt
```

## 🚀 Run Locally

**Requirements:** Python 3.11 and a free [Groq API key](https://console.groq.com/keys).

```bash
# 1. Clone
git clone https://github.com/Gurvinder-singh28/AI-video-assistant.git
cd AI-video-assistant

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
echo GROQ_API_KEY=your_groq_key_here > .env

# 5. Start the server
uvicorn server:app --reload
```

Open **http://127.0.0.1:8000**, upload a file, pick the language and click **Analyse**.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Your Groq API key (starts with `gsk_`) |
| `GROQ_MODEL` | ❌ | Force a specific chat model. Leave unset to auto-select |
| `GROQ_STT_MODEL` | ❌ | Speech-to-text model (default `whisper-large-v3-turbo`) |

> Never commit your `.env` file. It is already listed in `.gitignore`.

## ☁️ Deploy on Render

1. Push the repo to GitHub.
2. In Render: **New → Web Service**, select the repo.
3. Settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   - `GROQ_API_KEY` = your key (no quotes, no spaces)
   - `PYTHON_VERSION` = `3.11.9`

The app uses hosted Whisper and ONNX embeddings, so it does not need PyTorch and fits on small instances.

## 🔌 API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyse` | Upload a file (`file`, `language`). Returns `{ "job_id": ... }` |
| `GET` | `/api/status/{job_id}` | Job stage and, when finished, the full result |
| `POST` | `/api/chat` | Body `{ "session_id", "question" }`. Returns `{ "answer": ... }` |

## 📋 Supported Input

- **Formats:** MP3, MP4, WAV, M4A, AAC, OGG, FLAC, WebM, MPEG
- **Max size:** 200 MB per file
- **Languages:** English, Hinglish (Hindi mode)

## ⚠️ Limitations

- **Free-tier limits:** Groq enforces rate limits on free accounts, so very long recordings can be slow or may hit limits.
- **YouTube links are not supported** in the deployed app. YouTube blocks server downloads, so upload a local file instead.
- Analysis jobs and chat sessions are stored in memory, so they are lost when the server restarts.
- Hinglish uses Whisper in Hindi mode, so accuracy on mixed-language speech can vary.

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `GROQ_API_KEY is missing` | Create `.env` next to `server.py`, then restart the server |
| `401 Invalid API Key` | Re-copy the key (no quotes or spaces) and update `.env` or the Render environment |
| `404 model_not_found` | Remove `GROQ_MODEL` from `.env` so a supported model is auto-selected |
| `429 rate limit` | Wait a minute and retry, or try a shorter file |
| Page loads but buttons do nothing | Check that `static/app.js` is saved and loads at `/static/app.js` |

## 👤 Author

**Gurvinder Singh**
GitHub: [@Gurvinder-singh28](https://github.com/Gurvinder-singh28)
