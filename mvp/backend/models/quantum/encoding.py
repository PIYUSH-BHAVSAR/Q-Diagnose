"""Quantum encoding methods for mapping classical data to quantum states.

Angle encoding maps classical values to rotation angles of quantum gates.
"""

from typing import List, Optional

import numpy as np

from backend.core.logging import logger


class AngleEncoder:
    """Encodes classical data using angle encoding.
    
    Maps each feature value to a rotation angle on a qubit.
    """
    
    def __init__(
        self,
        n_qubits: int,
        rotation: str = 'Y',
        scaling: bool = True
    ):
        """Initialize angle encoder.
        
        Args:
            n_qubits: Number of qubits (matches feature count)
            rotation: Rotation axis ('X', 'Y', 'Z', 'XY')
            scaling: Whether to scale inputs to [0, π]
        """
        self.n_qubits = n_qubits
        self.rotation = rotation
        self.scaling = scaling
    
    def encode(self, x: np.ndarray) -> np.ndarray:
        """Encode classical features to rotation angles.
        
        Args:
            x: Input features (1D array of length n_qubits)
        
        Returns:
            Array of rotation angles
        """
        if len(x) != self.n_qubits:
            raise ValueError(
                f"Expected {self.n_qubits} features, got {len(x)}"
            )
        
        if self.scaling:
            # Scale to [0, π]
            x_scaled = np.pi * (x - x.min()) / (x.max() - x.min() + 1e-10)
        else:
            x_scaled = x
        
        return x_scaled
    
    def encode_batch(self, X: np.ndarray) -> np.ndarray:
        """Encode a batch of samples.

        Uses per-feature scaling fitted across the entire batch so that
        a single-sample batch doesn't collapse to NaN (min==max → divide by 0).
        """
        if X.shape[1] != self.n_qubits:
            raise ValueError(
                f"Expected {self.n_qubits} features per sample, got {X.shape[1]}"
            )

        if self.scaling:
            X_scaled = np.zeros_like(X, dtype=float)
            for i in range(X.shape[1]):
                col = X[:, i]
                col_min, col_max = col.min(), col.max()
                rng = col_max - col_min
                if rng < 1e-10:
                    # Feature is constant — map to mid-angle π/2
                    X_scaled[:, i] = np.pi / 2
                else:
                    X_scaled[:, i] = np.pi * (col - col_min) / rng
            return X_scaled
        else:
            return X.astype(float)


class AmplitudeEncoder:
    """Encodes classical data using amplitude encoding.
    
    Maps classical data to the amplitudes of a quantum state.
    """
    
    def __init__(self, n_qubits: int):
        """Initialize amplitude encoder.
        
        Args:
            n_qubits: Number of qubits (2^n_qubits >= n_features)
        """
        self.n_qubits = n_qubits
        self.dimension = 2 ** n_qubits
    
    def encode(self, x: np.ndarray) -> np.ndarray:
        """Encode features to amplitude vector.
        
        Args:
            x: Input features
        
        Returns:
            Normalized amplitude vector
        """
        # Pad to dimension
        if len(x) > self.dimension:
            raise ValueError(
                f"Too many features ({len(x)}) for {self.n_qubits} qubits"
            )
        
        padded = np.zeros(self.dimension)
        padded[:len(x)] = x
        
        # Normalize
        norm = np.linalg.norm(padded)
        if norm > 1e-10:
            padded = padded / norm
        
        return padded
    
    def encode_batch(self, X: np.ndarray) -> np.ndarray:
        """Encode a batch of samples."""
        encoded = np.zeros((X.shape[0], self.dimension))
        for i, x in enumerate(X):
            encoded[i] = self.encode(x)
        return encoded
