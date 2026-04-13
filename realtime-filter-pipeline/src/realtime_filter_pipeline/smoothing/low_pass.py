"""Weighted FIR-style low-pass streaming filter."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from ..core.base import StreamingFilterBase


class LowPassFilter(StreamingFilterBase):
    """Apply a normalized kernel over the current sliding window."""

    def __init__(self, window_size: int = 3, kernel: Sequence[float] | None = None) -> None:
        super().__init__(window_size=window_size)
        self.kernel = self._normalize_kernel(kernel if kernel is not None else np.ones(window_size))

    @StreamingFilterBase.window_size.setter
    def window_size(self, new_size: int) -> None:
        StreamingFilterBase.window_size.fset(self, new_size)
        self.kernel = np.ones(new_size, dtype=float) / new_size

    def _normalize_kernel(self, kernel: Sequence[float]) -> np.ndarray:
        array = np.asarray(kernel, dtype=float)
        if len(array) != self.window_size:
            raise ValueError("kernel length must equal window_size")
        total = array.sum()
        if total == 0:
            raise ValueError("kernel sum must be non-zero")
        return array / total

    def set_kernel(self, kernel: Sequence[float]) -> None:
        self.kernel = self._normalize_kernel(kernel)

    def update(self, value: float) -> float:
        self.buffer.append(float(value))
        data = np.array(self.buffer, dtype=float)
        if len(data) < self.window_size:
            kernel = self.kernel[-len(data):].copy()
            kernel /= kernel.sum()
            return float(np.dot(kernel, data))
        return float(np.dot(self.kernel, data))
