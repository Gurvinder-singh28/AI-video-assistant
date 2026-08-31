import os
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from yt_dlp.utils import DownloadError


# ============================================================
# DIRECTORIES
# ============================================================

# Render allows writing to /tmp
DOWNLOAD_DIR = "/tmp/ai_video_assistant"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ============================================================
# YOUTUBE AUDIO DOWNLOAD
# ============================================================

def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL using yt-dlp.

    Render Secret File:
        /etc/secrets/cookies.txt

    IMPORTANT:
        /etc/secrets is READ-ONLY on Render.

    Therefore:
        1. Read cookies from /etc/secrets/cookies.txt
        2. Copy them to /tmp/cookies.txt
        3. Give /tmp/cookies.txt to yt-dlp
        4. Delete the temporary cookie file afterwards
    """

    # --------------------------------------------------------
    # Writable download directory
    # --------------------------------------------------------

    download_dir = DOWNLOAD_DIR

    os.makedirs(
        download_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Download output filename
    # --------------------------------------------------------

    output_path = os.path.join(
        download_dir,
        "%(id)s.%(ext)s"
    )

    # --------------------------------------------------------
    # FFmpeg
    # --------------------------------------------------------

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    # --------------------------------------------------------
    # Render Secret File
    # --------------------------------------------------------

    render_cookies = "/etc/secrets/cookies.txt"

    # IMPORTANT:
    # This file is writable.
    temp_cookies = "/tmp/cookies.txt"

    # --------------------------------------------------------
    # Copy Render Secret File to /tmp
    # --------------------------------------------------------

    cookies_available = False

    if os.path.isfile(render_cookies):

        try:

            shutil.copyfile(
                render_cookies,
                temp_cookies
            )

            cookies_available = True

            print(
                "✅ YouTube cookies copied to /tmp/cookies.txt",
                flush=True
            )

        except Exception as e:

            raise RuntimeError(
                f"❌ Could not copy YouTube cookies: {e}"
            )

    else:

        print(
            "⚠️ /etc/secrets/cookies.txt was not found.",
            flush=True
        )

        print(
            "Trying YouTube without cookies...",
            flush=True
        )

    # --------------------------------------------------------
    # yt-dlp configuration
    # --------------------------------------------------------

    ydl_opts = {

        # Best available audio
        "format": "bestaudio/best",

        # Download location
        "outtmpl": output_path,

        # FFmpeg location
        "ffmpeg_location": ffmpeg_path,

        # Convert downloaded audio to WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        # Don't download playlists
        "noplaylist": True,

        # Retry settings
        "retries": 3,
        "fragment_retries": 3,

        # Required by newer YouTube extraction
        "remote_components": [
            "ejs:github"
        ],

        # Show useful logs on Render
        "quiet": False,
        "no_warnings": False,

        # Don't save anything in /etc/secrets
        "cachedir": False,
    }

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # NEVER give yt-dlp:
    #
    # /etc/secrets/cookies.txt
    #
    # Give it:
    #
    # /tmp/cookies.txt
    # --------------------------------------------------------

    if cookies_available:

        ydl_opts["cookiefile"] = temp_cookies

        print(
            "✅ yt-dlp will use: /tmp/cookies.txt",
            flush=True
        )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    try:

        print(
            "▶️ Starting YouTube download...",
            flush=True
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            # Original downloaded filename
            filename = ydl.prepare_filename(info)

        # ----------------------------------------------------
        # FFmpegExtractAudio converts it to WAV
        # ----------------------------------------------------

        wav_filename = str(
            Path(filename).with_suffix(".wav")
        )

        # ----------------------------------------------------
        # Check downloaded file
        # ----------------------------------------------------

        if not os.path.exists(wav_filename):

            # Sometimes yt-dlp/FFmpeg may already have
            # produced a WAV file with a slightly different
            # path. Search the download directory.

            video_id = info.get("id")

            possible_wav = os.path.join(
                download_dir,
                f"{video_id}.wav"
            )

            if os.path.exists(possible_wav):

                wav_filename = possible_wav

            else:

                raise RuntimeError(
                    "YouTube download completed, "
                    "but the WAV audio file was not found."
                )

        print(
            f"✅ Audio downloaded successfully: {wav_filename}",
            flush=True
        )

        return wav_filename

    except DownloadError as e:

        error_message = str(e)

        # ----------------------------------------------------
        # YouTube bot/authentication error
        # ----------------------------------------------------

        if (
            "Sign in to confirm you're not a bot"
            in error_message
        ):

            raise RuntimeError(
                "YouTube rejected the cookies. "
                "The Render filesystem is working correctly, "
                "but the cookies are invalid/expired. "
                "Please replace the cookies.txt Secret File "
                "in Render with a valid fresh cookie file."
            )

        # ----------------------------------------------------
        # Read-only filesystem error
        # ----------------------------------------------------

        if "Read-only file system" in error_message:

            raise RuntimeError(
                "A read-only filesystem error occurred. "
                "Make sure yt-dlp is using /tmp/cookies.txt "
                "and NOT /etc/secrets/cookies.txt."
            )

        raise RuntimeError(
            f"YouTube download failed: {error_message}"
        )

    except Exception as e:

        raise RuntimeError(
            f"YouTube audio processing failed: {e}"
        )

    finally:

        # ----------------------------------------------------
        # Delete temporary cookie file
        # ----------------------------------------------------

        try:

            if os.path.exists(temp_cookies):

                os.remove(temp_cookies)

                print(
                    "🧹 Temporary cookies removed.",
                    flush=True
                )

        except Exception as cleanup_error:

            print(
                f"⚠️ Could not remove temporary cookies: "
                f"{cleanup_error}",
                flush=True
            )


# ============================================================
# CONVERT AUDIO/VIDEO TO WAV
# ============================================================

def convert_to_wav(input_path: str) -> str:
    """
    Convert an audio/video file to WAV using FFmpeg.

    Output:
        Mono
        16 kHz
        WAV
    """

    # --------------------------------------------------------
    # FFmpeg
    # --------------------------------------------------------

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    # --------------------------------------------------------
    # Output path
    # --------------------------------------------------------

    output_path = (
        str(Path(input_path).with_suffix(""))
        + "_converted.wav"
    )

    # --------------------------------------------------------
    # FFmpeg command
    # --------------------------------------------------------

    command = [
        ffmpeg_path,

        "-y",

        "-i",
        input_path,

        # Mono audio
        "-ac",
        "1",

        # 16 kHz
        "-ar",
        "16000",

        output_path,
    ]

    # --------------------------------------------------------
    # Run FFmpeg
    # --------------------------------------------------------

    subprocess.run(
        command,
        check=True
    )

    return output_path


# ============================================================
# CHUNK AUDIO
# ============================================================

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into smaller chunks using FFmpeg.

    Default:
        10 minutes per chunk
    """

    # --------------------------------------------------------
    # FFmpeg
    # --------------------------------------------------------

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    output_dir = wav_path + "_chunks"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Convert minutes to seconds
    # --------------------------------------------------------

    chunk_seconds = chunk_minutes * 60

    # --------------------------------------------------------
    # Chunk filename pattern
    # --------------------------------------------------------

    chunk_pattern = os.path.join(
        output_dir,
        "chunk_%03d.wav"
    )

    # --------------------------------------------------------
    # FFmpeg command
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Run FFmpeg
    # --------------------------------------------------------

    subprocess.run(
        command,
        check=True
    )

    # --------------------------------------------------------
    # Find generated chunks
    # --------------------------------------------------------

    chunks = [
        os.path.join(
            output_dir,
            file
        )
        for file in os.listdir(output_dir)
        if file.endswith(".wav")
    ]

    # --------------------------------------------------------
    # Sort chunks
    # --------------------------------------------------------

    return sorted(chunks)


# ============================================================
# PROCESS INPUT
# ============================================================

def process_input(source: str) -> list:
    """
    Process either:

    1. YouTube URL
    2. Local audio/video file

    Returns:
        List of WAV audio chunks.
    """

    # --------------------------------------------------------
    # YouTube URL
    # --------------------------------------------------------

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL. "
            "Downloading audio...",
            flush=True
        )

        wav_path = download_youtube_audio(
            source
        )

    # --------------------------------------------------------
    # Local file
    # --------------------------------------------------------

    else:

        print(
            "Detected local file. "
            "Converting to WAV...",
            flush=True
        )

        wav_path = convert_to_wav(
            source
        )

    # --------------------------------------------------------
    # Chunk audio
    # --------------------------------------------------------

    print(
        "Chunking audio...",
        flush=True
    )

    chunks = chunk_audio(
        wav_path
    )

    # --------------------------------------------------------
    # Final message
    # --------------------------------------------------------

    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s) created.",
        flush=True
    )

    return chunks