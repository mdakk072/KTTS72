# -*- mode: python ; coding: utf-8 -*-
"""
Simple PyInstaller spec for Kokoro Announce.
Bundles all required data files for standalone execution.
"""

import os
from pathlib import Path

block_cipher = None
project_root = Path.cwd()


# Collect model files
def collect_models():
    """Collect all model files to bundle."""
    datas = []

    models_dir = project_root / 'models'
    if not models_dir.exists():
        print("WARNING: models directory not found!")
        return datas

    # Recursively add all files from models/ preserving full structure
    for root, dirs, files in os.walk(models_dir):
        for file in files:
            src = Path(root) / file
            # Preserve the full path relative to project root
            # e.g., models/kokoro-82m/config.json -> models/kokoro-82m
            rel_path = src.relative_to(project_root)
            dest = str(rel_path.parent)
            datas.append((str(src), dest))

    print(f"Collected {len(datas)} model files")
    return datas


# Collect package data files
def collect_package_data():
    """Collect data files from installed packages."""
    datas = []

    # language_tags data
    try:
        import language_tags
        pkg_path = Path(language_tags.__file__).parent
        data_dir = pkg_path / "data"
        if data_dir.exists():
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    src = Path(root) / file
                    rel = src.relative_to(pkg_path.parent)
                    dest = str(rel.parent)
                    datas.append((str(src), dest))
            print(f"Collected language_tags data files")
    except ImportError:
        print("WARNING: language_tags not found")

    # espeakng_loader data
    try:
        import espeakng_loader
        pkg_path = Path(espeakng_loader.__file__).parent
        data_dir = pkg_path / "espeak-ng-data"
        if data_dir.exists():
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    src = Path(root) / file
                    rel = src.relative_to(pkg_path.parent)
                    dest = str(rel.parent)
                    datas.append((str(src), dest))
            print(f"Collected espeakng_loader data files")
    except ImportError:
        print("WARNING: espeakng_loader not found")

    # spaCy lang data (needed for tokenization)
    try:
        import spacy
        pkg_path = Path(spacy.__file__).parent
        lang_dir = pkg_path / "lang"
        if lang_dir.exists():
            datas.append((str(lang_dir), "spacy/lang"))
            print(f"Collected spaCy lang data")
    except ImportError:
        print("WARNING: spaCy not found")

    # misaki data files (g2p data)
    try:
        import misaki
        pkg_path = Path(misaki.__file__).parent
        data_dir = pkg_path / "data"
        if data_dir.exists():
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    src = Path(root) / file
                    rel = src.relative_to(pkg_path.parent)
                    dest = str(rel.parent)
                    datas.append((str(src), dest))
            print(f"Collected misaki data files")
    except ImportError:
        print("WARNING: misaki not found")

    return datas


# Collect espeak binaries
def collect_espeak_binaries():
    """Collect espeak-ng DLL for non-English phonemization."""
    binaries = []

    try:
        import espeakng_loader
        dll_path = espeakng_loader.get_library_path()
        if Path(dll_path).exists():
            # Bundle as espeakng_loader/espeak-ng.dll to preserve package structure
            binaries.append((dll_path, 'espeakng_loader'))
            print(f"Collected espeak-ng.dll from {dll_path}")
    except ImportError:
        print("WARNING: espeakng_loader not found, non-English languages may not work")

    return binaries


# Collect all data
all_datas = collect_models() + collect_package_data()
all_binaries = collect_espeak_binaries()

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=[
        'kokoro',
        'kokoro.model',
        'kokoro.pipeline',
        'kokoro.modules',
        'kokoro_announce',
        'kokoro_announce.announcer',
        'kokoro_announce.pipeline',
        'kokoro_announce.config',
        'kokoro_announce.local_models',
        'kokoro_announce.validation',
        'kokoro_announce.audio',
        'kokoro_announce.patches',
        'kokoro_announce.cli',
        'soundfile',
        'numpy',
        'torch',
        'transformers',
        'huggingface_hub',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
        # Exclude spaCy language models only (not spaCy itself)
        'en_core_web_sm',
        'en_core_web_md',
        'en_core_web_lg',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Kokoro72CLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Kokoro72CLI',
)
