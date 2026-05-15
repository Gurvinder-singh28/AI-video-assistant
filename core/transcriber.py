import whisper
import whisper.audio
import torch
import os
import imageio_ffmpeg

# --- Monkey-patch Whisper to use imageio_ffmpeg binary directly ---
_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def _patched_load_audio(file: str, sr: int = whisper.audio.SAMPLE_RATE):
    import numpy as np
    import subprocess
    cmd = [
        _FFMPEG,
        "-nostdin",
        "-threads", "0",
        "-i", file,
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-",
    ]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

whisper.audio.load_audio = _patched_load_audio
whisper.transcribe.load_audio = _patched_load_audio
# -----------------------------------------------------------------

_model = None

def _get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model on {device}...")
        _model = whisper.load_model("base", device=device)
    return _model


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    model = _get_model()
    lang_map = {"english": "en", "hinglish": "hi"}
    lang_code = lang_map.get(language.lower(), "en")
    result = model.transcribe(chunk_path, language=lang_code, fp16=False)
    return result["text"].strip()


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = []
    for i, chunk_path in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}: {os.path.basename(chunk_path)}")
        text = transcribe_chunk(chunk_path, language)
        full_transcript.append(text)
    return " ".join(full_transcript)