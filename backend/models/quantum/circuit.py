"""
backend/models/quantum/circuit.py
Owner: Piyush
Phase: 8

VQC circuit builder — parameterized quantum circuit for binary classification.
From phase8.md §16-17:

    Architecture:
        Layer 0: Angle encoding (RY rotations from AngleEncoder)
        Variational layers (configurable n_layers):
            - RY(θ_i, wires=i) per qubit
            - RZ(θ_i, wires=i) per qubit
            - Linear CNOT entanglement: qubit i → qubit i+1
        Measurement: qml.expval(qml.PauliZ(0)) on first qubit

    From phase8.md §15: record circuit stats — qubits, layers, gate_count, two_qubit_gates.

Parameter layout for n_qubits=8, n_layers=2:
    params shape: (n_layers * n_qubits * 2,)  = (32,) for 8q 2l
    params[layer * n_qubits*2 : layer * n_qubits*2 + n_qubits] → RY angles
    params[layer * n_qubits*2 + n_qubits : ...]               → RZ angles
"""

from __future__ import annotations

from typing import Callable

import numpy as np


def count_params(n_qubits: int, n_layers: int) -> int:
    """Total trainable parameters: RY + RZ per qubit per layer."""
    return n_layers * n_qubits * 2


def count_gates(n_qubits: int, n_layers: int) -> int:
    """
    Total gate count (encoding + variational + entanglement).
    Encoding: n_qubits RY gates
    Variational: n_layers * n_qubits * 2 (RY+RZ)
    Entanglement: n_layers * (n_qubits - 1) CNOT
    """
    encoding_gates = n_qubits
    variational_gates = n_layers * n_qubits * 2
    entanglement_gates = n_layers * (n_qubits - 1)
    return encoding_gates + variational_gates + entanglement_gates


def count_two_qubit_gates(n_qubits: int, n_layers: int) -> int:
    """CNOT gates only: linear chain per layer."""
    return n_layers * (n_qubits - 1)


def circuit_depth(n_layers: int) -> int:
    """
    Approximate circuit depth:
        1 encoding layer + n_layers variational layers + 1 measurement layer
    """
    return n_layers * 2 + 1


def build_vqc_circuit(n_qubits: int, n_layers: int, device) -> Callable:
    """
    Build and return a PennyLane QNode for the VQC.

    Args:
        n_qubits: number of qubits (= number of PCA features)
        n_layers: number of variational layers
        device:   PennyLane device (from QuantumBackend.get_device())

    Returns:
        circuit: callable(features, params) → float (PauliZ expectation on qubit 0)
                 Output range: [-1, 1]
                 Mapped to [0, 1] probability by: (output + 1) / 2
    """
    import pennylane as qml
    from backend.models.quantum.encoding import AngleEncoder

    encoder = AngleEncoder(n_qubits)

    @qml.qnode(device)
    def circuit(features: np.ndarray, params: np.ndarray) -> float:
        """
        QNode: takes one sample (n_qubits features) + parameter array.

        Phase 8 circuit architecture:
            1. Angle encoding: RY(x * π) on each qubit
            2. Variational layers:
                - RY(θ) + RZ(θ) on each qubit (trainable)
                - Linear CNOT chain: 0→1, 1→2, ..., (n-1)→n
            3. Measurement: <Z> on qubit 0

        Returns PauliZ expectation ∈ [-1, 1].
        """
        # ── Layer 0: Angle encoding ───────────────────────────────────────────
        encoder.encode(features)

        # ── Variational layers ────────────────────────────────────────────────
        for layer in range(n_layers):
            base_ry = layer * n_qubits * 2
            base_rz = base_ry + n_qubits

            # Single-qubit rotations (trainable)
            for qubit in range(n_qubits):
                qml.RY(params[base_ry + qubit], wires=qubit)
                qml.RZ(params[base_rz + qubit], wires=qubit)

            # Linear entanglement: CNOT chain (phase8.md §17)
            for qubit in range(n_qubits - 1):
                qml.CNOT(wires=[qubit, qubit + 1])

        # ── Measurement ───────────────────────────────────────────────────────
        return qml.expval(qml.PauliZ(0))

    return circuit
