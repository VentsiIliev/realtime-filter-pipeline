"""Savitzky-Golay smoothing filter."""

from __future__ import annotations

import numpy as np

from ..core.base import StreamingFilterBase


class SavitzkyGolayFilter(StreamingFilterBase):
    """Polynomial smoothing filter that preserves local signal shape."""

    def __init__(self, window_size: int = 5, poly_order: int = 2) -> None:
        if poly_order >= window_size:
            raise ValueError("poly_order must be less than window_size")
        super().__init__(window_size=window_size)
        self.poly_order = poly_order

    def update(self, value: float) -> float:
        self.buffer.append(float(value))
        if len(self.buffer) < self.window_size:
            padded = [self.buffer[0]] * (self.window_size - len(self.buffer)) + list(self.buffer)
        else:
            padded = list(self.buffer)
        x = np.arange(len(padded), dtype=float)
        coeffs = np.polyfit(x, np.asarray(padded, dtype=float), self.poly_order)
        return float(np.polyval(coeffs, x[-1]))
