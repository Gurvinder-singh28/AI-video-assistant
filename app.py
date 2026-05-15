import streamlit as st
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg:        #0a0a0f;
    --surface:   #111118;
    --border:    #1e1e2e;
    --accent:    #7c6af7;
    --accent2:   #f76a8c;
    --text:      #e8e8f0;
    --muted:     #6b6b80;
    --success:   #4ade80;
    --warn:      #facc15;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}

/* Hide default header */
[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
.block-container { padding: 2rem 3rem !important; max-width: 1200px !important; }

/* Hero */
.hero {
    text-align: center;
    padding: 3rem 0 2rem;
    position: relative;
}
.hero-badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    border: 1px solid var(--accent);
    padding: 0.3rem 1rem;
    border-radius: 2rem;
    margin-bottom: 1.2rem;
    text-transform: uppercase;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.4rem, 5vw, 4rem);
    font-weight: 800;
    line-height: 1.05;
    margin: 0;
    background: linear-gradient(135deg, #e8e8f0 30%, var(--accent) 70%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 0.8rem;
    letter-spacing: 0.05em;
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--accent); }
.card-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.5rem;
}
.card-body {
    color: #b0b0c8;
    font-size: 0.85rem;
    line-height: 1.7;
}

/* Stat row */
.stat-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}
.stat-box {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.stat-num {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--accent);
}
.stat-lbl {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    color: var(--muted);
    text-transform: uppercase;
}

/* Tag pills */
.pill {
    display: inline-block;
    background: rgba(124,106,247,0.12);
    color: var(--accent);
    border: 1px solid rgba(124,106,247,0.3);
    border-radius: 999px;
    padding: 0.25rem 0.8rem;
    font-size: 0.75rem;
    margin: 0.2rem 0.15rem;
}

/* Chat bubbles */
.chat-wrap { display: flex; flex-direction: column; gap: 0.8rem; }
.bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, var(--accent), #5a4fd4);
    color: #fff;
    border-radius: 16px 16px 4px 16px;
    padding: 0.7rem 1.1rem;
    max-width: 75%;
    font-size: 0.85rem;
    line-height: 1.6;
}
.bubble-bot {
    align-self: flex-start;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 16px 16px 16px 4px;
    padding: 0.7rem 1.1rem;
    max-width: 75%;
    font-size: 0.85rem;
    line-height: 1.6;
}
.bubble-label {
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.3rem;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* Step indicator */
.step {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.6rem 0;
    color: var(--muted);
    font-size: 0.8rem;
}
.step-dot {
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    flex-shrink: 0;
}
.step-active .step-dot  { background: var(--accent); color: #fff; }
.step-done .step-dot    { background: var(--success); color: #000; }
.step-pending .step-dot { background: var(--border); color: var(--muted); }
.step-active { color: var(--text); }
.step-done   { color: var(--success); }

/* Streamlit overrides */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select,
textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
}
div[data-testid="stTextInput"] input:focus,
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(124,106,247,0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), #5a4fd4) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    padding: 0.55rem 1.4rem !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* secondary button */
.stButton.secondary > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

[data-testid="stTabs"] [role="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    border-radius: 6px 6px 0 0 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

.stAlert { border-radius: 10px !important; }

div[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }

/* Progress bar */
.stProgress > div > div { background: var(--accent) !important; border-radius: 4px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
for key, val in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "step": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">✦ AI-Powered Analysis</div>
  <h1 class="hero-title">AI Video Assistant</h1>
  <p class="hero-sub">Transcribe · Summarize · Extract Insights · Chat with any video</p>
</div>
""", unsafe_allow_html=True)


# ── Input panel ────────────────────────────────────────────────────────────────
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">⬡ Source</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        source = st.text_input(
            "YouTube URL or local file path",
            placeholder="https://youtu.be/... or C:/path/to/video.mp4",
            label_visibility="collapsed",
        )
    with col2:
        language = st.selectbox(
            "Language",
            ["english", "hinglish"],
            label_visibility="collapsed",
        )

    run_col, _, reset_col = st.columns([2, 5, 1])
    with run_col:
        run_btn = st.button("▶  Analyse Video", use_container_width=True)
    with reset_col:
        if st.button("↺", help="Reset", use_container_width=True):
            for k in ["result", "chat_history", "step"]:
                st.session_state[k] = None if k == "result" else []
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Pipeline ───────────────────────────────────────────────────────────────────
def run_step(label, fn, *args, **kwargs):
    with st.spinner(f"{label}…"):
        return fn(*args, **kwargs)


if run_btn and source:
    st.session_state.result = None
    st.session_state.chat_history = []

    steps = ["Downloading / converting audio", "Chunking", "Transcribing", "Summarising", "Extracting insights", "Building RAG index"]
    step_placeholder = st.empty()

    def render_steps(done_count):
        html = '<div style="margin:1rem 0">'
        for i, s in enumerate(steps):
            if i < done_count:
                cls = "step step-done"
                dot = "✓"
            elif i == done_count:
                cls = "step step-active"
                dot = str(i + 1)
            else:
                cls = "step step-pending"
                dot = str(i + 1)
            html += f'<div class="{cls}"><div class="step-dot">{dot}</div>{s}</div>'
        html += "</div>"
        step_placeholder.markdown(html, unsafe_allow_html=True)

    render_steps(0)

    try:
        from utils.audio_processor import process_input
        chunks = run_step("Downloading / converting", process_input, source)
        render_steps(2)

        from core.transcriber import transcribe_all
        transcript = run_step("Transcribing", transcribe_all, chunks, language)
        render_steps(3)

        from core.summarizer import summarize, generate_title
        title   = run_step("Generating title",   generate_title, transcript)
        summary = run_step("Summarising",         summarize,      transcript)
        render_steps(4)

        from core.extractor import extract_action_items, extract_key_decisions, extract_questions
        actions   = run_step("Extracting action items",  extract_action_items,   transcript)
        decisions = run_step("Extracting decisions",     extract_key_decisions,  transcript)
        questions = run_step("Extracting questions",     extract_questions,      transcript)
        render_steps(5)

        from core.rag_engine import build_rag_chain
        rag_chain = run_step("Building RAG index", build_rag_chain, transcript)
        render_steps(6)

        st.session_state.result = {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": actions,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
        step_placeholder.empty()
        st.success("✦ Analysis complete!")
        time.sleep(0.6)
        st.rerun()

    except Exception as e:
        step_placeholder.empty()
        st.error(f"Pipeline error: {e}")

elif run_btn and not source:
    st.warning("Please enter a YouTube URL or local file path.")


# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title bar
    st.markdown(f"""
    <div class="card" style="border-color:rgba(124,106,247,0.4);background:rgba(124,106,247,0.06)">
        <div class="card-label">📌 Title</div>
        <div class="card-title">{r['title']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    word_count  = len(r["transcript"].split())
    chunk_count = r["transcript"].count(".") // 10 or 1
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><div class="stat-num">{word_count:,}</div><div class="stat-lbl">Words</div></div>
        <div class="stat-box"><div class="stat-num">{len(r['action_items'].strip().splitlines())}</div><div class="stat-lbl">Action Items</div></div>
        <div class="stat-box"><div class="stat-num">{len(r['key_decisions'].strip().splitlines())}</div><div class="stat-lbl">Decisions</div></div>
        <div class="stat-box"><div class="stat-num">{len(r['open_questions'].strip().splitlines())}</div><div class="stat-lbl">Questions</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Summary", "✅ Actions", "🔑 Decisions", "❓ Questions", "📄 Transcript"])

    with tab1:
        st.markdown(f'<div class="card"><div class="card-label">Summary</div><div class="card-body">{r["summary"]}</div></div>', unsafe_allow_html=True)

    with tab2:
        lines = [l.strip() for l in r["action_items"].strip().splitlines() if l.strip()]
        for line in lines:
            st.markdown(f"""
            <div class="card" style="padding:0.9rem 1.2rem;display:flex;gap:0.8rem;align-items:flex-start">
                <span style="color:var(--success);font-size:1rem;margin-top:2px">◈</span>
                <span class="card-body" style="margin:0">{line}</span>
            </div>""", unsafe_allow_html=True)

    with tab3:
        lines = [l.strip() for l in r["key_decisions"].strip().splitlines() if l.strip()]
        for line in lines:
            st.markdown(f"""
            <div class="card" style="padding:0.9rem 1.2rem;display:flex;gap:0.8rem;align-items:flex-start">
                <span style="color:var(--accent);font-size:1rem;margin-top:2px">◆</span>
                <span class="card-body" style="margin:0">{line}</span>
            </div>""", unsafe_allow_html=True)

    with tab4:
        lines = [l.strip() for l in r["open_questions"].strip().splitlines() if l.strip()]
        for line in lines:
            st.markdown(f"""
            <div class="card" style="padding:0.9rem 1.2rem;display:flex;gap:0.8rem;align-items:flex-start">
                <span style="color:var(--warn);font-size:1rem;margin-top:2px">?</span>
                <span class="card-body" style="margin:0">{line}</span>
            </div>""", unsafe_allow_html=True)

    with tab5:
        with st.expander("Full transcript", expanded=False):
            st.markdown(f'<div class="card-body" style="white-space:pre-wrap;max-height:400px;overflow-y:auto">{r["transcript"]}</div>', unsafe_allow_html=True)

    # ── RAG chat ───────────────────────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem">
        <span style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:var(--text)">💬 Chat with this video</span>
        <span class="pill">RAG-powered</span>
    </div>
    """, unsafe_allow_html=True)

    # Render history
    if st.session_state.chat_history:
        html = '<div class="chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                html += f'<div class="bubble-user"><div class="bubble-label">You</div>{msg["content"]}</div>'
            else:
                html += f'<div class="bubble-bot"><div class="bubble-label">🤖 Assistant</div>{msg["content"]}</div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Input row
    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input("Ask anything about the video…", key="chat_input", label_visibility="collapsed", placeholder="Ask anything about the video…")
    with btn_col:
        ask_btn = st.button("Send ➤", use_container_width=True)

    if ask_btn and question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.spinner("Thinking…"):
            from core.rag_engine import ask_question
            answer = ask_question(r["rag_chain"], question)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑  Clear chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center;padding:3rem 0;color:var(--muted)">
        <div style="font-size:3rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:600;color:#3a3a50">Paste a URL above to get started</div>
        <div style="font-size:0.8rem;margin-top:0.4rem">Supports YouTube links and local audio / video files</div>
    </div>
    """, unsafe_allow_html=True)