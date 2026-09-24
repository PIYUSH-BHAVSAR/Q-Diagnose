"""Quantum backend abstraction layer.

Provides a unified interface for different quantum backends,
enabling future migration to cloud/hardware without code changes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

import pennylane as qml

from backend.core.logging import logger


class QuantumBackend(ABC):
    """Abstract base class for quantum backends."""
    
    @abstractmethod
    def get_device(self, n_qubits: int, shots: Optional[int] = None):
        """Get a quantum device.
        
        Args:
            n_qubits: Number of qubits
            shots: Number of shots (None for exact)
        
        Returns:
            PennyLane device
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict:
        """Get backend information.
        
        Returns:
            Backend metadata
        """
        pass


class LocalSimulatorBackend(QuantumBackend):
    """Local simulator backend using PennyLane default.qubit."""
    
    def __init__(self, name: str = 'default.qubit'):
        """Initialize local simulator.
        
        Args:
            name: PennyLane device name
        """
        self.name = name
        self.type = 'local_simulator'
    
    def get_device(self, n_qubits: int, shots: Optional[int] = None):
        """Get local simulator device.
        
        Args:
            n_qubits: Number of qubits
            shots: Number of shots (None for exact)
        
        Returns:
            PennyLane device
        """
        device = qml.device(
            self.name,
            wires=n_qubits,
            shots=shots
        )
        
        logger.info(
            f"Created device: {self.name}, qubits={n_qubits}, shots={shots or 'exact'}"
        )
        
        return device
    
    def get_info(self) -> Dict:
        """Get backend information."""
        return {
            'name': self.name,
            'type': self.type,
            'provider': 'PennyLane',
            'location': 'local',
            'cost': 'none',
            'max_qubits': 30,
            'supports_shots': True,
            'supports_exact': True
        }


class BackendFactory:
    """Factory for creating quantum backends."""
    
    _backends = {
        'local': LocalSimulatorBackend,
        'default.qubit': LocalSimulatorBackend,
    }
    
    @classmethod
    def create(cls, backend_type: str = 'local', **kwargs) -> QuantumBackend:
        """Create a quantum backend.
        
        Args:
            backend_type: Backend type identifier
            **kwargs: Backend-specific parameters
        
        Returns:
            Quantum backend instance
        """
        if backend_type not in cls._backends:
            logger.warning(
                f"Unknown backend '{backend_type}', falling back to local"
            )
            backend_type = 'local'
        
        backend_class = cls._backends[backend_type]
        return backend_class(**kwargs)
    
    @classmethod
    def list_backends(cls) -> list:
        """List available backend types."""
        return list(cls._backends.keys())


# Default backend instance
default_backend = BackendFactory.create('local')
