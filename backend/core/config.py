"""
backend/core/config.py
Owner: Arzaan
Purpose: Load config.yaml and expose a typed Config object.
         Every backend module imports from here.
         Also re-exports Jayed's pipeline CONFIG dict for backward compatibility
         with data/, features/ modules that do: from config import CONFIG
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_config_file() -> Path:
    """Search for config.yaml walking up from this file's location."""
    # Walk up: backend/core/ → backend/ → project root (SIH2026/)
    candidates = [
        Path(__file__).parent.parent.parent / "config.yaml",  # SIH2026/config.yaml
        Path(__file__).parent.parent / "config.yaml",
        Path(os.getcwd()) / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        "config.yaml not found. Expected at d:/projects/SIH2026/config.yaml. "
        f"Searched: {[str(c) for c in candidates]}"
    )


# ---------------------------------------------------------------------------
# Typed sub-configs
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    name: str = "Q-Diagnose"
    version: str = "1.0.0"
    debug: bool = False


@dataclass
class StorageConfig:
    backend: str = "local"
    base_path: str = "."
    max_file_size_mb: int = 50
    max_uncompressed_size_gb: int = 2
    supported_formats: List[str] = field(default_factory=lambda: [".csv", ".xlsx", ".zip"])
    uploads_dir: str = "data/uploads"
    demo_dir: str = "data/demo"


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///./mvp.db"


@dataclass
class ExperimentConfig:
    test_size: float = 0.20
    random_state: int = 42
    n_components: int = 8
    candidate_dimensions: List[int] = field(default_factory=lambda: [8])
    cv_folds: int = 5


@dataclass
class QuantumConfig:
    backend_type: str = "LOCAL_SIMULATOR"
    backend_name: str = "qasm_simulator"
    provider: str = "qiskit_aer"
    shots: int = 1024
    seed_simulator: int = 42
    seed_transpiler: int = 42
    optimization_level: int = 1
    qubits: int = 8
    circuit_depth: int = 2
    ansatz: str = "RealAmplitudes"
    entanglement: str = "linear"
    reps: int = 2
    optimizer: str = "COBYLA"
    max_iterations: int = 200
    encoding_type: str = "ANGLE_ENCODING"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


# ---------------------------------------------------------------------------
# Root Config
# ---------------------------------------------------------------------------

@dataclass
class Config:
    """
    Typed configuration object. Import and use as:
        from backend.core.config import config
        config.storage.base_path
    """
    app: AppConfig = field(default_factory=AppConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)
    quantum_config: QuantumConfig = field(default_factory=QuantumConfig)
    classical_models: Dict[str, Any] = field(default_factory=dict)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    _config_path: Optional[str] = field(default=None, repr=False, compare=False)

    @property
    def project_root(self) -> Path:
        """Absolute path to the project root (directory containing config.yaml)."""
        if self._config_path:
            return Path(self._config_path).parent
        return Path(os.getcwd())

    @property
    def storage_base_path(self) -> Path:
        """Resolved absolute base path for all storage operations."""
        raw = self.storage.base_path
        p = Path(raw)
        if not p.is_absolute():
            p = self.project_root / p
        return p.resolve()

    @property
    def uploads_path(self) -> Path:
        return (self.storage_base_path / self.storage.uploads_dir).resolve()

    @property
    def demo_path(self) -> Path:
        return (self.storage_base_path / self.storage.demo_dir).resolve()

    @property
    def artifacts_path(self) -> Path:
        return (self.storage_base_path / "artifacts").resolve()

    def get_max_file_size_bytes(self) -> int:
        return self.storage.max_file_size_mb * 1024 * 1024


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _build_config(raw: Dict[str, Any], config_path: str) -> Config:
    def _get(d: dict, key: str, default: Any = None) -> Any:
        return d.get(key, default) or default

    app_raw  = _get(raw, "app", {})
    stor_raw = _get(raw, "storage", {})
    db_raw   = _get(raw, "database", {})
    exp_raw  = _get(raw, "experiment", {})
    q_raw    = _get(raw, "quantum_config", {})
    log_raw  = _get(raw, "logging", {})

    return Config(
        app=AppConfig(
            name=_get(app_raw, "name", "Q-Diagnose"),
            version=_get(app_raw, "version", "1.0.0"),
            debug=bool(_get(app_raw, "debug", False)),
        ),
        storage=StorageConfig(
            backend=_get(stor_raw, "backend", "local"),
            base_path=_get(stor_raw, "base_path", "."),
            max_file_size_mb=int(_get(stor_raw, "max_file_size_mb", 50)),
            max_uncompressed_size_gb=int(_get(stor_raw, "max_uncompressed_size_gb", 2)),
            supported_formats=list(_get(stor_raw, "supported_formats", [".csv", ".xlsx", ".zip"])),
            uploads_dir=_get(stor_raw, "uploads_dir", "data/uploads"),
            demo_dir=_get(stor_raw, "demo_dir", "data/demo"),
        ),
        database=DatabaseConfig(
            url=_get(db_raw, "url", "sqlite:///./mvp.db"),
        ),
        experiment=ExperimentConfig(
            test_size=float(_get(exp_raw, "test_size", 0.20)),
            random_state=int(_get(exp_raw, "random_state", 42)),
            n_components=int(_get(exp_raw, "n_components", 8)),
            candidate_dimensions=list(_get(exp_raw, "candidate_dimensions", [8])),
            cv_folds=int(_get(exp_raw, "cv_folds", 5)),
        ),
        quantum_config=QuantumConfig(
            backend_type=_get(q_raw, "backend_type", "LOCAL_SIMULATOR"),
            backend_name=_get(q_raw, "backend_name", "qasm_simulator"),
            provider=_get(q_raw, "provider", "qiskit_aer"),
            shots=int(_get(q_raw, "shots", 1024)),
            seed_simulator=int(_get(q_raw, "seed_simulator", 42)),
            seed_transpiler=int(_get(q_raw, "seed_transpiler", 42)),
            optimization_level=int(_get(q_raw, "optimization_level", 1)),
            qubits=int(_get(q_raw, "qubits", 8)),
            circuit_depth=int(_get(q_raw, "circuit_depth", 2)),
            ansatz=_get(q_raw, "ansatz", "RealAmplitudes"),
            entanglement=_get(q_raw, "entanglement", "linear"),
            reps=int(_get(q_raw, "reps", 2)),
            optimizer=_get(q_raw, "optimizer", "COBYLA"),
            max_iterations=int(_get(q_raw, "max_iterations", 200)),
            encoding_type=_get(q_raw, "encoding_type", "ANGLE_ENCODING"),
        ),
        classical_models=_get(raw, "classical_models", {}),
        logging=LoggingConfig(
            level=_get(log_raw, "level", "INFO"),
            format=_get(log_raw, "format", "%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
        ),
        _config_path=config_path,
    )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load and return a Config object from config.yaml."""
    path = Path(config_path) if config_path else _find_config_file()
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _build_config(raw, str(path))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

config: Config = load_config()
