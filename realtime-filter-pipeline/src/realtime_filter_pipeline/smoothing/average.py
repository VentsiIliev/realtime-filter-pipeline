"""Simple moving-average filter."""

from __future__ import annotations

import numpy as np

from ..core.aggregations import WindowedAggregationFilter


class AverageFilter(WindowedAggregationFilter):
    """Return the arithmetic mean of the current sliding window."""

    def __init__(self, window_size: int = 3) -> None:
        super().__init__(aggregator=np.mean, window_size=window_size)
