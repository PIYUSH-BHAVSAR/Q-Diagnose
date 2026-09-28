"""
backend/models/quantum/backend.py
Owner: Piyush
Phase: 8

QuantumBackend abstraction — phase8.md §21-25.
"The rest of the platform should not need to know which backend is being used."

The VQC never hardcodes `default.qubit` directly.
It calls `backend.get_device(n_qubits)`.
When we later move to IBM hardware, only this file changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class QuantumBackend(ABC):
    """
    Abstract quantum backend.

    Implementations:
        LocalSimulatorBackend  — PennyLane default.qubit (MVP)
        RemoteSimulatorBackend — future: cloud simulator
        RealQuantumBackend     — future: IBM / other hardware
    """

    @abstractmethod
    def get_device(self, n_qubits: int) -> Any:
        """Return a PennyLane device configured for n_qubits."""
        ...

    @abstractmethod
    def get_resource_info(self) -> dict:
        """Return metadata dict for storage in ModelResult.backend_type etc."""
        ...

    @property
    @abstractmethod
    def backend_type(self) -> str:
        """String identifier: 'LOCAL_SIMULATOR', 'REMOTE_SIMULATOR', 'REAL_HARDWARE'."""
        ...


class LocalSimulatorBackend(QuantumBackend):
    """
    PennyLane default.qubit state-vector simulator.

    From phase8.md §22:
        Advantages: no cloud cost, easy development, reproducible, fast for small circuits.
        Limit: does not represent real hardware noise.

    For 8 qubits: 2^8 = 256 amplitudes in state vector — manageable on any machine.
    """

    def get_device(self, n_qubits: int):
        import pennylane as qml
        return qml.device("default.qubit", wires=n_qubits)

    def get_resource_info(self) -> dict:
        return {
            "backend_type": "LOCAL_SIMULATOR",
            "provider":     "PennyLane",
            "device":       "default.qubit",
            "description":  "State-vector simulator — no hardware noise",
        }

    @property
    def backend_type(self) -> str:
        return "LOCAL_SIMULATOR"
