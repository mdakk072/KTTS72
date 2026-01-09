# Kokoro72CLI

![Windows](https://img.shields.io/badge/Windows-0078D4?style=flat&logo=microsoft&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat)

High-quality offline text-to-speech application powered by the [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) neural TTS model. Convert text to natural-sounding speech in 32 voices across English, Spanish, and French - completely offline after setup.

## Features

- **32 pre-trained voices** across 4 languages
- **Fully offline** - works without internet after initial setup
- **Multiple output formats** - WAV (native) and MP3 (with ffmpeg)
- **Adjustable parameters** - speed, sample rate, voice selection
- **Standalone Windows executable** - no Python installation required

## Supported Languages

| Code | Language | Voices |
|------|----------|--------|
| `a` | American English | 20 (af_*, am_*) |
| `b` | British English | 8 (bf_*, bm_*) |
| `e` | European Spanish | 3 (ef_*, em_*) |
| `f` | French | 1 (ff_*) |

## Installation

### Build from Source

Requirements:
- Windows 10/11
- Python 3.10+
- ~1.2GB disk space for models

```batch
:: Clone the repository
git clone https://github.com/your-username/kokoro72cli.git
cd kokoro72cli

:: Run setup (creates venv, installs deps, downloads models)
setup_env.bat

:: Build the executable
build.bat
```

The executable will be in `dist\Kokoro72CLI.exe` (one-file) or `dist\Kokoro72CLI\` (one-directory).

## Usage

### Basic Examples

```batch
:: Simple text-to-speech
Kokoro72CLI.exe --text "Hello world" --out hello.wav

:: Read from file
Kokoro72CLI.exe --text-file script.txt --out speech.wav

:: Change voice
Kokoro72CLI.exe --text "Hello" --voice am_adam --out hello.wav

:: Adjust speed (0.25 to 4.0)
Kokoro72CLI.exe --text "Fast speech" --speed 1.5 --out fast.wav

:: Output as MP3 (requires ffmpeg in PATH)
Kokoro72CLI.exe --text "Hello" --out hello.mp3

:: French voice
Kokoro72CLI.exe --text "Bonjour le monde" --lang f --voice ff_siwis --out french.wav
```

### List Available Options

```batch
:: List all voices
Kokoro72CLI.exe --list-voices

:: List all languages
Kokoro72CLI.exe --list-languages

:: Show help
Kokoro72CLI.exe --help
```

### All Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--text` | `-t` | - | Text to synthesize |
| `--text-file` | `-f` | - | Read text from UTF-8 file |
| `--out` | `-o` | output.wav | Output file path |
| `--format` | - | (from extension) | Output format: wav, mp3 |
| `--voice` | `-v` | af_heart | Voice name |
| `--lang` | `-l` | a | Language code |
| `--speed` | `-s` | 1.0 | Playback speed (0.25-4.0) |
| `--sample-rate` | `-r` | 24000 | Sample rate in Hz |
| `--device` | `-d` | auto | PyTorch device: cpu, cuda, mps |
| `--verbose` | - | false | Show detailed output |
| `--list-voices` | - | - | List available voices |
| `--list-languages` | - | - | List available languages |

## Voice Reference

### American English
- Female: `af_heart`, `af_bella`, `af_nicole`, `af_sarah`, `af_sky`, `af_alloy`, `af_aoede`, `af_jessica`, `af_kore`, `af_nova`, `af_river`
- Male: `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`

### British English
- Female: `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`
- Male: `bm_daniel`, `bm_george`, `bm_fable`, `bm_lewis`

### Other Languages
- French: `ff_siwis`
- Spanish: `ef_dora`, `em_alex`, `em_santa`

## MP3 Support

MP3 output requires [ffmpeg](https://ffmpeg.org/) to be installed and available in your PATH.

**Windows Installation:**
1. Download ffmpeg from https://ffmpeg.org/download.html
2. Extract and add the `bin` folder to your system PATH
3. Verify with `ffmpeg -version`

## Build Size

The standalone executable is approximately **1.5 GB** due to:
- PyTorch runtime (~500 MB)
- Kokoro model weights (~308 MB)
- Voice embeddings (~16 MB for 32 voices)
- Python runtime and dependencies

## Python API

You can also use Kokoro72CLI as a Python library:

```python
from kokoro_announce import KokoroAnnouncer, KokoroSettings

# Configure settings
settings = KokoroSettings(
    voice="af_heart",
    lang_code="a",
    speed=1.0,
    sample_rate=24000,
)

# Create announcer
announcer = KokoroAnnouncer(settings)

# Synthesize to file
announcer.synthesize_to_file("Hello world", "output.wav")

# Or get raw audio
audio = announcer.synthesize("Hello world")  # numpy array
```

## Example Script

See [example.py](example.py) for a complete demonstration of using the library to generate multiple audio files:

```python
# Generate 4 different voices with custom parameters
synthesis_tasks = [
    {"text": "Hello, this is American English.", "voice": "af_heart", "lang": "a", "speed": 1.0, "sample_rate": 24000, "filename": "english_american.wav"},
    {"text": "Good afternoon from Britain.", "voice": "bm_lewis", "lang": "b", "speed": 0.9, "sample_rate": 22050, "filename": "english_british.wav"},
    {"text": "Hola, esto es español.", "voice": "ef_dora", "lang": "e", "speed": 1.1, "sample_rate": 24000, "filename": "spanish_test.wav"},
    {"text": "Bonjour, ceci est français.", "voice": "ff_siwis", "lang": "f", "speed": 1.0, "sample_rate": 48000, "filename": "french_test.wav"}
]
```

Run `python example.py` to generate sample audio files in multiple languages.

## Project Structure

```
kokoro_lib/
├── app.py                    # CLI entry point
├── app.spec                  # PyInstaller build config
├── kokoro_announce/          # Python package
│   ├── announcer.py          # High-level TTS API
│   ├── audio.py              # Audio output (WAV/MP3)
│   ├── cli.py                # CLI argument handling
│   ├── config.py             # Settings dataclass
│   ├── local_models.py       # Model path resolution
│   ├── patches.py            # Runtime compatibility patches
│   ├── pipeline.py           # Kokoro pipeline wrapper
│   └── validation.py         # Input validation
├── models/                   # TTS models (downloaded)
│   ├── kokoro-82m/           # Base model
│   └── voices/               # Voice embeddings
├── build.bat                 # Build script
├── setup_env.bat             # Environment setup
└── requirements.txt          # Python dependencies
```

## Troubleshooting

### "Models not found"
Run `setup_env.bat` to download the required models (~1.5 GB).

### Slow first run
The first synthesis takes longer due to model loading. Subsequent runs are faster.

### CUDA out of memory
Use `--device cpu` to force CPU inference for lower memory usage.

### MP3 encoding failed
Ensure ffmpeg is installed and in your PATH. Use WAV as a fallback.

### Invalid speed/sample rate
- Speed must be between 0.25 and 4.0
- Valid sample rates: 8000, 16000, 22050, 24000, 44100, 48000

## Security

This application includes input validation and path security checks:
- File paths are validated to prevent directory traversal
- Text length is limited to prevent memory exhaustion
- Speed and sample rate parameters are validated
- Only bundled/verified models are used

## License

This project uses the Kokoro-82M model from [Hexgrad](https://huggingface.co/hexgrad/Kokoro-82M). Please refer to the model's license for usage terms.

## Acknowledgments

- [Hexgrad](https://huggingface.co/hexgrad) for the Kokoro-82M model
- [StyleTTS2](https://github.com/yl4579/StyleTTS2) architecture
- [espeak-ng](https://github.com/espeak-ng/espeak-ng) for phonemization
