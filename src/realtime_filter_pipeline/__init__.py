"""Public package interface for realtime-filter-pipeline."""

from .core import StreamingFilterBase, WindowedAggregationFilter
from .derivatives import DerivativeFilter
from .pipeline import FilterPipeline
from .smoothing import (
    AverageFilter,
    EMAFilter,
    GaussianFilter,
    LowPassFilter,
    MedianFilter,
    ModeFilter,
    SavitzkyGolayFilter,
)

__all__ = [
    "AverageFilter",
    "DerivativeFilter",
    "EMAFilter",
    "FilterPipeline",
    "GaussianFilter",
    "LowPassFilter",
    "MedianFilter",
    "ModeFilter",
    "SavitzkyGolayFilter",
    "StreamingFilterBase",
    "WindowedAggregationFilter",
]
