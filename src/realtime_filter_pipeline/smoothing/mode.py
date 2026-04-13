"""Mode filter for streaming numeric samples."""

from __future__ import annotations

from ..core.aggregations import WindowedAggregationFilter, mode_aggregate


class ModeFilter(WindowedAggregationFilter):
    """Return the most common value in the current sliding window."""

    def __init__(self, window_size: int = 3) -> None:
        super().__init__(aggregator=mode_aggregate, window_size=window_size)
