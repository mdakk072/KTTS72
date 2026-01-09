from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .announcer import KokoroAnnouncer
from .config import KokoroSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthesize announcements with Kokoro TTS.",
    )
    text_source = parser.add_mutually_exclusive_group(required=True)
    text_source.add_argument(
        "--text",
        help="Text to speak.",
    )
    text_source.add_argument(
        "--text-file",
        type=Path,
        help="Path to a UTF-8 text file to speak.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("announcement.wav"),
        help="Path to write the WAV file (default: announcement.wav).",
    )
    parser.add_argument(
        "--lang",
        default="a",
        help="Kokoro language code (default: a = American English).",
    )
    parser.add_argument(
        "--voice",
        default="af_heart",
        help="Voice name or path to a voice tensor.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier (default: 1.0).",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional torch device (e.g., cpu, cuda, mps).",
    )
    return parser


def main() -> int:
    """Main entry point."""
    # When running as a PyInstaller bundle, sys.argv might be modified by
    # other libraries. The `pyi_rth_argv_fix` hook saves the original
    # argv in `sys._original_argv`.
    if hasattr(sys, "_original_argv"):
        argv = sys._original_argv[1:]
    else:
        # Fallback for running as a normal script
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    text = args.text
    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8")

    settings = KokoroSettings(
        lang_code=args.lang,
        voice=args.voice,
        speed=args.speed,
        device=args.device,
    )
    announcer = KokoroAnnouncer(settings)

    try:
        out_path = announcer.synthesize_to_file(text, args.out)
    except Exception as exc:
        parser.error(f"Failed to synthesize: {exc}")
        return 1

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
