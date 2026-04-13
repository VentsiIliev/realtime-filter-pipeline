"""Median filter for streaming numeric samples."""

from __future__ import annotations

import numpy as np

from ..core.aggregations import WindowedAggregationFilter


class MedianFilter(WindowedAggregationFilter):
    """Return the median of the current sliding window."""

    def __init__(self, window_size: int = 3) -> None:
        super().__init__(aggregator=np.median, window_size=window_size)
