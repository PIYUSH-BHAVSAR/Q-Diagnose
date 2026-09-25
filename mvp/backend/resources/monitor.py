"""Resource monitor for tracking CPU, memory, and quantum resources."""

import time
from dataclasses import dataclass
from typing import Dict, Optional

import psutil

from backend.core.logging import logger


@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    cpu_percent: float
    memory_mb: float
    peak_memory_mb: float
    elapsed_time: float
    quantum_resources: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            'cpu_percent': round(self.cpu_percent, 2),
            'memory_mb': round(self.memory_mb, 2),
            'peak_memory_mb': round(self.peak_memory_mb, 2),
            'elapsed_time': round(self.elapsed_time, 4),
            'quantum_resources': self.quantum_resources
        }


class ResourceMonitor:
    """Monitors system and quantum resources during experiments.
    
    Tracks:
    - CPU usage
    - Memory usage
    - Execution time
    - Quantum resources (qubits, shots, executions)
    """
    
    def __init__(self):
        """Initialize resource monitor."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory: float = 0.0
        self.cpu_samples: list = []
        self.process = psutil.Process()
        self.is_monitoring = False
    
    def start(self):
        """Start resource monitoring."""
        self.start_time = time.perf_counter()
        self.end_time = None
        self.peak_memory = 0.0
        self.cpu_samples = []
        self.is_monitoring = True
        
        # Record initial state
        self._sample()
        
        logger.info("Resource monitoring started")
    
    def stop(self) -> ResourceUsage:
        """Stop monitoring and get usage summary.
        
        Returns:
            ResourceUsage with summary metrics
        """
        if not self.is_monitoring:
            return ResourceUsage(0, 0, 0, 0)
        
        self.end_time = time.perf_counter()
        self.is_monitoring = False
        
        # Final sample
        self._sample()
        
        elapsed_time = self.end_time - self.start_time
        
        usage = ResourceUsage(
            cpu_percent=sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            memory_mb=self.process.memory_info().rss / (1024 * 1024),
            peak_memory_mb=self.peak_memory,
            elapsed_time=elapsed_time
        )
        
        logger.info(
            f"Resource monitoring stopped: "
            f"elapsed={elapsed_time:.2f}s, "
            f"peak_memory={self.peak_memory:.2f}MB"
        )
        
        return usage
    
    def _sample(self):
        """Take a resource sample."""
        if not self.is_monitoring:
            return
        
        # CPU
        cpu = self.process.cpu_percent()
        self.cpu_samples.append(cpu)
        
        # Memory
        memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_memory = max(self.peak_memory, memory_mb)
    
    def get_current_usage(self) -> Dict:
        """Get current resource usage.
        
        Returns:
            Dictionary with current metrics
        """
        elapsed = time.perf_counter() - self.start_time if self.start_time else 0
        
        return {
            'elapsed_time': round(elapsed, 4),
            'cpu_percent': self.process.cpu_percent(),
            'memory_mb': round(self.process.memory_info().rss / (1024 * 1024), 2),
            'peak_memory_mb': round(self.peak_memory, 2)
        }


def measure_time(func):
    """Decorator to measure function execution time.
    
    Usage:
        @measure_time
        def my_function():
            ...
    """
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        
        logger.info(f"{func.__name__} executed in {elapsed:.4f}s")
        
        return result
    
    return wrapper
