"""
Pipeline factory for Kokoro TTS.

Handles lazy initialization of the Kokoro pipeline with support for
local bundled models and HuggingFace downloads.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

from .config import KokoroSettings
from .local_models import get_model_paths, models_exist, download_models

# Suppress known harmless warnings
warnings.filterwarnings('ignore', message='dropout option adds dropout after all but last recurrent layer')
warnings.filterwarnings('ignore', message='.*torch.nn.utils.weight_norm.*is deprecated.*')


class PipelineFactory:
    """
    Lazy creator for kokoro.KPipeline.

    Maintains a single pipeline instance for reuse, only initializing
    on first use to reduce startup time.

    The pipeline uses local bundled models when available for fully
    offline operation. Falls back to HuggingFace download if needed.
    """

    def __init__(self, settings: KokoroSettings) -> None:
        """
        Initialize the factory.

        Args:
            settings: Configuration for the pipeline
        """
        self.settings = settings
        self._pipeline = None

    def get(self):
        """
        Get or create the Kokoro pipeline.

        On first call, initializes the pipeline using local models if
        available, otherwise downloads from HuggingFace.

        Returns:
            Configured KPipeline instance
        """
        if self._pipeline is None:
            self._pipeline = self._create_pipeline()
        return self._pipeline

    def _create_pipeline(self):
        """
        Create a new pipeline instance.

        Security note: The kokoro library uses torch.load() internally
        for loading model weights. We use only bundled/verified models
        from known sources (hexgrad/Kokoro-82M on HuggingFace).
        """
        # Import lazily to avoid slow startup
        from kokoro import KPipeline, KModel

        # Check for local bundled models
        use_local = models_exist()

        if not use_local:
            # Try to download models
            if download_models():
                use_local = True

        if use_local:
            return self._create_local_pipeline(KPipeline, KModel)
        else:
            return self._create_remote_pipeline(KPipeline)

    def _create_local_pipeline(self, KPipeline, KModel):
        """
        Create pipeline using local bundled models.

        This enables fully offline operation.
        """
        model_paths = get_model_paths()

        # Verify model files exist
        config_path = Path(model_paths['config'])
        model_path = Path(model_paths['model'])

        if not config_path.exists():
            raise FileNotFoundError(f"Model config not found: {config_path}")
        if not model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {model_path}")

        # Create model with local files
        # Note: KModel internally uses torch.load - we trust bundled models
        model = KModel(
            repo_id='hexgrad/Kokoro-82M',
            config=model_paths['config'],
            model=model_paths['model'],
        )

        # Move to device if specified
        if self.settings.device:
            model = model.to(self.settings.device)
        model = model.eval()

        return KPipeline(
            lang_code=self.settings.lang_code,
            repo_id='hexgrad/Kokoro-82M',
            model=model,
        )

    def _create_remote_pipeline(self, KPipeline):
        """
        Create pipeline using HuggingFace remote models.

        Falls back to this when local models aren't available.
        """
        return KPipeline(
            lang_code=self.settings.lang_code,
            device=self.settings.device,
            repo_id='hexgrad/Kokoro-82M',
        )

    def reset(self) -> None:
        """
        Dispose of the cached pipeline.

        Call this to reload the model, e.g., when changing devices.
        """
        self._pipeline = None
