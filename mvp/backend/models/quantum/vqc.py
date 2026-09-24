"""Variational Quantum Classifier (VQC) implementation.

Implements a VQC using PennyLane with angle encoding for binary classification.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pennylane as qml
from pennylane.optimize import NesterovMomentumOptimizer, AdamOptimizer

from backend.core.config import config
from backend.core.logging import logger
from backend.models.classical.logistic_regression import ModelResult
from backend.models.quantum.circuit import VariationalCircuit, QCircuitBuilder
from backend.models.quantum.encoding import AngleEncoder
from backend.models.shared_metrics import safe_classification_metrics


@dataclass
class VQCTrainingConfig:
    """Configuration for VQC training."""
    n_layers: int = 2
    n_qubits: int = 8
    shots: Optional[int] = None
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.01
    optimizer: str = 'adam'


@dataclass
class QuantumResources:
    """Quantum resource usage metrics."""
    n_qubits: int
    n_layers: int
    n_params: int
    shots: Optional[int]
    circuit_depth: int
    n_circuit_executions: int
    training_time: float
    
    def to_dict(self) -> dict:
        return {
            'n_qubits': self.n_qubits,
            'n_layers': self.n_layers,
            'n_params': self.n_params,
            'shots': self.shots,
            'circuit_depth': self.circuit_depth,
            'n_circuit_executions': self.n_circuit_executions,
            'training_time': self.training_time
        }


class VQCModel:
    """Variational Quantum Classifier for binary classification.
    
    Architecture:
    1. Angle encoding: Classical features -> Rotation angles
    2. Variational circuit: Trainable rotations + entanglement
    3. Measurement: Expectation value -> Binary prediction
    """
    
    def __init__(
        self,
        n_qubits: int = 8,
        n_layers: int = 2,
        shots: Optional[int] = None,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.01,
        random_state: int = 42
    ):
        """Initialize VQC model.
        
        Args:
            n_qubits: Number of qubits (must match input features)
            n_layers: Number of variational layers
            shots: Number of shots for sampling (None for exact)
            epochs: Training epochs
            batch_size: Mini-batch size
            learning_rate: Learning rate for optimizer
            random_state: Random seed
        """
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.shots = shots
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.random_state = random_state
        
        # Components
        self.circuit: Optional[VariationalCircuit] = None
        self.encoder: Optional[AngleEncoder] = None
        self.device: Optional[qml.QubitDevice] = None
        self.qnode_ = None   # cached QNode — built once, reused for predict
        self.params_: Optional[np.ndarray] = None
        
        # Training state
        self.is_fitted = False
        self.loss_history: List[float] = []
        
        # Resource tracking
        self.n_executions = 0
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None
    ) -> ModelResult:
        """Train the VQC model.
        
        Args:
            X_train: Training features (n_qubits features)
            y_train: Training labels (binary: 0/1)
            X_test: Test features for evaluation
            y_test: Test labels for evaluation
        
        Returns:
            ModelResult with predictions and metrics
        """
        np.random.seed(self.random_state)
        
        logger.info("=" * 60)
        logger.info(f"Training VQC Model")
        logger.info(f"  n_qubits: {self.n_qubits}")
        logger.info(f"  n_layers: {self.n_layers}")
        logger.info(f"  epochs: {self.epochs}")
        logger.info(f"  shots: {self.shots or 'exact'}")
        logger.info("=" * 60)
        
        # Validate input
        if X_train.shape[1] != self.n_qubits:
            raise ValueError(
                f"Expected {self.n_qubits} features, got {X_train.shape[1]}"
            )
        
        # Initialize components
        self._initialize_model()
        
        # Encode data
        X_encoded = self.encoder.encode_batch(X_train)
        
        # Map labels to [-1, 1] for quantum classifier
        y_mapped = 2 * y_train - 1
        
        # Initialize parameters
        self.params_ = self.circuit.get_random_params()
        
        # Make params a PennyLane numpy array that tracks gradients
        self.params_ = qml.numpy.array(self.params_, requires_grad=True)
        
        # Training — always use exact simulation for stable gradients.
        # shots is only stored for resource reporting, not actually used
        # in training (shot-based PennyLane returns integer counts that
        # break the continuous MSE loss and probability mapping below).
        start_time = time.perf_counter()
        optimizer = AdamOptimizer(stepsize=self.learning_rate)
        
        # Create QNode — build once and cache
        qnode = self.circuit.build_circuit(self.device)
        self.qnode_ = qnode
        
        # Training loop
        self.loss_history = []
        self.n_executions = 0
        
        n_samples = len(X_encoded)
        
        for epoch in range(self.epochs):
            # Shuffle data
            indices = np.random.permutation(n_samples)
            X_shuffled = X_encoded[indices]
            y_shuffled = y_mapped[indices]
            
            # Mini-batch training
            epoch_loss = 0.0
            n_batches = 0
            
            for i in range(0, n_samples, self.batch_size):
                batch_X = X_shuffled[i:i+self.batch_size]
                batch_y = y_shuffled[i:i+self.batch_size]
                
                # Cost function
                def cost(params):
                    batch_loss = 0.0
                    for x, y in zip(batch_X, batch_y):
                        pred = qnode(x, params)
                        batch_loss = batch_loss + (pred - y) ** 2
                        self.n_executions += 1
                    return batch_loss / len(batch_X)
                
                # Optimization step - step_and_cost returns (new_params, loss_value)
                self.params_, batch_loss = optimizer.step_and_cost(
                    cost, self.params_
                )
                epoch_loss += batch_loss
                n_batches += 1
            
            avg_loss = epoch_loss / n_batches
            self.loss_history.append(avg_loss)
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.4f}")
        
        training_time = time.perf_counter() - start_time
        
        self.is_fitted = True
        
        # Predictions
        y_pred_train = self.predict(X_train)
        
        y_pred_test = None
        y_pred_proba_test = None
        metrics = {}
        
        if X_test is not None and y_test is not None:
            start_time = time.perf_counter()
            y_pred_test = self.predict(X_test)
            y_pred_proba_test = self.predict_proba(X_test)
            inference_time = time.perf_counter() - start_time
            metrics = self._calculate_metrics(y_test, y_pred_test, y_pred_proba_test)
        else:
            inference_time = 0.0
        
        # Quantum resources
        resources = QuantumResources(
            n_qubits=self.n_qubits,
            n_layers=self.n_layers,
            n_params=self.circuit.n_params,
            shots=self.shots,
            circuit_depth=self._estimate_depth(),
            n_circuit_executions=self.n_executions,
            training_time=training_time
        )
        metrics['quantum_resources'] = resources.to_dict()
        
        logger.info(f"VQC training complete: {training_time:.2f}s, {self.n_executions} executions")
        
        return ModelResult(
            model_name='vqc',
            model_type='quantum',
            y_pred_train=y_pred_train,
            y_pred_test=y_pred_test,
            y_pred_proba_test=y_pred_proba_test,
            metrics=metrics,
            training_time=training_time,
            inference_time=inference_time,
            model=self
        )
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary labels.
        
        Args:
            X: Input features
        
        Returns:
            Binary predictions (0/1)
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        proba = self.predict_proba(X)
        return (proba >= 0.5).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for positive class.
        
        Args:
            X: Input features
        
        Returns:
            Probability array
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction")
        
        X_encoded = self.encoder.encode_batch(X)
        qnode = self.qnode_  # use cached node — don't rebuild on every call

        # Get expectation values (mapped from [-1,1] to [0,1])
        expectations = np.array([
            qnode(x, self.params_) for x in X_encoded
        ])
        
        # Map to probabilities: [-1, 1] -> [0, 1]
        proba = (expectations + 1) / 2
        
        return proba
    
    def _initialize_model(self):
        """Initialize quantum circuit and encoder."""
        # Always use exact (statevector) simulation for training.
        # Shot-based simulation produces integer samples that break
        # the continuous MSE loss and [-1,1] -> [0,1] probability mapping.
        device_name = 'default.qubit'
        self.device = qml.device(
            device_name,
            wires=self.n_qubits,
            shots=None   # exact — shots stored in resources for reporting only
        )
        
        # Create circuit
        self.circuit = VariationalCircuit(
            n_qubits=self.n_qubits,
            n_layers=self.n_layers
        )
        
        # Create encoder
        self.encoder = AngleEncoder(n_qubits=self.n_qubits)
        
        logger.info(
            f"Initialized VQC: qubits={self.n_qubits}, "
            f"layers={self.n_layers}, params={self.circuit.n_params}"
        )
    
    def _estimate_depth(self) -> int:
        """Estimate circuit depth."""
        # Rough estimate: encoding + layers * (rotations + entanglement)
        depth = self.n_qubits  # Encoding
        depth += self.n_layers * (self.n_qubits * 2 + self.n_qubits)  # Layers
        return depth
    
    def _calculate_metrics(self, y_true, y_pred, y_pred_proba=None):
        return safe_classification_metrics(y_true, y_pred, y_pred_proba)
    
    def get_circuit_diagram(self) -> str:
        """Get circuit diagram representation."""
        if self.circuit is None:
            return "Circuit not initialized"
        
        return (
            f"VQC Circuit\n"
            f"  Qubits: {self.n_qubits}\n"
            f"  Layers: {self.n_layers}\n"
            f"  Parameters: {self.circuit.n_params}\n"
            f"  Shots: {self.shots or 'exact'}\n"
            f"\n"
            f"  Structure:\n"
            f"    1. Angle encoding (RY rotations)\n"
            f"    2. Variational layers (RY, RZ + CNOT)\n"
            f"    3. Measurement (Z on qubit 0)"
        )
