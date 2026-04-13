"""Helpers for aggregation-based windowed filters."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence

from .base import StreamingFilterBase


Aggregator = Callable[[Sequence[float]], float]


def mode_aggregate(values: Sequence[float]) -> float:
    """Return the most common value in a numeric sequence."""
    counts = Counter(float(value) for value in values)
    max_count = max(counts.values())
    winners = [value for value, count in counts.items() if count == max_count]
    return float(min(winners))


class WindowedAggregationFilter(StreamingFilterBase):
    """Apply a single aggregation function over the current sliding window."""

    def __init__(self, aggregator: Aggregator, window_size: int = 3) -> None:
        super().__init__(window_size=window_size)
        self.aggregator = aggregator

    def update(self, value: float) -> float:
        self.buffer.append(float(value))
        return float(self.aggregator(self.buffer))
