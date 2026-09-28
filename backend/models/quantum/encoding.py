"""
backend/models/quantum/encoding.py
Owner: Piyush
Phase: 8

AngleEncoder — maps classical features to quantum rotation angles.
From phase8.md §10-13 + guide_piyush.md §6:

    Angle encoding: each feature xi → RY(xi * π, wires=i)

    Feature range requirement (phase8.md §12):
        Jayed's StandardScaler already ran in Phase 4.
        DO NOT apply StandardScaler again (phase8.md §13).
        Instead: clip to ±3σ (which is ±3 for N(0,1)) → scale to [-1, 1]
        Then apply RY(x * π, wires=i) so angle is in [-π, π]

Usage inside a QNode:
    encoder = AngleEncoder(n_qubits=8)
    encoder.encode(features)   # applies gates inside circuit

Usage outside a QNode (preprocessing):
    X_scaled = encoder.scale_features(X_train_reduced)
"""

from __future__ import annotations

import numpy as np


class AngleEncoder:
    """
    Encodes classical feature vectors as quantum rotation angles (RY gates).

    One qubit per feature. For 8 PCA components → 8 qubits.

    Key rule (phase8.md §13):
        Phase 4 already applied StandardScaler.
        scale_features() only clips and rescales — it does NOT call
        StandardScaler again. Jayed's output is already N(0,1)-ish.
    """

    def __init__(self, n_qubits: int) -> None:
        self.n_qubits = n_qubits

    def encode(self, features: np.ndarray) -> None:
        """
        Apply RY(x * π, wires=i) for each feature.
        Must be called INSIDE a PennyLane QNode (circuit function).

        Args:
            features: 1-D array of scaled features, length >= n_qubits.
                      Values should be in [-1, 1] (after scale_features()).
        """
        import pennylane as qml
        for i in range(self.n_qubits):
            # features[i] ∈ [-1, 1] → angle ∈ [-π, π]
            qml.RY(float(features[i]) * np.pi, wires=i)

    def scale_features(self, X: np.ndarray) -> np.ndarray:
        """
        Map StandardScaler output to [-1, 1] for angle encoding.

        Method (phase8.md §12 + guide_piyush.md §9 rules):
            1. Clip to ±3 standard deviations (covers 99.7% of N(0,1))
            2. Divide by 3 → maps [-3, 3] to [-1, 1]

        Args:
            X: ndarray shape (n_samples, n_features), already N(0,1) scaled by Jayed

        Returns:
            ndarray same shape, values in [-1, 1]
        """
        X_clipped = np.clip(X, -3.0, 3.0)
        return X_clipped / 3.0
