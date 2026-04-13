"""Exponential moving-average filter."""

from __future__ import annotations

from typing import Optional

from ..core.base import StreamingFilterBase


class EMAFilter(StreamingFilterBase):
    """Exponentially weighted smoother for streaming data."""

    def __init__(self, alpha: float = 0.1) -> None:
        if not (0 < alpha <= 1):
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = alpha
        self.prev_ema: Optional[float] = None
        super().__init__(window_size=1)

    def reset(self) -> None:
        super().reset()
        self.prev_ema = None

    def update(self, value: float) -> float:
        value = float(value)
        if self.prev_ema is None:
            self.prev_ema = value
        else:
            self.prev_ema = self.alpha * value + (1 - self.alpha) * self.prev_ema
        return self.prev_ema
