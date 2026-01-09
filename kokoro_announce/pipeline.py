from __future__ import annotations

import warnings
from typing import Optional
from pathlib import Path

from .config import KokoroSettings
from .local_models import get_model_paths, models_exist, download_models

# Suppress known warnings
warnings.filterwarnings('ignore', message='dropout option adds dropout after all but last recurrent layer')
warnings.filterwarnings('ignore', message='.*torch.nn.utils.weight_norm.*is deprecated.*')


class PipelineFactory:
    """
    Lazy creator for kokoro.KPipeline. Keeps a single instance alive for reuse.
    """

    def __init__(self, settings: KokoroSettings) -> None:
        self.settings = settings
        self._pipeline = None

    def get(self):
        """
        Instantiate kokoro.KPipeline on first use and return it thereafter.
        Uses local bundled models if available, otherwise downloads from HuggingFace.
        """
        if self._pipeline is None:
            # Import lazily so importing this library does not require kokoro
            # until you actually synthesize.
            from kokoro import KPipeline, KModel

            # Check if we have local bundled models, download if needed
            use_local = models_exist()

            if not use_local:
                # Try to download models
                if download_models():
                    use_local = True

            if use_local:
                # Use local bundled models
                model_paths = get_model_paths()
                model = KModel(
                    repo_id='hexgrad/Kokoro-82M',
                    config=model_paths['config'],
                    model=model_paths['model'],
                )

                # Move model to device if specified
                if self.settings.device:
                    model = model.to(self.settings.device)
                model = model.eval()

                self._pipeline = KPipeline(
                    lang_code=self.settings.lang_code,
                    repo_id='hexgrad/Kokoro-82M',
                    model=model,
                )
            else:
                # Fall back to downloading from HuggingFace
                self._pipeline = KPipeline(
                    lang_code=self.settings.lang_code,
                    device=self.settings.device,
                    repo_id='hexgrad/Kokoro-82M',
                )
        return self._pipeline

    def reset(self) -> None:
        """Dispose of the cached pipeline (e.g., to reload on a new device)."""
        self._pipeline = None

