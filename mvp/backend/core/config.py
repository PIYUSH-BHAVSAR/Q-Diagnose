"""Configuration management for the QuantWarriors QML platform."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "QuantWarriors-QML"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./quantwarriors.db"
    
    # Paths
    data_dir: str = "./data"
    upload_dir: str = "./data/uploads"
    artifacts_dir: str = "./artifacts"
    
    # Quantum Configuration
    quantum_max_qubits: int = 8
    quantum_layers: int = 2
    quantum_shots: int = 1024
    
    # Feature Reduction
    pca_candidate_dimensions: List[int] = Field(default_factory=lambda: [4, 8])
    
    # Experiment
    random_state: int = 42
    test_size: float = 0.2
    max_runtime_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ConfigManager:
    """Manages configuration from YAML file and environment."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.settings = Settings()
        self.config_path = config_path or "config.yaml"
        self._yaml_config = self._load_yaml()
    
    def _load_yaml(self) -> dict:
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    @property
    def experiment(self) -> dict:
        """Get experiment configuration."""
        return self._yaml_config.get('experiment', {
            'random_state': self.settings.random_state,
            'test_size': self.settings.test_size
        })
    
    @property
    def classical_models(self) -> list:
        """Get classical model list."""
        return self._yaml_config.get('classical', {}).get('models', [
            'logistic_regression', 'svm', 'random_forest'
        ])
    
    @property
    def quantum_config(self) -> dict:
        """Get quantum configuration."""
        default_config = {
            'model': 'vqc',
            'max_qubits': self.settings.quantum_max_qubits,
            'candidate_dimensions': self.settings.pca_candidate_dimensions,
            'layers': self.settings.quantum_layers,
            'shots': self.settings.quantum_shots
        }
        return self._yaml_config.get('quantum', default_config)
    
    @property
    def feature_reduction(self) -> dict:
        """Get feature reduction configuration."""
        return self._yaml_config.get('feature_reduction', {
            'method': 'pca',
            'variance_threshold': 0.95
        })
    
    @property
    def resources(self) -> dict:
        """Get resource limits."""
        return self._yaml_config.get('resources', {
            'max_runtime_seconds': self.settings.max_runtime_seconds
        })


# Global config instance
config = ConfigManager()
