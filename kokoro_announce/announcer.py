from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import soundfile as sf

from .config import KokoroSettings, VoiceInput
from .pipeline import PipelineFactory
from .local_models import get_voice_path, models_exist


@dataclass
class SynthesisResult:
    """Container for synthesized audio and metadata."""

    graphemes: Sequence[str]
    phonemes: Sequence[str]
    audio: np.ndarray


class KokoroAnnouncer:
    """
    High-level synthesizer for announcement-style text.
    """

    def __init__(
        self,
        settings: Optional[KokoroSettings] = None,
        pipeline_factory: Optional[PipelineFactory] = None,
    ) -> None:
        self.settings = settings or KokoroSettings()
        self.pipeline_factory = pipeline_factory or PipelineFactory(self.settings)

    def _resolve_voice(self, voice: Optional[VoiceInput]) -> VoiceInput:
        """
        Resolve voice input, preferring local bundled voices if available.
        """
        resolved = voice if voice is not None else self.settings.voice

        # If voice is a string name and we have local models, use local voice file
        if isinstance(resolved, str) and models_exist():
            # Check if it's just a voice name (not a path)
            if not Path(resolved).exists():
                local_voice = get_voice_path(resolved)
                if Path(local_voice).exists():
                    return local_voice

        return resolved

    def synthesize_segments(
        self,
        text: str,
        *,
        voice: Optional[VoiceInput] = None,
        speed: Optional[float] = None,
        split_pattern=None,
    ) -> List[SynthesisResult]:
        """
        Return a list of SynthesisResult items, one per text chunk.
        """
        pipeline = self.pipeline_factory.get()
        speed = speed if speed is not None else self.settings.speed
        split_pattern = split_pattern or self.settings.split_pattern
        results: List[SynthesisResult] = []

        for graphemes, phonemes, audio in pipeline(
            text,
            voice=self._resolve_voice(voice),
            speed=speed,
            split_pattern=split_pattern,
        ):
            results.append(
                SynthesisResult(
                    graphemes=graphemes,
                    phonemes=phonemes,
                    audio=np.asarray(audio, dtype=np.float32),
                )
            )

        return results

    def synthesize(
        self,
        text: str,
        *,
        voice: Optional[VoiceInput] = None,
        speed: Optional[float] = None,
        split_pattern=None,
    ) -> np.ndarray:
        """
        Synthesize text and return a single waveform by concatenating segments.
        """
        segments = self.synthesize_segments(
            text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )
        if not segments:
            return np.zeros(0, dtype=np.float32)
        audio = [seg.audio for seg in segments]
        return np.concatenate(audio, axis=0)

    def synthesize_to_file(
        self,
        text: str,
        out_path: Path | str,
        *,
        voice: Optional[VoiceInput] = None,
        speed: Optional[float] = None,
        split_pattern=None,
        sample_rate: Optional[int] = None,
    ) -> Path:
        """
        Synthesize text and write a single WAV file. Returns the output path.
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        sample_rate = sample_rate or self.settings.sample_rate

        waveform = self.synthesize(
            text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )
        sf.write(out_path, waveform, sample_rate)
        return out_path

