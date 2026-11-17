const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const MAX_MB = 200;
const OK_EXT = ["mp3", "mp4", "wav", "m4a", "aac", "ogg", "flac", "webm", "mpeg"];
const STEPS = 5;
let file = null, language = "english", sessionId = null, data = null;

const drop = $("#drop"), fileInput = $("#file"), analyseBtn = $("#analyseBtn");

/* ---------- helpers ---------- */
function toast(msg, err = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  setTimeout(() => (t.className = "toast"), 3500);
}
const fmtSize = (b) => (b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : (b / 1024).toFixed(0) + " KB");
const clean = (s) => s.replace(/\*\*/g, "").replace(/^#+\s*/, "").trim();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* Parse the LLM's numbered / bulleted text into [{title, sub[]}] */
function parseList(text) {
  if (!text) return [];
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length === 1 && /^no .* found\.?$/i.test(clean(lines[0]))) return [];
  const isNum = (l) => /^\d+[\.\)]\s+/.test(l);
  const isBul = (l) => /^[-*•]\s+/.test(l);
  const hasNum = lines.some(isNum);
  const items = [];
  for (const l of lines) {
    if (hasNum ? isNum(l) : isBul(l)) {
      items.push({ title: clean(l.replace(/^(\d+[\.\)]|[-*•])\s+/, "")), sub: [] });
    } else if (items.length) {
      items[items.length - 1].sub.push(clean(l.replace(/^[-*•]\s+/, "")));
    } else {
      items.push({ title: clean(l), sub: [] });
    }
  }
  return items;
}

/* ---------- file selection ---------- */
function setFile(f) {
  if (!f) return;
  const ext = f.name.split(".").pop().toLowerCase();
  if (!OK_EXT.includes(ext)) return toast("Unsupported file type: ." + ext, true);
  if (f.size > MAX_MB * 1048576) return toast(`File is larger than ${MAX_MB}MB`, true);
  file = f;
  $("#fileName").textContent = f.name;
  $("#fileSize").textContent = fmtSize(f.size);
  $("#fileInfo").classList.remove("hidden");
  drop.classList.add("hidden");
  analyseBtn.disabled = false;
}
function clearFile() {
  file = null;
  fileInput.value = "";
  $("#fileInfo").classList.add("hidden");
  drop.classList.remove("hidden");
  analyseBtn.disabled = true;
}
fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));
$("#removeFile").onclick = clearFile;
["dragenter", "dragover"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); })
);
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); })
);
drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));

/* ---------- language ---------- */
$$("#lang .seg").forEach((b) => (b.onclick = () => {
  $$("#lang .seg").forEach((x) => x.classList.remove("active"));
  b.classList.add("active");
  language = b.dataset.v;
  $("#langHint").innerHTML = language === "english"
    ? "<b>English</b> uses the local <code>Whisper</code> model in English mode."
    : "<b class='t'>Hinglish</b> uses the local <code>Whisper</code> model in Hindi mode.";
}));

/* ---------- progress ---------- */
function setStep(n) {
  $$(".stepper li").forEach((li, i) => {
    li.classList.toggle("done", i < n);
    li.classList.toggle("active", i === n);
  });
  $("#barFill").style.width = Math.max(6, Math.min(100, (n / STEPS) * 100)) + "%";
}

/* ---------- analyse ---------- */
analyseBtn.onclick = async () => {
  if (!file) return;
  analyseBtn.disabled = true;
  $("#results").classList.add("hidden");
  $("#progress").classList.remove("hidden");
  setStep(0);
  $("#progress").scrollIntoView({ behavior: "smooth", block: "center" });

  try {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("language", language);
    const res = await fetch("/api/analyse", { method: "POST", body: fd });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json.detail || "Upload failed");

    data = await poll(json.job_id);
    sessionId = data.session_id;
    setStep(STEPS);
    await sleep(400);
    $("#progress").classList.add("hidden");
    showResults();
  } catch (e) {
    $("#progress").classList.add("hidden");
    toast(e.message, true);
  } finally {
    analyseBtn.disabled = !file;
  }
};

async function poll(jobId) {
  let fails = 0;
  while (true) {
    await sleep(1500);
    try {
      const res = await fetch(`/api/status/${jobId}`);
      const j = await res.json();
      if (!res.ok) throw new Error(j.detail || "Status check failed");
      fails = 0;
      if (j.status === "error") throw new Error(j.error);
      setStep(j.stage);
      if (j.status === "done") return j.result;
    } catch (e) {
      if (e instanceof TypeError && ++fails < 5) continue;
      throw e;
    }
  }
}

/* ---------- results ---------- */
function showResults() {
  $("#resTitle").textContent = data.title ? clean(data.title).replace(/^["']|["']$/g, "") : "Results";
  ["action_items", "key_decisions", "open_questions"].forEach(
    (k) => ($("#c-" + k).textContent = parseList(data[k]).length)
  );
  $("#msgs").innerHTML = "";
  addMsg("Hi! Ask me anything about this recording.", "bot");
  $("#results").classList.remove("hidden");
  renderTab("summary");
  $("#results").scrollIntoView({ behavior: "smooth" });
}

function renderTab(t) {
  $$(".tab").forEach((b) => b.classList.toggle("active", b.dataset.t === t));
  const panel = $("#panel");
  panel.innerHTML = "";

  if (t === "transcript") {
    const pre = document.createElement("pre");
    pre.textContent = data.transcript;
    panel.append(pre);
    return;
  }

  const items = parseList(data[t]);
  if (!items.length) {
    panel.innerHTML = '<p class="empty">Nothing found in this recording.</p>';
    return;
  }
  const ul = document.createElement("ul");
  items.forEach((it) => {
    const li = document.createElement("li");
    const title = document.createElement("div");
    title.className = "t";
    title.textContent = it.title;
    li.append(title);
    it.sub.forEach((s) => {
      const d = document.createElement("div");
      d.className = "s";
      d.textContent = s;
      li.append(d);
    });
    ul.append(li);
  });
  panel.append(ul);
}
$$(".tab").forEach((b) => (b.onclick = () => renderTab(b.dataset.t)));

function fullText() {
  return `${data.title || "Analysis"}\n\nSUMMARY\n${data.summary}\n\nACTION ITEMS\n${data.action_items}\n\nKEY DECISIONS\n${data.key_decisions}\n\nOPEN QUESTIONS\n${data.open_questions}\n\nTRANSCRIPT\n${data.transcript}`;
}
$("#copyBtn").onclick = async () => {
  await navigator.clipboard.writeText(fullText());
  toast("Copied to clipboard");
};
$("#dlBtn").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([fullText()], { type: "text/plain" }));
  a.download = "analysis.txt";
  a.click();
  URL.revokeObjectURL(a.href);
};
$("#resetBtn").onclick = () => {
  $("#results").classList.add("hidden");
  clearFile();
  sessionId = null;
  data = null;
  window.scrollTo({ top: 0, behavior: "smooth" });
};

/* ---------- chat ---------- */
function addMsg(text, cls) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.textContent = text;
  $("#msgs").append(d);
  $("#msgs").scrollTop = 1e9;
  return d;
}
async function ask(q) {
  if (!q.trim() || !sessionId) return;
  addMsg(q, "user");
  const typing = addMsg("Thinking…", "bot typing");
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question: q }),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Chat failed");
    typing.classList.remove("typing");
    typing.textContent = json.answer;
    $("#msgs").scrollTop = 1e9;
  } catch (e) {
    typing.remove();
    toast(e.message, true);
  }
}
$("#chatForm").onsubmit = (e) => {
  e.preventDefault();
  const q = $("#q").value;
  $("#q").value = "";
  ask(q);
};
$$("#suggest button").forEach((b) => (b.onclick = () => ask(b.textContent)));