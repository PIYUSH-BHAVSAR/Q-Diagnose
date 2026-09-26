# core/config.py
# Central configuration for the Q-Diagnose Dataset API.
# All limits, paths, and settings live here — never hardcode them in routes.

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class StorageConfig:
    """Where datasets are stored on disk."""
    backend: str = "local"                          # "local" | "s3" | "minio"
    base_path: str = "./datasets"                   # root folder for all raw files


@dataclass
class UploadConfig:
    """Limits on what the upload endpoint accepts."""
    max_file_size_mb: int = 500                     # hard cap per upload
    supported_formats: List[str] = field(
        default_factory=lambda: ["csv", "xlsx", "zip"]
    )


@dataclass
class ArchiveConfig:
    """Safety limits specifically for ZIP uploads."""
    max_entries: int = 100_000                      # max files inside the archive
    max_uncompressed_size_gb: float = 10.0          # GB, prevents zip-bombs


@dataclass
class DatabaseConfig:
    """
    For standalone/MVP development we use a simple JSON file as the registry.
    When Arzaan's real DB layer is ready, swap this for a proper SQLAlchemy URL.
    """
    use_json_registry: bool = True
    registry_path: str = "./datasets/registry.json"


@dataclass
class AppConfig:
    """Top-level config object — import `config` from this module."""
    app_name: str = "Q-Diagnose Dataset API"
    version: str = "1.0.0"
    environment: str = "development"               # "development" | "production"
    debug: bool = True
    allowed_origins: List[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",   # Naeem's Vite dev server
            "http://localhost:3000",   # fallback React dev server
        ]
    )
    storage: StorageConfig = field(default_factory=StorageConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Convenience shortcuts used throughout the app
    @property
    def storage_base_path(self) -> str:
        return self.storage.base_path

    @property
    def max_file_size_mb(self) -> int:
        return self.upload.max_file_size_mb

    @property
    def supported_formats(self) -> List[str]:
        return self.upload.supported_formats


# ── Environment overrides ────────────────────────────────────────────────────
# Pull from env vars when present so CI/CD can override without editing code.
def _build_config() -> AppConfig:
    cfg = AppConfig()
    cfg.storage.base_path       = os.getenv("STORAGE_BASE_PATH", cfg.storage.base_path)
    cfg.upload.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", cfg.upload.max_file_size_mb))
    cfg.environment             = os.getenv("APP_ENV", cfg.environment)
    cfg.database.registry_path  = os.getenv("REGISTRY_PATH", cfg.database.registry_path)
    return cfg


# Single shared instance — import this everywhere:
#   from core.config import config
config: AppConfig = _build_config()
