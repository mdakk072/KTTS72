"""
Local model path resolver.

This module handles loading models from local bundled files instead of
downloading from HuggingFace. Works with both development and PyInstaller builds.
Automatically downloads models if they don't exist locally.
"""

from pathlib import Path
import sys
import os
import ssl
import urllib3

# Handle SSL issues in corporate environments
try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
except Exception:
    pass  # Continue with default SSL settings

def get_models_dir() -> Path:
    """
    Get the models directory path.

    Works in both development and PyInstaller frozen builds.

    Returns:
        Path to the models directory
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        # _MEIPASS is the temp folder where PyInstaller extracts files
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python
        # Go up from kokoro_announce/ to project root
        base_path = Path(__file__).parent.parent

    return base_path / 'models'

def get_model_paths() -> dict:
    """
    Get paths to all bundled model files.

    Returns:
        Dict with keys: 'config', 'model', 'voice_dir'
    """
    models_dir = get_models_dir()
    kokoro_dir = models_dir / 'kokoro-82m'
    voices_dir = models_dir / 'voices'

    return {
        'config': str(kokoro_dir / 'config.json'),
        'model': str(kokoro_dir / 'kokoro-v1_0.pth'),
        'voice_dir': str(voices_dir),
        'models_dir': str(models_dir),
    }

def get_voice_path(voice_name: str) -> str:
    """
    Get path to a voice file.

    Args:
        voice_name: Name of the voice (e.g., 'af_heart')

    Returns:
        Path to the voice file
    """
    paths = get_model_paths()
    voice_dir = Path(paths['voice_dir'])

    # Add .pt extension if not present
    if not voice_name.endswith('.pt'):
        voice_name = f"{voice_name}.pt"

    return str(voice_dir / voice_name)

def models_exist() -> bool:
    """
    Check if all required model files exist locally.

    Returns:
        True if all models are present, False otherwise
    """
    paths = get_model_paths()

    required_files = [
        paths['config'],
        paths['model'],
        get_voice_path('af_heart'),
    ]

    return all(Path(p).exists() for p in required_files)

def safe_hf_download(repo_id, filename, max_retries=3):
    """Download with SSL bypass and retry logic."""
    import time
    from huggingface_hub import hf_hub_download
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f"    Retry {attempt}/{max_retries - 1}...")
                time.sleep(2)
                
            return hf_hub_download(
                repo_id=repo_id, 
                filename=filename,
                headers={'User-Agent': 'KTTS72/1.1.0'}
            )
            
        except Exception as e:
            if "SSL" in str(e) or "CERTIFICATE" in str(e):
                print(f"    SSL error (attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    print("\n[ERROR] SSL Certificate verification failed.")
                    print("Please run download_models.py to get detailed SSL help.")
                    raise e
            else:
                if attempt == max_retries - 1:
                    raise e
        time.sleep(1)
    return None


def download_models() -> bool:
    """
    Download models to local directory if they don't exist.

    Returns:
        True if models are ready (already existed or downloaded successfully)
    """
    if models_exist():
        return True

    try:
        import shutil

        print("[SETUP] Downloading models to local directory...")
        print("This will download ~313 MB of model files...")

        models_dir = get_models_dir()
        kokoro_dir = models_dir / 'kokoro-82m'
        voices_dir = models_dir / 'voices'

        # Create directories
        kokoro_dir.mkdir(parents=True, exist_ok=True)
        voices_dir.mkdir(parents=True, exist_ok=True)

        repo_id = 'hexgrad/Kokoro-82M'
        files_to_download = [
            ('config.json', kokoro_dir),
            ('kokoro-v1_0.pth', kokoro_dir),
            ('voices/af_heart.pt', voices_dir),
        ]

        for filename, dest_dir in files_to_download:
            print(f"Downloading {filename}...")
            cached_path = safe_hf_download(repo_id, filename)
            local_filename = Path(filename).name
            dest_path = dest_dir / local_filename
            shutil.copy2(cached_path, dest_path)
            print(f"  Saved to {dest_path}")

        print("[OK] Models downloaded successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to download models: {e}")
        return False

def get_model_info() -> dict:
    """
    Get information about bundled models.

    Returns:
        Dict with model file information
    """
    paths = get_model_paths()
    info = {}

    for name, path in paths.items():
        if name == 'models_dir':
            continue

        if name == 'voice_dir':
            # List all voices
            voice_dir = Path(path)
            if voice_dir.exists():
                voices = [f.stem for f in voice_dir.glob('*.pt')]
                info['available_voices'] = voices
        else:
            filepath = Path(path)
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                info[name] = {
                    'path': str(filepath),
                    'size_mb': round(size_mb, 2),
                    'exists': True,
                }
            else:
                info[name] = {
                    'path': str(filepath),
                    'exists': False,
                }

    return info
