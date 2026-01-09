"""
High-level helpers for generating speech with the Kokoro TTS model.

This package wraps `kokoro.KPipeline` with a small interface that is easier to
call from other runtimes (e.g., future C++ bindings). It focuses on the
announcement use case: pass text in, get back a waveform or a saved file.
"""

from .config import KokoroSettings, VoiceInput
from .pipeline import PipelineFactory
from .announcer import KokoroAnnouncer, SynthesisResult

__all__ = [
    "KokoroSettings",
    "VoiceInput",
    "PipelineFactory",
    "KokoroAnnouncer",
    "SynthesisResult",
]
