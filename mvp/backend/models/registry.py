"""Model registry for managing available models."""

from typing import Dict, List, Optional, Type

from backend.core.logging import logger


class ModelRegistry:
    """Registry for managing available ML models."""
    
    _models: Dict[str, dict] = {}
    
    @classmethod
    def register(
        cls,
        name: str,
        model_type: str,
        description: str = "",
        default_params: Optional[dict] = None
    ):
        """Register a model.
        
        Args:
            name: Model name
            model_type: 'classical' or 'quantum'
            description: Model description
            default_params: Default parameters for the model
        """
        cls._models[name] = {
            'name': name,
            'type': model_type,
            'description': description,
            'default_params': default_params or {}
        }
        logger.debug(f"Registered model: {name} ({model_type})")
    
    @classmethod
    def get_model_info(cls, name: str) -> Optional[dict]:
        """Get information about a registered model."""
        return cls._models.get(name)
    
    @classmethod
    def list_models(cls, model_type: Optional[str] = None) -> List[dict]:
        """List all registered models.
        
        Args:
            model_type: Optional filter by type ('classical' or 'quantum')
        
        Returns:
            List of model info dictionaries
        """
        if model_type:
            return [
                m for m in cls._models.values()
                if m['type'] == model_type
            ]
        return list(cls._models.values())
    
    @classmethod
    def list_classical(cls) -> List[str]:
        """List classical model names."""
        return [
            name for name, info in cls._models.items()
            if info['type'] == 'classical'
        ]
    
    @classmethod
    def list_quantum(cls) -> List[str]:
        """List quantum model names."""
        return [
            name for name, info in cls._models.items()
            if info['type'] == 'quantum'
        ]


# Register default models
ModelRegistry.register(
    'logistic_regression',
    'classical',
    'Logistic Regression classifier with L2 regularization',
    {'max_iter': 1000, 'random_state': 42}
)

ModelRegistry.register(
    'svm',
    'classical',
    'Support Vector Machine with RBF kernel',
    {'kernel': 'rbf', 'random_state': 42, 'probability': True}
)

ModelRegistry.register(
    'random_forest',
    'classical',
    'Random Forest ensemble classifier',
    {'n_estimators': 100, 'max_depth': 10, 'random_state': 42}
)

ModelRegistry.register(
    'vqc',
    'quantum',
    'Variational Quantum Classifier using angle encoding',
    {'layers': 2, 'shots': 1024}
)
