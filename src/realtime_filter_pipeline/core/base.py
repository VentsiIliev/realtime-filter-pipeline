"""Shared base class for streaming filters."""

from __future__ import annotations

from collections import deque
from typing import Deque


class StreamingFilterBase:
    """Base class for streaming filters backed by a sliding window."""

    def __init__(self, window_size: int = 3) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if window_size % 2 == 0:
            raise ValueError("window_size must be odd")
        self._window_size = window_size
        self.buffer: Deque[float] = deque(maxlen=window_size)

    @property
    def window_size(self) -> int:
        return self._window_size

    @window_size.setter
    def window_size(self, new_size: int) -> None:
        if new_size <= 0:
            raise ValueError("window_size must be positive")
        if new_size % 2 == 0:
            raise ValueError("window_size must be odd")
        self._window_size = new_size
        self.buffer = deque(maxlen=new_size)

    def reset(self) -> None:
        """Clear the internal sample buffer."""
        self.buffer.clear()

    def update(self, value: float) -> float:
        raise NotImplementedError("Subclasses must implement update().")
