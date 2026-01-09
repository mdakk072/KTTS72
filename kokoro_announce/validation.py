"""
Input validation and path safety utilities.

Provides secure validation for:
- File paths (prevent traversal attacks)
- User inputs (speed, device, text length)
- Voice file names
"""

from pathlib import Path
import re
import sys
from typing import Optional, Tuple

# Validation constants
MIN_SPEED = 0.25
MAX_SPEED = 4.0
MAX_TEXT_LENGTH = 100_000  # ~100KB of text
MAX_TEXT_FILE_SIZE = 10 * 1024 * 1024  # 10MB
VALID_DEVICES = frozenset(['cpu', 'cuda', 'mps', 'cuda:0', 'cuda:1', 'cuda:2', 'cuda:3'])
VALID_OUTPUT_FORMATS = frozenset(['wav', 'mp3'])
VALID_SAMPLE_RATES = frozenset([8000, 16000, 22050, 24000, 44100, 48000])
VOICE_NAME_PATTERN = re.compile(r'^[a-z]{2}_[a-z0-9_]+$')


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def get_safe_base_paths() -> Tuple[Path, ...]:
    """
    Get list of safe base paths for file operations.

    Returns paths where file I/O is allowed:
    - Current working directory
    - User's home directory
    - Temp directory
    - PyInstaller bundle directory (if frozen)
    """
    import tempfile

    safe_paths = [
        Path.cwd(),
        Path.home(),
        Path(tempfile.gettempdir()),
    ]

    # Add PyInstaller temp directory if running as frozen exe
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        safe_paths.append(Path(sys._MEIPASS))

    return tuple(p.resolve() for p in safe_paths)


def is_path_safe(path: Path, allow_creation: bool = False) -> bool:
    """
    Check if a path is safe for file operations.

    Prevents directory traversal attacks by ensuring the path
    is within allowed directories.

    Args:
        path: Path to validate
        allow_creation: If True, check parent for non-existent files

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve to absolute path (handles .., symlinks, etc.)
        if path.exists():
            resolved = path.resolve()
        elif allow_creation and path.parent.exists():
            resolved = path.parent.resolve() / path.name
        else:
            # For new files, resolve the parent
            resolved = path.resolve()

        safe_bases = get_safe_base_paths()

        # Check if path is under any safe base
        for safe_base in safe_bases:
            try:
                resolved.relative_to(safe_base)
                return True
            except ValueError:
                continue

        return False

    except (OSError, ValueError):
        return False


def validate_input_path(path: Path, purpose: str = "input") -> Path:
    """
    Validate an input file path.

    Args:
        path: Path to validate
        purpose: Description for error messages

    Returns:
        Validated absolute path

    Raises:
        ValidationError: If path is invalid or unsafe
    """
    if not path.exists():
        raise ValidationError(f"{purpose} file not found: {path}")

    if not path.is_file():
        raise ValidationError(f"{purpose} path is not a file: {path}")

    if not is_path_safe(path):
        raise ValidationError(f"{purpose} path is outside allowed directories: {path}")

    # Check file size for text files
    if path.stat().st_size > MAX_TEXT_FILE_SIZE:
        raise ValidationError(
            f"{purpose} file too large: {path.stat().st_size / 1024 / 1024:.1f}MB "
            f"(max {MAX_TEXT_FILE_SIZE / 1024 / 1024:.0f}MB)"
        )

    return path.resolve()


def validate_output_path(path: Path, purpose: str = "output") -> Path:
    """
    Validate an output file path.

    Args:
        path: Path to validate
        purpose: Description for error messages

    Returns:
        Validated absolute path

    Raises:
        ValidationError: If path is invalid or unsafe
    """
    resolved = path.resolve()

    if not is_path_safe(resolved, allow_creation=True):
        raise ValidationError(f"{purpose} path is outside allowed directories: {path}")

    # Check parent directory exists or can be created
    if not resolved.parent.exists():
        # Will be created by synthesize_to_file
        pass

    return resolved


def validate_speed(speed: float) -> float:
    """
    Validate playback speed.

    Args:
        speed: Speed multiplier

    Returns:
        Validated speed

    Raises:
        ValidationError: If speed is out of bounds
    """
    if not isinstance(speed, (int, float)):
        raise ValidationError(f"Speed must be a number, got {type(speed).__name__}")

    if speed < MIN_SPEED or speed > MAX_SPEED:
        raise ValidationError(
            f"Speed must be between {MIN_SPEED} and {MAX_SPEED}, got {speed}"
        )

    return float(speed)


def validate_device(device: Optional[str]) -> Optional[str]:
    """
    Validate PyTorch device string.

    Args:
        device: Device string or None for auto-detect

    Returns:
        Validated device string or None

    Raises:
        ValidationError: If device is invalid
    """
    if device is None:
        return None

    device = device.lower().strip()

    if device not in VALID_DEVICES:
        raise ValidationError(
            f"Invalid device '{device}'. Valid options: {', '.join(sorted(VALID_DEVICES))}"
        )

    return device


def validate_text(text: str) -> str:
    """
    Validate input text.

    Args:
        text: Text to synthesize

    Returns:
        Validated text (stripped)

    Raises:
        ValidationError: If text is empty or too long
    """
    if not isinstance(text, str):
        raise ValidationError(f"Text must be a string, got {type(text).__name__}")

    text = text.strip()

    if not text:
        raise ValidationError("Text cannot be empty")

    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(
            f"Text too long: {len(text)} characters (max {MAX_TEXT_LENGTH})"
        )

    return text


def validate_sample_rate(sample_rate: int) -> int:
    """
    Validate audio sample rate.

    Args:
        sample_rate: Sample rate in Hz

    Returns:
        Validated sample rate

    Raises:
        ValidationError: If sample rate is invalid
    """
    if sample_rate not in VALID_SAMPLE_RATES:
        raise ValidationError(
            f"Invalid sample rate {sample_rate}. "
            f"Valid options: {', '.join(str(r) for r in sorted(VALID_SAMPLE_RATES))}"
        )

    return sample_rate


def validate_output_format(fmt: str) -> str:
    """
    Validate output audio format.

    Args:
        fmt: Format string (wav, mp3)

    Returns:
        Validated format (lowercase)

    Raises:
        ValidationError: If format is invalid
    """
    fmt = fmt.lower().strip()

    if fmt not in VALID_OUTPUT_FORMATS:
        raise ValidationError(
            f"Invalid output format '{fmt}'. Valid options: {', '.join(sorted(VALID_OUTPUT_FORMATS))}"
        )

    return fmt


def validate_voice_name(voice: str) -> str:
    """
    Validate voice name format.

    Args:
        voice: Voice name (e.g., 'af_heart')

    Returns:
        Validated voice name

    Raises:
        ValidationError: If voice name format is invalid
    """
    if not isinstance(voice, str):
        raise ValidationError(f"Voice must be a string, got {type(voice).__name__}")

    voice = voice.strip()

    # Allow full paths to .pt files
    if voice.endswith('.pt'):
        return voice

    # Validate voice name pattern
    if not VOICE_NAME_PATTERN.match(voice):
        raise ValidationError(
            f"Invalid voice name format '{voice}'. "
            "Expected format: xx_name (e.g., af_heart, bm_lewis)"
        )

    return voice


def validate_lang_code(lang: str) -> str:
    """
    Validate language code.

    Args:
        lang: Language code (a, b, e, f)

    Returns:
        Validated language code

    Raises:
        ValidationError: If language code is invalid
    """
    valid_langs = {'a', 'b', 'e', 'f'}

    lang = lang.lower().strip()

    if lang not in valid_langs:
        raise ValidationError(
            f"Invalid language code '{lang}'. "
            f"Valid options: {', '.join(sorted(valid_langs))}"
        )

    return lang
