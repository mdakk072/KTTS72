"""
Runtime patches for third-party library compatibility.

This module contains necessary patches to make the Kokoro TTS pipeline
work correctly in a PyInstaller bundle. These patches address specific
issues with spaCy and espeak that occur in frozen environments.

Patches are designed to be:
- Minimal: Only patch what's necessary
- Safe: Don't break other functionality
- Documented: Explain why each patch exists
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Store original sys.argv BEFORE any imports can modify it
_original_argv = sys.argv.copy()


def protect_argv() -> bool:
    """
    Protect sys.argv from being corrupted by subprocess calls.

    spaCy's weasel library runs pip commands that corrupt sys.argv,
    causing argparse to see pip arguments instead of user arguments.

    This patch:
    1. Blocks pip install commands from running (they fail in frozen envs anyway)
    2. Restores sys.argv after any subprocess call

    Returns:
        True if patch was applied
    """
    global _original_argv
    _original_run = subprocess.run

    def _patched_run(*args, **kwargs):
        global _original_argv

        # Block pip install commands from spaCy/weasel
        if args and len(args) > 0:
            cmd = args[0] if isinstance(args[0], list) else str(args[0])
            cmd_str = str(cmd).lower()

            # Block pip install attempts
            if 'pip' in cmd_str and 'install' in cmd_str:
                # Return fake successful result
                class FakeResult:
                    returncode = 0
                    stdout = b''
                    stderr = b''
                return FakeResult()

        # Run the actual command
        result = _original_run(*args, **kwargs)

        # Restore argv after subprocess (some libs corrupt it)
        sys.argv = _original_argv

        return result

    subprocess.run = _patched_run
    return True


def configure_espeak() -> bool:
    """
    Configure espeak-ng library paths for non-English phonemization.

    The phonemizer library needs to find the espeak-ng DLL and data files.
    In a PyInstaller bundle, these are in a different location than
    where phonemizer looks by default.

    Returns:
        True if espeak was configured, False otherwise
    """
    try:
        # Determine base path (PyInstaller bundle or development)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent

        # Try to use espeakng_loader if available
        try:
            import espeakng_loader
            dll_path = espeakng_loader.get_library_path()
            data_path = espeakng_loader.get_data_path()

            # In frozen exe, check for bundled paths
            if getattr(sys, 'frozen', False):
                frozen_dll = base_path / 'espeakng_loader' / 'espeak-ng.dll'
                if frozen_dll.exists():
                    dll_path = str(frozen_dll)

                frozen_data = base_path / 'espeakng_loader' / 'espeak-ng-data'
                if frozen_data.exists():
                    data_path = str(frozen_data)

            os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = dll_path
            os.environ['ESPEAK_DATA_PATH'] = data_path
            return True

        except ImportError:
            # espeakng_loader not available
            return False

    except Exception:
        # Silently fail - American English will still work
        return False


def patch_spacy_load() -> bool:
    """
    Patch spacy.load() to avoid loading en_core_web_sm model.

    The misaki (g2p) library tries to load spaCy's en_core_web_sm model
    for tokenization, but it doesn't actually need the full NLP pipeline.
    We provide a minimal fake model that satisfies the tokenization needs.

    This avoids:
    - Downloading 11MB+ model files
    - spaCy's pip install attempts in frozen environments
    - Import errors when the model isn't installed

    Returns:
        True if patch was applied, False otherwise
    """
    try:
        import spacy
        _original_load = spacy.load

        def _patched_load(name, **kwargs):
            """Intercept spacy.load() calls for en_core_web_sm."""
            if 'en_core_web_sm' in str(name):
                return _create_minimal_tokenizer()
            return _original_load(name, **kwargs)

        spacy.load = _patched_load
        return True

    except ImportError:
        # spaCy not installed
        return False
    except Exception:
        return False


def _create_minimal_tokenizer():
    """
    Create a minimal spaCy-compatible tokenizer.

    This provides just enough functionality for misaki's g2p pipeline
    without loading the full en_core_web_sm model.
    """
    class MinimalToken:
        """Minimal token that satisfies misaki's requirements."""
        def __init__(self, text: str, has_space: bool = True):
            self.text = text
            self.text_with_ws = text + (" " if has_space else "")
            self.whitespace_ = " " if has_space else ""
            self.tag_ = "NN"
            self.pos_ = "NOUN"
            self.lemma_ = text.lower()

    class MinimalTokenizer:
        """Simple whitespace tokenizer."""
        def __call__(self, text: str):
            words = text.split()
            tokens = []
            for i, word in enumerate(words):
                has_space = i < len(words) - 1
                tokens.append(MinimalToken(word, has_space))
            return tokens

    class MinimalModel:
        """Minimal spaCy model compatible with misaki."""
        def __init__(self):
            self.tokenizer = MinimalTokenizer()

        def __call__(self, text: str):
            return self.tokenizer(text)

    return MinimalModel()


def suppress_spacy_warnings():
    """Suppress non-critical spaCy warnings."""
    os.environ['SPACY_WARNING_IGNORE'] = 'W007,W008'


def apply_all_patches() -> dict:
    """
    Apply all necessary patches for frozen environment compatibility.

    Call this early in the application startup, before importing kokoro.

    Returns:
        Dict with patch names and their success status
    """
    results = {}

    # CRITICAL: Protect sys.argv first (before any imports)
    results['argv_protection'] = protect_argv()

    # Suppress warnings
    suppress_spacy_warnings()
    results['spacy_warnings'] = True

    # Configure espeak (needed before importing phonemizer)
    results['espeak'] = configure_espeak()

    # Patch spaCy load
    results['spacy_load'] = patch_spacy_load()

    return results
