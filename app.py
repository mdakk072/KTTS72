"""
mdakk072
12/2025

Kokoro Announce - Simple TTS CLI Application

This app works in both development and PyInstaller frozen environments.
"""

import sys
import os
from pathlib import Path
import argparse

# CRITICAL: Protect sys.argv from being modified by subprocess calls
# spaCy tries to run pip install which changes sys.argv
_original_argv = sys.argv.copy()

# Disable spaCy's auto-download behavior
os.environ['SPACY_WARNING_IGNORE'] = 'W007,W008'

# CRITICAL FIX: Configure espeak for phonemization (needed for non-English languages)
# Must be done BEFORE importing phonemizer or kokoro
def _configure_espeak():
    """Set up espeak library and data paths for phonemizer."""
    try:
        # In frozen exe, espeakng_loader is bundled
        base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent

        # Try to use espeakng_loader if available
        try:
            import espeakng_loader
            dll_path = espeakng_loader.get_library_path()
            data_path = espeakng_loader.get_data_path()

            # In frozen exe, paths might be different
            if getattr(sys, 'frozen', False):
                # Check if DLL exists in _MEIPASS
                frozen_dll = base_path / 'espeakng_loader' / 'espeak-ng.dll'
                if frozen_dll.exists():
                    dll_path = str(frozen_dll)

                # Data should still be in the package location
                frozen_data = base_path / 'espeakng_loader' / 'espeak-ng-data'
                if frozen_data.exists():
                    data_path = str(frozen_data)

            os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = dll_path
            os.environ['ESPEAK_DATA_PATH'] = data_path

        except ImportError:
            pass  # espeakng_loader not available, phonemizer might find system espeak

    except Exception as e:
        pass  # Silently fail, American English will still work

_configure_espeak()

# CRITICAL FIX: Patch spacy.load to avoid loading en_core_web_sm
# misaki (g2p library) tries to load it but doesn't actually need it for TTS
def _patch_spacy():
    try:
        import spacy
        _original_load = spacy.load

        def _fake_load(name, **kwargs):
            if 'en_core_web_sm' in str(name):
                # Return a minimal fake model with just what misaki needs
                class FakeToken:
                    def __init__(self, text, has_space=True):
                        self.text = text
                        self.text_with_ws = text + (" " if has_space else "")
                        self.whitespace_ = " " if has_space else ""
                        self.tag_ = "NN"  # Fake POS tag
                        self.pos_ = "NOUN"  # Fake POS
                        self.lemma_ = text.lower()

                class FakeTokenizer:
                    def __call__(self, text):
                        # Simple word tokenization
                        words = text.split()
                        return [FakeToken(w) for w in words]

                class FakeModel:
                    def __init__(self):
                        self.tokenizer = FakeTokenizer()

                    def __call__(self, text):
                        # Make the model itself callable (delegates to tokenizer)
                        return self.tokenizer(text)

                return FakeModel()
            return _original_load(name, **kwargs)

        spacy.load = _fake_load
    except Exception as e:
        pass  # Silently fail if patching doesn't work

_patch_spacy()

# Monkey-patch subprocess to restore argv after any subprocess call
import subprocess
_original_run = subprocess.run
def _patched_run(*args, **kwargs):
    # Block pip install commands from spaCy
    if args and len(args) > 0:
        cmd = args[0] if isinstance(args[0], list) else []
        if 'pip' in str(cmd) or 'install' in str(cmd):
            # Return a fake successful result
            class FakeResult:
                returncode = 0
                stdout = b''
                stderr = b''
            return FakeResult()

    result = _original_run(*args, **kwargs)
    sys.argv = _original_argv  # Restore after subprocess
    return result
subprocess.run = _patched_run


def get_base_path():
    """Get the base path - works for both dev and frozen exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return Path(sys._MEIPASS)
    else:
        # Running as script
        return Path(__file__).parent


def list_voices():
    """List all available voices."""
    base_path = get_base_path()

    # Check in bundled models directory
    voices_dir = base_path / 'models' / 'voices'
    if not voices_dir.exists():
        # Try project root for development
        voices_dir = base_path / 'models' / 'voices'

    print("\nAvailable Voices:")
    print("=" * 60)

    if voices_dir.exists():
        voices = sorted([f.stem for f in voices_dir.glob('*.pt')])
        if voices:
            # Group by prefix
            groups = {}
            for voice in voices:
                prefix = voice[:2]  # af, am, bf, bm, etc.
                if prefix not in groups:
                    groups[prefix] = []
                groups[prefix].append(voice)

            prefix_names = {
                'af': 'American Female',
                'am': 'American Male',
                'bf': 'British Female',
                'bm': 'British Male',
                'ef': 'European Female',
                'em': 'European Male',
                'ff': 'French Female',
                'hf': 'Hindi Female',
                'hm': 'Hindi Male',
                'if': 'Italian Female',
                'im': 'Italian Male',
                'jf': 'Japanese Female',
                'jm': 'Japanese Male',
                'pf': 'Portuguese Female',
                'pm': 'Portuguese Male',
                'zf': 'Chinese Female',
                'zm': 'Chinese Male',
            }

            for prefix in sorted(groups.keys()):
                group_name = prefix_names.get(prefix, prefix.upper())
                print(f"\n{group_name}:")
                for voice in groups[prefix]:
                    print(f"  - {voice}")
        else:
            print("No voices found!")
    else:
        print(f"Voices directory not found: {voices_dir}")

    print("\n" + "=" * 60)


def list_languages():
    """List all available languages."""
    print("\nAvailable Languages:")
    print("=" * 60)
    print("Code | Language")
    print("-----|----------")
    print("a    | American English")
    print("b    | British English")
    print("e    | European (Spanish/Italian)")
    print("f    | French")
    print("h    | Hindi")
    print("i    | Italian")
    print("j    | Japanese")
    print("p    | Portuguese")
    print("z    | Chinese (Mandarin)")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""

    # Parse arguments
    parser = argparse.ArgumentParser(description="Kokoro TTS - Text-to-Speech Synthesizer")

    text_group = parser.add_mutually_exclusive_group(required=False)
    text_group.add_argument("--text", help="Text to synthesize")
    text_group.add_argument("--text-file", type=Path, help="Read text from file (UTF-8)")

    parser.add_argument("--out", type=Path, default=Path("output.wav"), help="Output WAV file path")
    parser.add_argument("--lang", default="a", help="Language code (a=American English)")
    parser.add_argument("--voice", default="af_heart", help="Voice name or path to .pt file")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier")
    parser.add_argument("--device", default=None, help="PyTorch device: cpu, cuda, mps")

    # List commands
    parser.add_argument("--list-voices", action="store_true", help="List all available voices")
    parser.add_argument("--list-languages", action="store_true", help="List all available languages")

    args = parser.parse_args()

    # Handle list commands
    if args.list_voices:
        list_voices()
        return 0

    if args.list_languages:
        list_languages()
        return 0

    # Require text if not listing
    if not args.text and not args.text_file:
        parser.error("one of the arguments --text --text-file is required (unless using --list-voices or --list-languages)")

    # Get text
    if args.text:
        text = args.text
    else:
        try:
            text = args.text_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[ERROR] Failed to read text file: {e}", file=sys.stderr)
            return 1

    if not text or not text.strip():
        print("[ERROR] Text is empty", file=sys.stderr)
        return 1

    # Now import after argparse (to avoid import side effects)
    try:
        from kokoro_announce import KokoroAnnouncer, KokoroSettings

        # Create settings
        settings = KokoroSettings(
            lang_code=args.lang,
            voice=args.voice,
            speed=args.speed,
            device=args.device,
        )

        # Create announcer
        announcer = KokoroAnnouncer(settings)

        # Synthesize
        print(f"Synthesizing: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        out_path = announcer.synthesize_to_file(text, args.out)

        print(f"[OK] Wrote {out_path}")
        return 0

    except Exception as e:
        print(f"[ERROR] Synthesis failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
