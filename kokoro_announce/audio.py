"""
Audio output handling for different formats.

Supports:
- WAV (native, always available)
- MP3 (requires ffmpeg or pydub with ffmpeg)
"""

from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import subprocess
import tempfile
import os


def write_wav(
    audio: np.ndarray,
    path: Path,
    sample_rate: int = 24000,
) -> Path:
    """
    Write audio to WAV file.

    Args:
        audio: Audio waveform as numpy array
        path: Output path
        sample_rate: Sample rate in Hz

    Returns:
        Path to written file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sample_rate)
    return path


def write_mp3(
    audio: np.ndarray,
    path: Path,
    sample_rate: int = 24000,
    bitrate: str = "192k",
) -> Path:
    """
    Write audio to MP3 file.

    Uses ffmpeg if available, otherwise falls back to pydub.

    Args:
        audio: Audio waveform as numpy array
        path: Output path
        sample_rate: Sample rate in Hz
        bitrate: MP3 bitrate (e.g., "128k", "192k", "320k")

    Returns:
        Path to written file

    Raises:
        RuntimeError: If MP3 encoding is not available
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Try ffmpeg first (more reliable)
    if _has_ffmpeg():
        return _write_mp3_ffmpeg(audio, path, sample_rate, bitrate)

    # Try pydub as fallback
    try:
        return _write_mp3_pydub(audio, path, sample_rate, bitrate)
    except ImportError:
        pass

    raise RuntimeError(
        "MP3 encoding requires ffmpeg. "
        "Please install ffmpeg and add it to your PATH."
    )


def _has_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False


def _write_mp3_ffmpeg(
    audio: np.ndarray,
    path: Path,
    sample_rate: int,
    bitrate: str,
) -> Path:
    """Write MP3 using ffmpeg."""
    # Write temporary WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        sf.write(str(tmp_path), audio, sample_rate)

        # Convert to MP3
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",  # Overwrite output
                "-i", str(tmp_path),
                "-b:a", bitrate,
                "-q:a", "2",  # VBR quality
                str(path),
            ],
            capture_output=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")

        return path

    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except OSError:
            pass


def _write_mp3_pydub(
    audio: np.ndarray,
    path: Path,
    sample_rate: int,
    bitrate: str,
) -> Path:
    """Write MP3 using pydub (requires ffmpeg anyway)."""
    from pydub import AudioSegment

    # Convert numpy array to pydub AudioSegment
    # Normalize to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)

    segment = AudioSegment(
        audio_int16.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,  # 16-bit
        channels=1,
    )

    # Export as MP3
    segment.export(
        str(path),
        format="mp3",
        bitrate=bitrate,
    )

    return path


def write_audio(
    audio: np.ndarray,
    path: Path,
    sample_rate: int = 24000,
    format: Optional[str] = None,
) -> Path:
    """
    Write audio to file in specified format.

    Args:
        audio: Audio waveform as numpy array
        path: Output path
        sample_rate: Sample rate in Hz
        format: Output format ('wav' or 'mp3'). If None, inferred from path.

    Returns:
        Path to written file

    Raises:
        ValueError: If format is unknown
        RuntimeError: If format encoding is not available
    """
    if format is None:
        format = path.suffix.lstrip('.').lower()

    if format == 'wav':
        return write_wav(audio, path, sample_rate)
    elif format == 'mp3':
        return write_mp3(audio, path, sample_rate)
    else:
        raise ValueError(f"Unknown audio format: {format}")


def check_mp3_support() -> bool:
    """
    Check if MP3 encoding is supported.

    Returns:
        True if MP3 can be encoded, False otherwise
    """
    if _has_ffmpeg():
        return True

    try:
        import pydub
        return True
    except ImportError:
        return False
