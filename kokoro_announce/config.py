"""
Configuration for Kokoro TTS pipeline.

Defines the settings dataclass and type aliases used throughout
the kokoro_announce package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Pattern, Union

try:
    import torch
    TorchTensor = torch.Tensor
except Exception:
    TorchTensor = object


# Type alias for voice inputs
VoiceInput = Union[str, Path, TorchTensor]


# Default constants
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_SPEED = 1.0
DEFAULT_LANG_CODE = "a"
DEFAULT_VOICE = "af_heart"


@dataclass
class KokoroSettings:
    """
    Configuration for a Kokoro TTS pipeline.

    Attributes:
        lang_code: Language code for text processing:
            - 'a': American English
            - 'b': British English
            - 'e': European Spanish
            - 'f': French
        voice: Voice name (e.g., 'af_heart'), path to .pt file, or tensor
        speed: Playback speed multiplier (0.25 to 4.0)
        split_pattern: Regex to split long text into segments
        sample_rate: Output audio sample rate in Hz
        device: PyTorch device ('cpu', 'cuda', 'mps', or None for auto)
    """

    lang_code: str = DEFAULT_LANG_CODE
    voice: Optional[VoiceInput] = DEFAULT_VOICE
    speed: float = DEFAULT_SPEED
    split_pattern: Pattern[str] = re.compile(r"\n+")
    sample_rate: int = DEFAULT_SAMPLE_RATE
    device: Optional[str] = None
