"""Composable filter pipeline."""

from __future__ import annotations

from typing import Iterable, Sequence

from ..core.base import StreamingFilterBase


class FilterPipeline:
    """Run a value through a sequence of streaming filters in order."""

    def __init__(self, filters: Sequence[StreamingFilterBase]) -> None:
        self.filters = list(filters)

    def reset(self) -> None:
        for filter_instance in self.filters:
            filter_instance.reset()

    def update(self, value: float) -> float:
        result = float(value)
        for filter_instance in self.filters:
            result = filter_instance.update(result)
        return result

    def update_many(self, values: Iterable[float]) -> list[float]:
        return [self.update(value) for value in values]
