"""Quantum circuit definitions for VQC.

Implements variational quantum circuits with angle encoding
and trainable rotation layers.
"""

from typing import Tuple, Any

import numpy as np
import pennylane as qml

from backend.core.logging import logger


class VariationalCircuit:
    """Variational quantum circuit for classification.

    Architecture:
        1. Angle encoding (input features -> qubit rotations)
        2. Variational layers (trainable rotations + entanglement)
        3. Measurement (expectation of Z on first qubit)
    """

    def __init__(
        self,
        n_qubits: int,
        n_layers: int = 2,
        encoding: str = "angle",
        entanglement: str = "full",
    ):
        """Initialize variational circuit.

        Args:
            n_qubits: Number of qubits.
            n_layers: Number of variational layers.
            encoding: Encoding type ('angle').
            entanglement: Entanglement pattern ('full', 'linear').
        """
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.encoding = encoding
        self.entanglement = entanglement

        # Parameter count:
        # 2 parameters per qubit per layer:
        # RY + RZ
        self.n_params = n_qubits * n_layers * 2

    def build_circuit(self, device: Any):
        """Build the quantum circuit.

        Args:
            device: PennyLane device.

        Returns:
            PennyLane QNode.
        """

        @qml.qnode(device, interface="numpy")
        def circuit(x: np.ndarray, params: np.ndarray) -> np.ndarray:
            """Quantum circuit node.

            Args:
                x: Input features encoded as angles.
                params: Trainable parameters.

            Returns:
                Expectation value of Z on the first qubit.
            """

            # Input encoding
            self._encode_features(x)

            # Variational layers
            self._variational_layers(params)

            # Measurement
            return qml.expval(qml.PauliZ(0))

        return circuit

    def _encode_features(self, x: np.ndarray):
        """Encode input features as rotation angles.

        Args:
            x: Input features. Length must be at least n_qubits.
        """

        if len(x) < self.n_qubits:
            raise ValueError(
                f"Input has {len(x)} features, but "
                f"{self.n_qubits} qubits are required."
            )

        for i in range(self.n_qubits):
            qml.RY(x[i], wires=i)

    def _variational_layers(self, params: np.ndarray):
        """Apply variational layers.

        Each layer consists of:
            1. Trainable RY and RZ rotations.
            2. Entangling gates.

        Args:
            params: Trainable parameters.

        Expected parameter layout:
            n_layers * n_qubits * 2
        """

        expected_params = self.n_layers * self.n_qubits * 2

        if len(params) != expected_params:
            raise ValueError(
                f"Expected {expected_params} parameters, "
                f"but received {len(params)}."
            )

        param_idx = 0

        for _layer in range(self.n_layers):

            # Trainable rotations
            for qubit in range(self.n_qubits):

                qml.RY(
                    params[param_idx],
                    wires=qubit,
                )
                param_idx += 1

                qml.RZ(
                    params[param_idx],
                    wires=qubit,
                )
                param_idx += 1

            # Entanglement
            self._entangle()

    def _entangle(self):
        """Apply entanglement gates."""

        if self.n_qubits < 2:
            return

        if self.entanglement == "full":

            # Full entanglement:
            # CNOT between every pair of qubits.
            for i in range(self.n_qubits - 1):
                for j in range(i + 1, self.n_qubits):
                    qml.CNOT(wires=[i, j])

        elif self.entanglement == "linear":

            # Nearest-neighbor entanglement.
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        else:
            raise ValueError(
                f"Unsupported entanglement pattern: "
                f"{self.entanglement}. "
                f"Use 'full' or 'linear'."
            )

    def get_random_params(self) -> np.ndarray:
        """Generate random initial trainable parameters.

        Returns:
            NumPy array containing random parameters.
        """

        return np.random.uniform(
            -np.pi,
            np.pi,
            self.n_params,
        )


class QCircuitBuilder:
    """Builder for creating quantum circuits."""

    @staticmethod
    def build_vqc(
        n_qubits: int,
        n_layers: int = 2,
        device_type: str = "default.qubit",
    ) -> Tuple[VariationalCircuit, Any]:
        """Build a VQC circuit.

        Args:
            n_qubits: Number of qubits.
            n_layers: Number of variational layers.
            device_type: PennyLane device type.

        Returns:
            Tuple containing:
                - VariationalCircuit
                - PennyLane device
        """

        # Validate configuration
        if n_qubits < 1:
            raise ValueError(
                "n_qubits must be at least 1."
            )

        if n_layers < 1:
            raise ValueError(
                "n_layers must be at least 1."
            )

        # Create PennyLane device
        device = qml.device(
            device_type,
            wires=n_qubits,
        )

        # Create circuit
        circuit = VariationalCircuit(
            n_qubits=n_qubits,
            n_layers=n_layers,
        )

        logger.info(
            f"Built VQC: "
            f"n_qubits={n_qubits}, "
            f"n_layers={n_layers}, "
            f"params={circuit.n_params}, "
            f"device={device_type}"
        )

        return circuit, device