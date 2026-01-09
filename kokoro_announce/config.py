from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Pattern, Union

try:  # Torch is optional at import time; type-checkers can still see it.
    import torch

    TorchTensor = torch.Tensor
except Exception:
    TorchTensor = object


VoiceInput = Union[str, Path, TorchTensor]


@dataclass
class KokoroSettings:
    """
    Configuration for a Kokoro pipeline.

    lang_code: see Kokoro docs (e.g., 'a' for American English).
    voice: name, path to a voice tensor, or an in-memory tensor.
    speed: playback speed multiplier.
    split_pattern: regex used to chunk long text into utterances.
    sample_rate: output sample rate for saved files.
    device: optional device string for PyTorch (e.g., 'cpu', 'cuda', 'mps').
    """

    lang_code: str = "a"
    voice: Optional[VoiceInput] = "af_heart"
    speed: float = 1.0
    split_pattern: Pattern[str] = re.compile(r"\n+")
    sample_rate: int = 24000
    device: Optional[str] = None

