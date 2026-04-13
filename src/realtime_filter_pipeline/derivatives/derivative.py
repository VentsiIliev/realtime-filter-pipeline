"""Streaming derivative estimation filters."""

from __future__ import annotations

import time
from collections import deque
from typing import Literal

import numpy as np

from ..core.base import StreamingFilterBase


class DerivativeFilter(StreamingFilterBase):
    """Estimate first-, second-, or third-order derivatives from streaming samples."""

    def __init__(
        self,
        window_size: int = 3,
        dt: float = 1.0,
        derivative_order: Literal[1, 2, 3] = 1,
        smooth_window: int | None = None,
        use_dynamic_time: bool = False,
    ) -> None:
        if derivative_order not in (1, 2, 3):
            raise ValueError("derivative_order must be 1, 2, or 3")
        if derivative_order >= 2 and window_size < 3:
            raise ValueError("window_size must be at least 3 for second derivative")
        if derivative_order == 3 and window_size < 5:
            raise ValueError("window_size must be at least 5 for third derivative")
        super().__init__(window_size=window_size)
        self.default_dt = float(dt)
        self.derivative_order = derivative_order
        self.use_dynamic_time = use_dynamic_time
        self.timestamps: deque[float] = deque(maxlen=window_size)
        self.last_time: float | None = None
        self.smooth_buffer: deque[float] | None = deque(maxlen=smooth_window) if smooth_window else None

    def reset(self) -> None:
        super().reset()
        self.timestamps.clear()
        self.last_time = None
        if self.smooth_buffer is not None:
            self.smooth_buffer.clear()

    def update(self, value: float, timestamp: float | None = None) -> float:
        value = float(value)
        now = timestamp if timestamp is not None else time.time()
        self.buffer.append(value)
        self.timestamps.append(now)

        if len(self.buffer) < self.window_size:
            return 0.0

        data = np.asarray(self.buffer, dtype=float)
        mid = self.window_size // 2

        if self.use_dynamic_time:
            times = np.asarray(self.timestamps, dtype=float)
            dts = np.diff(times)
            dt = float(np.mean(dts)) if len(dts) > 0 else self.default_dt
        else:
            dt = self.default_dt

        if dt <= 0:
            dt = self.default_dt

        if self.derivative_order == 1:
            result = (data[mid + 1] - data[mid - 1]) / (2 * dt)
        elif self.derivative_order == 2:
            result = (data[mid - 1] - 2 * data[mid] + data[mid + 1]) / (dt**2)
        else:
            result = (
                data[mid - 2]
                - 2 * data[mid - 1]
                + 2 * data[mid + 1]
                - data[mid + 2]
            ) / (2 * dt**3)

        if self.smooth_buffer is not None:
            self.smooth_buffer.append(float(result))
            result = float(np.mean(self.smooth_buffer))

        return float(result)
