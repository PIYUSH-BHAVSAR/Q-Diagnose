"""Dataset loader for CSV files."""

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from backend.core.exceptions import DatasetUploadError, DatasetNotFoundError
from backend.core.logging import logger


class DatasetLoader:
    """Handles loading and initial processing of CSV datasets."""
    
    SUPPORTED_EXTENSIONS = ['.csv']
    MAX_FILE_SIZE_MB = 100
    _datasets: Dict[str, dict] = {}
    
    def __init__(self, upload_dir: str = "./data/uploads"):
        """Initialize the dataset loader.
        
        Args:
            upload_dir: Directory for uploaded datasets
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def load_csv(
        self,
        file_path: str,
        dataset_name: Optional[str] = None,
        dataset_id: Optional[str] = None
    ) -> Tuple[str, pd.DataFrame]:
        """Load a CSV file and register it.
        
        Args:
            file_path: Path to CSV file
            dataset_name: Optional name for the dataset
            dataset_id: Optional custom dataset ID
        
        Returns:
            Tuple of (dataset_id, DataFrame)
        
        Raises:
            DatasetUploadError: If file cannot be loaded
        """
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise DatasetNotFoundError(f"File not found: {file_path}")
        
        # Validate extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DatasetUploadError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {self.SUPPORTED_EXTENSIONS}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise DatasetUploadError(
                f"File too large: {file_size_mb:.2f}MB. "
                f"Maximum allowed: {self.MAX_FILE_SIZE_MB}MB"
            )
        
        # Generate dataset ID
        if not dataset_id:
            dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"
        
        # Load DataFrame
        try:
            df = pd.read_csv(file_path)
            
            # Drop completely empty columns or columns with >95% missing values (e.g., trailing commas in CSV headers)
            empty_cols = df.columns[df.isnull().all()].tolist()
            mostly_empty_cols = df.columns[df.isnull().sum() / len(df) > 0.95].tolist()
            cols_to_drop = list(set(empty_cols + mostly_empty_cols))
            
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
                logger.info(f"Dropped empty columns: {cols_to_drop}")
            
            logger.info(f"Loaded CSV: {file_path} with {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            raise DatasetUploadError(f"Failed to read CSV file: {str(e)}")
        
        # Calculate file hash
        file_hash = self._calculate_hash(file_path)
        
        # Register dataset in shared dict
        self._datasets[dataset_id] = {
            'id': dataset_id,
            'name': dataset_name or path.stem,
            'filename': path.name,
            'path': str(path.absolute()),
            'hash': file_hash,
            'rows': len(df),
            'columns': list(df.columns),
            'loaded_at': datetime.utcnow().isoformat(),
            'size_mb': file_size_mb
        }
        
        return dataset_id, df
    
    def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        dataset_name: Optional[str] = None
    ) -> Tuple[str, Path]:
        """Save uploaded file content and load it.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            dataset_name: Optional name for the dataset
        
        Returns:
            Tuple of (dataset_id, file_path)
        """
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{safe_filename}"
        
        # Save file
        file_path = self.upload_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved uploaded file: {file_path}")
        
        # Load and register
        dataset_id, _ = self.load_csv(str(file_path), dataset_name)
        
        return dataset_id, file_path
    
    def _scan_uploads_dir(self):
        """Scan upload directory and demo directory to register CSV datasets."""
        dirs_to_scan = [self.upload_dir, Path("./data/demo")]
        for d in dirs_to_scan:
            if d.exists():
                for f in d.glob("*.csv"):
                    try:
                        self.load_csv(str(f))
                    except Exception:
                        pass

    def get_dataset_info(self, dataset_id: str) -> dict:
        """Get registered dataset information.
        
        Args:
            dataset_id: Dataset identifier
        
        Returns:
            Dataset metadata dictionary
        """
        if dataset_id not in self._datasets:
            self._scan_uploads_dir()
            
        if dataset_id not in self._datasets:
            raise DatasetNotFoundError(f"Dataset not found: {dataset_id}")
        return self._datasets[dataset_id].copy()
    
    def list_datasets(self) -> list:
        """List all registered datasets.
        
        Returns:
            List of dataset info dictionaries
        """
        if not self._datasets:
            self._scan_uploads_dir()
        return list(self._datasets.values())
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path separators and invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
