"""
Command-line interface for Kokoro TTS.

Provides the main CLI functionality including:
- Argument parsing
- Voice/language listing
- Text synthesis with various output formats
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .validation import (
    ValidationError,
    validate_speed,
    validate_device,
    validate_text,
    validate_sample_rate,
    validate_output_format,
    validate_voice_name,
    validate_lang_code,
    validate_input_path,
    validate_output_path,
    VALID_SAMPLE_RATES,
    VALID_OUTPUT_FORMATS,
    MIN_SPEED,
    MAX_SPEED,
)


# Voice metadata for listing (English, French, Spanish only)
VOICE_PREFIXES = {
    'af': 'American Female',
    'am': 'American Male',
    'bf': 'British Female',
    'bm': 'British Male',
    'ef': 'Spanish Female',
    'em': 'Spanish Male',
    'ff': 'French Female',
}

# Supported languages (English, French, Spanish)
LANGUAGES = {
    'a': 'American English',
    'b': 'British English',
    'e': 'Spanish',
    'f': 'French',
}


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="Kokoro72CLI",
        description="Kokoro TTS - High-quality offline text-to-speech synthesis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --text "Hello world" --out hello.wav
  %(prog)s --text-file script.txt --voice am_adam --speed 1.2
  %(prog)s --text "Bonjour" --lang f --voice ff_siwis --out french.mp3
  %(prog)s --text "Hola mundo" --lang e --voice ef_dora --out spanish.wav
  %(prog)s --list-voices
  %(prog)s --list-languages
        """,
    )

    # Text input (mutually exclusive)
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument(
        "--text", "-t",
        help="Text to synthesize",
    )
    text_group.add_argument(
        "--text-file", "-f",
        type=Path,
        help="Read text from UTF-8 file",
    )

    # Output settings
    parser.add_argument(
        "--out", "-o",
        type=Path,
        default=Path("output.wav"),
        help="Output file path (default: output.wav)",
    )
    parser.add_argument(
        "--format",
        choices=sorted(VALID_OUTPUT_FORMATS),
        help="Output format (default: inferred from --out extension)",
    )
    parser.add_argument(
        "--sample-rate", "-r",
        type=int,
        default=24000,
        choices=sorted(VALID_SAMPLE_RATES),
        help="Audio sample rate in Hz (default: 24000)",
    )

    # Voice settings
    parser.add_argument(
        "--voice", "-v",
        default="af_heart",
        help="Voice name (default: af_heart)",
    )
    parser.add_argument(
        "--lang", "-l",
        default="a",
        help="Language code: a=American, b=British, e=Spanish, f=French (default: a)",
    )
    parser.add_argument(
        "--speed", "-s",
        type=float,
        default=1.0,
        help=f"Playback speed {MIN_SPEED}-{MAX_SPEED} (default: 1.0)",
    )

    # Hardware settings
    parser.add_argument(
        "--device", "-d",
        default=None,
        help="PyTorch device: cpu, cuda, mps (default: auto)",
    )

    # List commands
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List all available voices",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List all available languages",
    )

    # Debug
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    return parser


def get_base_path() -> Path:
    """Get the base path for bundled resources."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent


def list_voices() -> None:
    """List all available voices grouped by type."""
    base_path = get_base_path()
    voices_dir = base_path / 'models' / 'voices'

    print("\nAvailable Voices:")
    print("=" * 60)

    if voices_dir.exists():
        voices = sorted([f.stem for f in voices_dir.glob('*.pt')])
        if voices:
            # Group by prefix
            groups = {}
            for voice in voices:
                prefix = voice[:2]
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append(voice)

            for prefix in sorted(groups.keys()):
                group_name = VOICE_PREFIXES.get(prefix, prefix.upper())
                print(f"\n{group_name}:")
                for voice in groups[prefix]:
                    print(f"  - {voice}")
        else:
            print("No voices found!")
    else:
        print(f"Voices directory not found: {voices_dir}")
        print("Run setup_env.bat to download models.")

    print("\n" + "=" * 60)


def list_languages() -> None:
    """List all available languages."""
    print("\nSupported Languages:")
    print("=" * 60)
    print("Code | Language          | Voices")
    print("-----|-------------------|--------")
    print("  a  | American English  | 20")
    print("  b  | British English   | 8")
    print("  e  | Spanish           | 3")
    print("  f  | French            | 1")
    print("=" * 60 + "\n")


def validate_args(args: argparse.Namespace) -> Tuple[str, Path]:
    """
    Validate parsed arguments.

    Args:
        args: Parsed arguments

    Returns:
        Tuple of (validated_text, validated_output_path)

    Raises:
        ValidationError: If any argument is invalid
    """
    # Validate voice and language
    validate_voice_name(args.voice)
    validate_lang_code(args.lang)
    validate_speed(args.speed)
    validate_device(args.device)
    validate_sample_rate(args.sample_rate)

    # Validate format if specified
    if args.format:
        validate_output_format(args.format)

    # Get and validate text
    if args.text:
        text = validate_text(args.text)
    elif args.text_file:
        input_path = validate_input_path(args.text_file, "Text file")
        try:
            raw_text = input_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValidationError(f"Text file is not valid UTF-8: {e}")
        text = validate_text(raw_text)
    else:
        raise ValidationError(
            "Either --text or --text-file is required "
            "(unless using --list-voices or --list-languages)"
        )

    # Validate output path
    output_path = validate_output_path(args.out, "Output file")

    return text, output_path


def get_output_format(args: argparse.Namespace) -> str:
    """
    Determine output format from args or file extension.

    Args:
        args: Parsed arguments

    Returns:
        Output format string ('wav' or 'mp3')
    """
    if args.format:
        return args.format

    ext = args.out.suffix.lstrip('.').lower()
    if ext in VALID_OUTPUT_FORMATS:
        return ext

    # Default to wav
    return 'wav'


def print_synthesis_info(
    text: str,
    output_path: Path,
    voice: str,
    lang: str,
    speed: float,
    sample_rate: int,
    format: str,
    verbose: bool = False,
) -> None:
    """Print information about the synthesis operation."""
    preview = text[:50] + ('...' if len(text) > 50 else '')
    print(f"Synthesizing: '{preview}'")

    if verbose:
        print(f"  Voice: {voice}")
        print(f"  Language: {LANGUAGES.get(lang, lang)}")
        print(f"  Speed: {speed}x")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Format: {format.upper()}")
        print(f"  Output: {output_path}")
