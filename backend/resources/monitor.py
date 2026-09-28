"""
backend/resources/monitor.py
Owner: Piyush
Phase: 10

ResourceMonitor — CPU, RAM, and time tracking during model execution.
From guide_piyush.md §2 + phase10.md §28-29:
    - time.perf_counter() for timing
    - psutil for memory
    - Track peak memory (not just delta — full experiment peak)

Usage as context manager:
    with ResourceMonitor() as monitor:
        model.fit(X_train, y_train)
    print(monitor.elapsed_seconds, monitor.peak_memory_mb)
"""

from __future__ import annotations

import os
import time
from typing import Optional

import psutil


class ResourceMonitor:
    """
    Lightweight resource tracker for model training phases.

    Can be used as:
        1. Context manager (with statement) — automatic start/stop
        2. Manual start() / stop() calls

    Tracked:
        - Wall-clock elapsed time (perf_counter)
        - Peak RSS memory during the monitored period
        - CPU usage % (at stop time)
    """

    def __init__(self) -> None:
        self._proc = psutil.Process(os.getpid())
        self._start_time: Optional[float] = None
        self._start_mem: float = 0.0
        self._peak_mem: float = 0.0
        self._elapsed: float = 0.0
        self._cpu_percent: float = 0.0
        self._running = False

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "ResourceMonitor":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    # ── Manual control ────────────────────────────────────────────────────────

    def start(self) -> None:
        self._start_time = time.perf_counter()
        self._start_mem = self._proc.memory_info().rss / (1024 * 1024)
        self._peak_mem = self._start_mem
        self._running = True
        # Trigger CPU measurement baseline
        self._proc.cpu_percent(interval=None)

    def snapshot(self) -> float:
        """Record current memory; update peak. Returns current RSS in MB."""
        if not self._running:
            return 0.0
        current_mb = self._proc.memory_info().rss / (1024 * 1024)
        if current_mb > self._peak_mem:
            self._peak_mem = current_mb
        return current_mb

    def stop(self) -> None:
        if not self._running:
            return
        self._elapsed = time.perf_counter() - self._start_time
        self.snapshot()   # final snapshot for peak
        self._cpu_percent = self._proc.cpu_percent(interval=None)
        self._running = False

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def elapsed_seconds(self) -> float:
        """Total wall-clock seconds elapsed."""
        if self._running:
            return time.perf_counter() - self._start_time
        return self._elapsed

    @property
    def peak_memory_mb(self) -> float:
        """Peak RSS memory during the monitored period (MB)."""
        return round(max(self._peak_mem - self._start_mem, 0.0), 2)

    @property
    def cpu_percent(self) -> float:
        """CPU usage % at stop time."""
        return self._cpu_percent

    def to_dict(self) -> dict:
        """JSON-serialisable resource summary."""
        return {
            "elapsed_seconds":  round(self.elapsed_seconds, 4),
            "peak_memory_mb":   self.peak_memory_mb,
            "cpu_percent":      round(self._cpu_percent, 1),
        }
