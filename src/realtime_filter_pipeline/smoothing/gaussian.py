"""Gaussian-weighted streaming filter."""

from __future__ import annotations

import numpy as np

from ..core.base import StreamingFilterBase


class GaussianFilter(StreamingFilterBase):
    """Smooth the current window with a Gaussian kernel."""

    def __init__(self, window_size: int = 5, std_dev: float = 1.0) -> None:
        if std_dev <= 0:
            raise ValueError("std_dev must be positive")
        super().__init__(window_size=window_size)
        radius = window_size // 2
        x = np.linspace(-radius, radius, window_size)
        kernel = np.exp(-(x**2) / (2 * std_dev**2))
        self.kernel = kernel / kernel.sum()

    def update(self, value: float) -> float:
        self.buffer.append(float(value))
        data = np.array(self.buffer, dtype=float)
        if len(data) < self.window_size:
            kernel = self.kernel[-len(data):].copy()
            kernel /= kernel.sum()
            return float(np.dot(kernel, data))
        return float(np.dot(self.kernel, data))
