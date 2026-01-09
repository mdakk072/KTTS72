"""
High-level TTS synthesizer API.

Provides the main KokoroAnnouncer class for text-to-speech synthesis
with support for multiple output formats and secure file handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from .audio import write_audio
from .config import KokoroSettings, VoiceInput
from .pipeline import PipelineFactory
from .local_models import get_voice_path, models_exist
from .validation import (
    ValidationError,
    validate_output_path,
    validate_speed,
    validate_text,
    validate_sample_rate,
    validate_output_format,
)


@dataclass
class SynthesisResult:
    """Container for synthesized audio and metadata."""

    graphemes: Sequence[str]
    phonemes: Sequence[str]
    audio: np.ndarray


class KokoroAnnouncer:
    """
    High-level synthesizer for text-to-speech.

    Example:
        >>> settings = KokoroSettings(voice="af_heart", lang_code="a")
        >>> announcer = KokoroAnnouncer(settings)
        >>> announcer.synthesize_to_file("Hello world", "output.wav")
    """

    def __init__(
        self,
        settings: Optional[KokoroSettings] = None,
        pipeline_factory: Optional[PipelineFactory] = None,
    ) -> None:
        """
        Initialize the announcer.

        Args:
            settings: Configuration settings. Uses defaults if None.
            pipeline_factory: Custom pipeline factory. Creates one if None.
        """
        self.settings = settings or KokoroSettings()
        self.pipeline_factory = pipeline_factory or PipelineFactory(self.settings)

    def _resolve_voice(self, voice: Optional[VoiceInput]) -> VoiceInput:
        """
        Resolve voice input to a valid voice path or name.

        Prefers local bundled voices if available for offline operation.
        """
        resolved = voice if voice is not None else self.settings.voice

        # If voice is a string name and we have local models, use local voice file
        if isinstance(resolved, str) and models_exist():
            # Check if it's just a voice name (not already a path)
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
        Synthesize text and return individual segments.

        Args:
            text: Text to synthesize
            voice: Voice override (uses settings if None)
            speed: Speed override (uses settings if None)
            split_pattern: Pattern to split text into segments

        Returns:
            List of SynthesisResult for each text segment
        """
        # Validate inputs
        text = validate_text(text)
        if speed is not None:
            speed = validate_speed(speed)
        else:
            speed = self.settings.speed

        pipeline = self.pipeline_factory.get()
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
        Synthesize text and return a single concatenated waveform.

        Args:
            text: Text to synthesize
            voice: Voice override
            speed: Speed override
            split_pattern: Pattern to split text into segments

        Returns:
            Audio waveform as numpy array (float32, mono)
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
        format: Optional[str] = None,
    ) -> Path:
        """
        Synthesize text and write to an audio file.

        Supports WAV (native) and MP3 (requires ffmpeg) formats.

        Args:
            text: Text to synthesize
            out_path: Output file path
            voice: Voice override
            speed: Speed override
            split_pattern: Pattern to split text into segments
            sample_rate: Sample rate override (default: 24000)
            format: Output format override ('wav' or 'mp3')

        Returns:
            Path to the written file

        Raises:
            ValidationError: If output path is invalid or unsafe
            RuntimeError: If format encoding is not available
        """
        out_path = Path(out_path)

        # Validate output path (security check)
        validated_path = validate_output_path(out_path, "Output file")

        # Validate sample rate
        sample_rate = sample_rate or self.settings.sample_rate
        sample_rate = validate_sample_rate(sample_rate)

        # Validate format if specified
        if format:
            format = validate_output_format(format)

        # Synthesize audio
        waveform = self.synthesize(
            text,
            voice=voice,
            speed=speed,
            split_pattern=split_pattern,
        )

        # Write to file with appropriate format
        return write_audio(
            waveform,
            validated_path,
            sample_rate=sample_rate,
            format=format,
        )
