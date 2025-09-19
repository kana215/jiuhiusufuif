
import os
import subprocess
import tempfile
from typing import Optional
from pydub import AudioSegment
import imageio_ffmpeg

TARGET_SR = 16000

def _ffmpeg_bin() -> str:
    """
    Returns a path to an ffmpeg binary. imageio-ffmpeg will download a static
    build on first use and cache it.
    """
    return imageio_ffmpeg.get_ffmpeg_exe()

def sniff_media_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().strip(".")
    return ext

def ensure_wav(path: str) -> str:
    """
    Convert any supported audio/video file to mono 16kHz WAV using ffmpeg.
    """
    out_wav = tempfile.mktemp(suffix=".wav")
    ff = _ffmpeg_bin()
    cmd = [
        ff, "-y", "-i", path,
        "-ac", "1",
        "-ar", str(TARGET_SR),
        out_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_wav
