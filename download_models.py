"""Download Kokoro models and voices for supported languages."""
from huggingface_hub import hf_hub_download
from pathlib import Path

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

def main():
    voices = list(VOICES.keys())
    total = len(voices)

    # Download base model
    print('[1/3] Downloading base model files...')
    base_dir = Path('models/kokoro-82m')
    base_dir.mkdir(parents=True, exist_ok=True)

    for f in ['config.json', 'kokoro-v1_0.pth']:
        print(f'  Downloading {f}...')
        hf_hub_download(repo, f, local_dir=base_dir, local_dir_use_symlinks=False)
        print(f'  OK {f}')

    # Download voices
    print(f'\n[2/3] Downloading voice files ({total} total)...')
    voices_dir = Path('models')
    voices_dir.mkdir(exist_ok=True)

    for i, v in enumerate(voices):
        print(f'  [{i+1}/{total}] {v}.pt')
        hf_hub_download(repo, f'voices/{v}.pt', local_dir=voices_dir, local_dir_use_symlinks=False)

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
