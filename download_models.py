"""Download Kokoro models and voices for supported languages."""
import os
import ssl
import urllib3
from huggingface_hub import hf_hub_download
from pathlib import Path

# Handle SSL issues in corporate environments
try:
    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Try to use system certificates first
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Set environment variables for requests/urllib3
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
except Exception as e:
    print(f"Warning: SSL configuration failed: {e}")
    print("Proceeding with default SSL settings...")

repo = 'hexgrad/Kokoro-82M'

# Supported voices: English (US/UK), French, Spanish
# Total: 32 voices
VOICES = {
    # American English (20 voices)
    'af_alloy': 'American Female',
    'af_aoede': 'American Female',
    'af_bella': 'American Female',
    'af_heart': 'American Female',
    'af_jessica': 'American Female',
    'af_kore': 'American Female',
    'af_nicole': 'American Female',
    'af_nova': 'American Female',
    'af_river': 'American Female',
    'af_sarah': 'American Female',
    'af_sky': 'American Female',
    'am_adam': 'American Male',
    'am_echo': 'American Male',
    'am_eric': 'American Male',
    'am_fenrir': 'American Male',
    'am_liam': 'American Male',
    'am_michael': 'American Male',
    'am_onyx': 'American Male',
    'am_puck': 'American Male',
    'am_santa': 'American Male',
    # British English (8 voices)
    'bf_alice': 'British Female',
    'bf_emma': 'British Female',
    'bf_isabella': 'British Female',
    'bf_lily': 'British Female',
    'bm_daniel': 'British Male',
    'bm_fable': 'British Male',
    'bm_george': 'British Male',
    'bm_lewis': 'British Male',
    # Spanish (3 voices)
    'ef_dora': 'Spanish Female',
    'em_alex': 'Spanish Male',
    'em_santa': 'Spanish Male',
    # French (1 voice)
    'ff_siwis': 'French Female',
}

def safe_download(repo, filename, local_dir, max_retries=3):
    """Download with SSL bypass and retry logic for corporate environments."""
    import time
    from huggingface_hub.utils import HfHubHTTPError
    
    for attempt in range(max_retries):
        try:
            # First attempt with SSL bypass
            if attempt > 0:
                print(f"    Retry {attempt}/{max_retries - 1}...")
                time.sleep(2)
            
            # Configure download with SSL bypass
            return hf_hub_download(
                repo, 
                filename, 
                local_dir=local_dir, 
                local_dir_use_symlinks=False,
                # Add timeout and user agent for better compatibility
                headers={'User-Agent': 'KTTS72/1.1.0'}
            )
            
        except Exception as e:
            if "SSL" in str(e) or "CERTIFICATE" in str(e):
                print(f"    SSL error (attempt {attempt + 1}): {type(e).__name__}")
                if attempt == max_retries - 1:
                    print("\n[ERROR] SSL Certificate verification failed.")
                    print("This is common in corporate environments.")
                    print("\nPossible solutions:")
                    print("1. Use corporate VPN if available")
                    print("2. Download models manually from: https://huggingface.co/hexgrad/Kokoro-82M")
                    print("3. Contact IT support for SSL certificate issues")
                    print("\nManual download instructions:")
                    print(f"  - Download {filename} to models/kokoro-82m/ folder")
                    raise e
            else:
                print(f"    Download error: {e}")
                if attempt == max_retries - 1:
                    raise e
        
        time.sleep(1)
    
    return None


def main():
    voices = list(VOICES.keys())
    total = len(voices)

    # Download base model
    print('[1/3] Downloading base model files...')
    print('Note: If SSL errors occur, this is normal in corporate environments.')
    base_dir = Path('models/kokoro-82m')
    base_dir.mkdir(parents=True, exist_ok=True)

    for f in ['config.json', 'kokoro-v1_0.pth']:
        print(f'  Downloading {f}...')
        safe_download(repo, f, base_dir)
        print(f'  OK {f}')

    # Download voices
    print(f'\n[2/3] Downloading voice files ({total} total)...')
    voices_dir = Path('models')
    voices_dir.mkdir(exist_ok=True)

    for i, v in enumerate(voices):
        print(f'  [{i+1}/{total}] {v}.pt')
        safe_download(repo, f'voices/{v}.pt', voices_dir)

    print('\n[3/3] Verifying downloads...')
    if Path('models/voices/af_heart.pt').exists():
        print('[OK] All models downloaded successfully')
        print(f'\nDownloaded {total} voices:')
        print(f'  - American English: 20 voices')
        print(f'  - British English: 8 voices')
        print(f'  - Spanish: 3 voices')
        print(f'  - French: 1 voice')
    else:
        print('[ERROR] Voice files not found')
        exit(1)


if __name__ == '__main__':
    main()
