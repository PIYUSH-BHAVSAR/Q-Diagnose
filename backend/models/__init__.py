"""
backend/models/__init__.py
Owner: Piyush
Re-exports ModelResult so teammates can do:
    from backend.models import ModelResult
"""
from backend.models.result import ModelResult

__all__ = ["ModelResult"]
