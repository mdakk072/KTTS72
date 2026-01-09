# Kokoro72CLI Architecture

This document describes the design decisions and architecture of the Kokoro72CLI application.

## Overview

Kokoro72CLI is a command-line text-to-speech application that wraps the Kokoro-82M neural TTS model for easy offline use. The primary goal is to provide a standalone Windows executable that works completely offline after initial setup.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                               │
│                    (CLI Entry Point)                         │
│  - Applies runtime patches                                   │
│  - Parses arguments                                          │
│  - Handles errors                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    kokoro_announce                           │
│                    (Python Package)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   cli.py     │  │ validation.py│  │  patches.py  │       │
│  │              │  │              │  │              │       │
│  │ - Arg parser │  │ - Path safety│  │ - spaCy mock │       │
│  │ - Voice list │  │ - Speed/rate │  │ - espeak cfg │       │
│  │ - Lang list  │  │ - Text limit │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ announcer.py │  │ pipeline.py  │  │  audio.py    │       │
│  │              │  │              │  │              │       │
│  │ - High-level │  │ - Lazy init  │  │ - WAV output │       │
│  │   TTS API    │  │ - Model load │  │ - MP3 output │       │
│  │              │  │              │  │   (ffmpeg)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  config.py   │  │local_models. │                         │
│  │              │  │    py        │                         │
│  │ - Settings   │  │ - Path resol │                         │
│  │ - Defaults   │  │ - Download   │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      kokoro library                          │
│                  (External Dependency)                       │
│  - KPipeline: Text → Phonemes → Audio                       │
│  - KModel: Neural network inference                          │
│  - Phonemizer: Text to phoneme conversion                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         PyTorch                              │
│                  (Neural Network Runtime)                    │
└─────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Layered Architecture

The application follows a layered design:

1. **CLI Layer** (`app.py`, `cli.py`): User interaction, argument parsing
2. **API Layer** (`announcer.py`): High-level synthesis operations
3. **Pipeline Layer** (`pipeline.py`): Model management and inference
4. **Utility Layer** (`validation.py`, `audio.py`, `patches.py`): Support functions

Each layer only depends on layers below it, making the code easier to understand and modify.

### 2. Lazy Initialization

Model loading is deferred until first use:

```python
class PipelineFactory:
    def get(self):
        if self._pipeline is None:
            self._pipeline = self._create_pipeline()
        return self._pipeline
```

This provides:
- Fast CLI startup (instant `--help`, `--list-voices`)
- Single model instance reused across calls
- Memory efficiency for short sessions

### 3. Offline-First Design

The application is designed to work completely offline:

- Models are bundled with the executable via PyInstaller
- Voice files are resolved from bundled paths first
- HuggingFace download only used as fallback
- espeak-ng DLL bundled for non-English phonemization

### 4. Security by Default

Input validation is mandatory:

- **Path validation**: All file paths checked against safe directories
- **Parameter validation**: Speed, sample rate, device strings validated
- **Text limits**: Maximum text length enforced to prevent DoS
- **Model safety**: Only bundled/verified models used

## Key Design Decisions

### Why Monkey-Patching?

The `patches.py` module contains runtime patches for third-party libraries. This is not ideal, but necessary because:

1. **spaCy Model Loading**: The `misaki` (G2P) library tries to load `en_core_web_sm`, but only needs basic tokenization. Loading the full model adds 11MB+ and requires internet.

2. **espeak Path Configuration**: The `phonemizer` library needs espeak paths configured before import. In a PyInstaller bundle, these paths are different.

The patches are:
- Minimal (only patch what's necessary)
- Isolated in a single module
- Applied once at startup
- Documented with rationale

### Why Not Use `weights_only=True`?

The Kokoro library internally uses `torch.load()` for model loading. We cannot modify this without forking the library. Our mitigation:

- Only use bundled/verified models from hexgrad/Kokoro-82M
- Document the security consideration
- Validate model paths before loading

### Why PyInstaller?

PyInstaller was chosen for Windows distribution because:

- Creates single-folder distribution
- Bundles Python runtime, dependencies, and data files
- Handles native extensions (torch, soundfile)
- Mature and well-documented

Alternatives considered:
- **Nuitka**: Better performance but more complex setup
- **cx_Freeze**: Less reliable with large dependencies
- **Docker**: Not suitable for end-user Windows distribution

## Module Responsibilities

### app.py
- Single entry point for the application
- Applies runtime patches before other imports
- Delegates to cli.py for argument handling
- Top-level error handling and exit codes

### cli.py
- Argument parser configuration
- Voice and language listing
- Argument validation orchestration
- User-facing output formatting

### validation.py
- Input validation functions
- Path safety checking
- Parameter bounds enforcement
- Consistent error messages

### announcer.py
- High-level TTS API (`KokoroAnnouncer`)
- Voice resolution (name → path)
- Audio concatenation for long texts
- File output coordination

### pipeline.py
- Lazy pipeline initialization
- Local vs remote model handling
- Device management (CPU/GPU)
- Model caching

### audio.py
- WAV output (native via soundfile)
- MP3 output (via ffmpeg subprocess)
- Format detection from file extension
- Audio format abstraction

### patches.py
- spaCy mock model for tokenization
- espeak path configuration
- Warning suppression
- Centralized patching logic

### config.py
- Settings dataclass
- Default values
- Type definitions

### local_models.py
- Model directory resolution
- PyInstaller path handling
- Model downloading fallback
- Model existence checking

## Data Flow

### Synthesis Flow

```
User Input (text, voice, speed)
        │
        ▼
    validate_args()     ← Validate all inputs
        │
        ▼
    KokoroSettings      ← Configuration object
        │
        ▼
    KokoroAnnouncer     ← High-level API
        │
        ▼
    PipelineFactory.get() ← Lazy load model
        │
        ▼
    KPipeline(text)     ← Kokoro inference
        │
        ▼
    numpy.ndarray       ← Raw audio data
        │
        ▼
    write_audio()       ← WAV or MP3 output
        │
        ▼
    Output file
```

### Model Resolution Flow

```
Voice name (e.g., "af_heart")
        │
        ▼
    Check local models exist?
        │
    ┌───┴───┐
    │       │
   Yes      No
    │       │
    ▼       ▼
models/   Download from
voices/   HuggingFace
af_heart.pt
    │
    ▼
  Return path
```

## Extension Points

### Adding New Output Formats

1. Add format to `VALID_OUTPUT_FORMATS` in `validation.py`
2. Implement `write_xxx()` function in `audio.py`
3. Update `write_audio()` dispatcher
4. Document in README

### Adding New Languages

Languages are primarily handled by the Kokoro library. To add:

1. Ensure phonemizer supports the language
2. Add language code to `LANGUAGES` dict in `cli.py`
3. Add voice files to `models/voices/`
4. Update README voice reference

### Adding New Validation Rules

1. Add validation function in `validation.py`
2. Add constants for bounds/valid values
3. Call from `validate_args()` in `cli.py`
4. Update help text with new constraints

## Build System

### PyInstaller Configuration

The `app.spec` file configures:

- **Hidden imports**: Modules not detected by analysis
- **Data files**: Models, espeak data, language files
- **Binaries**: espeak-ng.dll
- **Excludes**: Unnecessary packages (matplotlib, jupyter, etc.)

### Build Process

```
setup_env.bat
    │
    ├─► Create venv
    ├─► Install requirements
    └─► Download models
          │
          ▼
      build.bat
          │
          ├─► Clean previous build
          ├─► Run PyInstaller
          └─► Test executable
                │
                ▼
          dist/Kokoro72CLI/
                │
                ├─► Kokoro72CLI.exe
                └─► _internal/
                        │
                        ├─► models/
                        ├─► torch/
                        └─► ...
```

## Performance Considerations

### Model Loading Time

First synthesis takes 5-15 seconds for model loading. Mitigations:
- Lazy loading (fast startup for `--help`)
- Model caching (subsequent calls fast)
- Consider warming in future versions

### Memory Usage

Peak memory ~2-3GB during inference. Recommendations:
- Use CPU for low-memory systems
- Process text in chunks for very long documents
- Close other applications if needed

### Disk Space

Distribution size ~1.5GB. Breakdown:
- PyTorch: ~500MB
- Model weights: ~308MB
- Voices: ~21MB
- Python + deps: ~600MB
