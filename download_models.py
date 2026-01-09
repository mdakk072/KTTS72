"""Download Kokoro models and voices"""
from huggingface_hub import hf_hub_download
from pathlib import Path

repo = 'hexgrad/Kokoro-82M'

# Download base model
print('[1/3] Downloading base model files...')
base_dir = Path('models/kokoro-82m')
base_dir.mkdir(parents=True, exist_ok=True)

for f in ['config.json', 'kokoro-v1_0.pth']:
    print(f'  Downloading {f}...')
    hf_hub_download(repo, f, local_dir=base_dir, local_dir_use_symlinks=False)
    print(f'  OK {f}')

# Download all 41 voices
print('\n[2/3] Downloading voice files (41 total)...')
voices_dir = Path('models')
voices_dir.mkdir(exist_ok=True)

voices = ['af_alloy','af_aoede','af_bella','af_heart','af_jessica','af_kore','af_nicole','af_nova','af_river','af_sarah','af_sky','am_adam','am_echo','am_eric','am_fenrir','am_liam','am_michael','am_onyx','am_puck','am_santa','bf_alice','bf_emma','bf_isabella','bf_lily','bm_daniel','bm_fable','bm_george','bm_lewis','ef_dora','em_alex','em_santa','ff_siwis','hf_alpha','hf_beta','hm_omega','hm_psi','if_sara','im_nicola','pf_dora','pm_alex','pm_santa']

for i, v in enumerate(voices):
    print(f'  [{i+1}/41] {v}.pt')
    hf_hub_download(repo, f'voices/{v}.pt', local_dir=voices_dir, local_dir_use_symlinks=False)

print('\n[3/3] Verifying downloads...')
if Path('models/voices/af_alloy.pt').exists():
    print('[OK] All models downloaded successfully')
else:
    print('[ERROR] Voice files not found')
    exit(1)
