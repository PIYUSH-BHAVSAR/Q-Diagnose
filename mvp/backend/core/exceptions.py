"""Custom exceptions for the platform."""


class QuantWarriorsError(Exception):
    """Base exception for all platform errors."""
    pass


class DatasetError(QuantWarriorsError):
    """Errors related to dataset operations."""
    pass


class DatasetUploadError(DatasetError):
    """Error during dataset upload."""
    pass


class DatasetValidationError(DatasetError):
    """Error during dataset validation."""
    pass


class DatasetNotFoundError(DatasetError):
    """Dataset not found."""
    pass


class TargetDetectionError(DatasetError):
    """Could not detect target column."""
    pass


class PreprocessingError(QuantWarriorsError):
    """Error during preprocessing."""
    pass


class FeatureReductionError(QuantWarriorsError):
    """Error during feature reduction."""
    pass


class ModelError(QuantWarriorsError):
    """Errors related to model operations."""
    pass


class ClassicalModelError(ModelError):
    """Error in classical model execution."""
    pass


class QuantumModelError(ModelError):
    """Error in quantum model execution."""
    pass


class ExperimentError(QuantWarriorsError):
    """Errors related to experiment operations."""
    pass


class ExperimentNotFoundError(ExperimentError):
    """Experiment not found."""
    pass


class ExperimentExecutionError(ExperimentError):
    """Error during experiment execution."""
    pass


class ConfigurationError(QuantWarriorsError):
    """Error in configuration."""
    pass


class ResourceLimitError(QuantWarriorsError):
    """Resource limit exceeded."""
    pass


class StorageError(QuantWarriorsError):
    """Error in storage operations."""
    pass
