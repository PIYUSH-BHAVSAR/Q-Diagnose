# exceptions.py
# Standalone custom exceptions for the Q-Diagnose pipeline.
# During team integration, replace with: from core.exceptions import *


class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    pass


class DataLoadError(PipelineError):
    """Raised when data cannot be loaded from the source."""
    pass


class DataValidationError(PipelineError):
    """Raised when dataset fails critical validation checks."""
    pass


class PreprocessingError(PipelineError):
    """Raised when preprocessing fails."""
    pass


class FeatureEngineeringError(PipelineError):
    """Raised when feature engineering fails."""
    pass


class DimensionalityReductionError(PipelineError):
    """Raised when PCA / dimensionality reduction fails."""
    pass


class ProfilingError(PipelineError):
    """Raised when dataset profiling fails."""
    pass
