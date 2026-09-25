"""Dataset API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.data.loader import DatasetLoader
from backend.data.profiler import DatasetProfiler
from backend.data.validator import DatasetValidator
from backend.core.logging import logger


router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# Global instances
loader = DatasetLoader()
profiler = DatasetProfiler()
validator = DatasetValidator()


class DatasetResponse(BaseModel):
    """Response for dataset upload."""
    dataset_id: str
    filename: str
    status: str


class DatasetProfileResponse(BaseModel):
    """Response for dataset profile."""
    dataset_id: str
    name: str
    rows: int
    columns: int
    missing_values_total: int
    missing_percentage: float
    duplicate_rows: int
    numerical_columns_count: int
    categorical_columns_count: int
    target_candidates: List[str]
    recommended_target: Optional[str]
    is_binary_classification: bool
    class_distribution: Optional[dict]
    columns: List[dict]


class DatasetListResponse(BaseModel):
    """Response for dataset list."""
    datasets: List[dict]


class ValidationResponse(BaseModel):
    """Response for dataset validation."""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    ready_for_ml: bool
    needs_target_selection: bool
    details: dict


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None
):
    """Upload a CSV dataset.
    
    Accepts CSV files and returns a dataset ID for subsequent operations.
    
    Args:
        file: Uploaded CSV file
        name: Optional dataset name
    
    Returns:
        Dataset ID and upload status
    """
    logger.info(f"Uploading dataset: {file.filename}")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )
    
    # Read file content
    content = await file.read()
    
    # Save and load
    try:
        dataset_id, file_path = loader.save_uploaded_file(
            content,
            file.filename,
            name
        )
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    return DatasetResponse(
        dataset_id=dataset_id,
        filename=file.filename,
        status="uploaded"
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets():
    """List all uploaded datasets.
    
    Returns:
        List of dataset metadata
    """
    datasets = loader.list_datasets()
    
    return DatasetListResponse(datasets=datasets)


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get dataset metadata.
    
    Args:
        dataset_id: Dataset identifier
    
    Returns:
        Dataset metadata
    """
    try:
        info = loader.get_dataset_info(dataset_id)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_dataset_profile(dataset_id: str):
    """Get dataset profile with statistics.
    
    Profiles the dataset if not already done and returns comprehensive statistics.
    
    Args:
        dataset_id: Dataset identifier
    
    Returns:
        Complete dataset profile
    """
    import pandas as pd
    
    # Get dataset info
    try:
        info = loader.get_dataset_info(dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Load DataFrame
    df = pd.read_csv(info['path'])
    
    # Profile
    profile = profiler.profile(df, dataset_id, info['name'])
    
    return profile.to_dict()


@router.post("/{dataset_id}/validate", response_model=ValidationResponse)
async def validate_dataset(
    dataset_id: str,
    target_column: Optional[str] = None
):
    """Validate dataset for ML pipeline.
    
    Checks if the dataset is suitable for the ML pipeline.
    
    Args:
        dataset_id: Dataset identifier
        target_column: Optional target column override
    
    Returns:
        Validation result
    """
    import pandas as pd
    
    # Get dataset info
    try:
        info = loader.get_dataset_info(dataset_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    # Load and profile
    df = pd.read_csv(info['path'])
    profile = profiler.profile(df, dataset_id, info['name'])
    
    # Validate
    result = validator.validate(df, profile, target_column)
    
    return result.to_dict()
