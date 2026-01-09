"""
Kokoro72CLI - High-quality offline text-to-speech.

Main entry point for the CLI application. This is the file that gets
packaged into the standalone Windows executable.

Usage:
    Kokoro72CLI.exe --text "Hello world" --out hello.wav
    Kokoro72CLI.exe --text-file script.txt --voice am_adam --out speech.mp3
    Kokoro72CLI.exe --list-voices
"""

import sys

# Apply runtime patches BEFORE any other imports
# This must happen first to configure espeak and patch spaCy
from kokoro_announce.patches import apply_all_patches
apply_all_patches()

# Now import the rest
from kokoro_announce import KokoroAnnouncer, KokoroSettings, ValidationError
from kokoro_announce.cli import (
    create_parser,
    list_voices,
    list_languages,
    validate_args,
    get_output_format,
    print_synthesis_info,
)


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle list commands (no text required)
    if args.list_voices:
        list_voices()
        return 0

    if args.list_languages:
        list_languages()
        return 0

    # Require text for synthesis
    if not args.text and not args.text_file:
        parser.error(
            "one of --text or --text-file is required "
            "(unless using --list-voices or --list-languages)"
        )

    try:
        # Validate all arguments
        text, output_path = validate_args(args)
        output_format = get_output_format(args)

        # Print synthesis info
        print_synthesis_info(
            text=text,
            output_path=output_path,
            voice=args.voice,
            lang=args.lang,
            speed=args.speed,
            sample_rate=args.sample_rate,
            format=output_format,
            verbose=args.verbose,
        )

        # Create settings and announcer
        settings = KokoroSettings(
            lang_code=args.lang,
            voice=args.voice,
            speed=args.speed,
            device=args.device,
            sample_rate=args.sample_rate,
        )

        announcer = KokoroAnnouncer(settings)

        # Synthesize
        out_path = announcer.synthesize_to_file(
            text,
            output_path,
            format=output_format,
        )

        print(f"[OK] Wrote {out_path}")
        return 0

    except ValidationError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        # MP3 encoding errors, etc.
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
