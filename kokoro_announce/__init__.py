"""
Kokoro Announce - High-level TTS wrapper for Kokoro-82M.

This package provides an easy-to-use interface for text-to-speech synthesis
using the Kokoro-82M neural TTS model. It supports multiple languages,
voices, and output formats.

Example:
    >>> from kokoro_announce import KokoroAnnouncer, KokoroSettings
    >>> settings = KokoroSettings(voice="af_heart", lang_code="a")
    >>> announcer = KokoroAnnouncer(settings)
    >>> announcer.synthesize_to_file("Hello world", "output.wav")

Features:
    - 32 pre-trained voices across 4 languages
    - WAV and MP3 output formats
    - Fully offline operation (with bundled models)
    - Adjustable speed and sample rate
    - Input validation and path security
"""

from .config import KokoroSettings, VoiceInput
from .pipeline import PipelineFactory
from .announcer import KokoroAnnouncer, SynthesisResult
from .validation import ValidationError
from .audio import write_audio, check_mp3_support
from .patches import apply_all_patches

__all__ = [
    # Main API
    "KokoroSettings",
    "VoiceInput",
    "PipelineFactory",
    "KokoroAnnouncer",
    "SynthesisResult",
    # Utilities
    "ValidationError",
    "write_audio",
    "check_mp3_support",
    "apply_all_patches",
]

__version__ = "1.1.0"
