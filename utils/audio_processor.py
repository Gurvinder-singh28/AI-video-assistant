import yt_dlp
import os
import subprocess
from pathlib import Path
import imageio_ffmpeg
from yt_dlp.utils import DownloadError

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": ffmpeg_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filename = (
                ydl.prepare_filename(info)
                .replace(".webm", ".wav")
                .replace(".m4a", ".wav")
            )

        return filename

    except DownloadError as e:
        raise RuntimeError(f"YouTube download failed: {e}")


def convert_to_wav(input_path: str) -> str:
    """
    Convert audio/video file to WAV using ffmpeg.
    """

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    output_path = str(Path(input_path).with_suffix("")) + "_converted.wav"

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        output_path,
    ]

    subprocess.run(command, check=True)

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """
    Split WAV into chunks using ffmpeg.
    """

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    output_dir = wav_path + "_chunks"

    os.makedirs(output_dir, exist_ok=True)

    chunk_seconds = chunk_minutes * 60

    chunk_pattern = os.path.join(output_dir, "chunk_%03d.wav")

    command = [
        ffmpeg_path,
        "-i",
        wav_path,
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        chunk_pattern,
    ]

    subprocess.run(command, check=True)

    chunks = [
        os.path.join(output_dir, file)
        for file in os.listdir(output_dir)
        if file.endswith(".wav")
    ]

    return sorted(chunks)


def process_input(source: str) -> list:

    if source.startswith("http://") or source.startswith("https://"):

        print("Detected YouTube URL. Downloading audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local file. Converting to WAV...")

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    return chunks