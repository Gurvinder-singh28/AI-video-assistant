import yt_dlp
import os
import subprocess
from pathlib import Path
import imageio_ffmpeg
from yt_dlp.utils import DownloadError

DOWNLOAD_DIR = "/tmp/ai_video_assistant"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Download YouTube audio using yt-dlp.

    Render:
    - /etc/secrets/cookies.txt = read-only secret
    - /tmp/ai_video_assistant = writable temporary directory
    """

    download_dir = "/tmp/ai_video_assistant"
    os.makedirs(download_dir, exist_ok=True)

    output_path = os.path.join(
        download_dir,
        "%(id)s.%(ext)s"
    )

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    cookies_path = "/etc/secrets/cookies.txt"

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
        "no_warnings": True,
        "noplaylist": True,

        "retries": 3,
        "fragment_retries": 3,

        "remote_components": ["ejs:github"],
    }

    # Use Render Secret File only as a READ-ONLY source
    if os.path.isfile(cookies_path):
        print("YouTube cookies found. Using Render cookies...")
        ydl_opts["cookiefile"] = cookies_path
    else:
        print("No YouTube cookies found. Trying without cookies...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)

        # yt-dlp/FFmpeg changes the extension to .wav
        filename = str(
            Path(filename).with_suffix(".wav")
        )

        if not os.path.exists(filename):
            raise RuntimeError(
                f"Downloaded audio file was not found: {filename}"
            )

        return filename

    except DownloadError as e:
        error_message = str(e)

        if "Sign in to confirm you're not a bot" in error_message:
            raise RuntimeError(
                "YouTube blocked the download. "
                "Please refresh the cookies.txt file in Render Secret Files."
            )

        raise RuntimeError(
            f"YouTube download failed: {error_message}"
        )


def convert_to_wav(input_path: str) -> str:
    """
    Convert audio/video file to WAV using FFmpeg.
    """

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    output_path = (
        str(Path(input_path).with_suffix(""))
        + "_converted.wav"
    )

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

    subprocess.run(
        command,
        check=True
    )

    return output_path


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV into chunks using FFmpeg.
    """

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    output_dir = wav_path + "_chunks"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    chunk_seconds = chunk_minutes * 60

    chunk_pattern = os.path.join(
        output_dir,
        "chunk_%03d.wav"
    )

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

    subprocess.run(
        command,
        check=True
    )

    chunks = [
        os.path.join(
            output_dir,
            file
        )
        for file in os.listdir(output_dir)
        if file.endswith(".wav")
    ]

    return sorted(chunks)


def process_input(source: str) -> list:

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL. "
            "Downloading audio..."
        )

        wav_path = download_youtube_audio(source)

    else:

        print(
            "Detected local file. "
            "Converting to WAV..."
        )

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s) created."
    )

    return chunks