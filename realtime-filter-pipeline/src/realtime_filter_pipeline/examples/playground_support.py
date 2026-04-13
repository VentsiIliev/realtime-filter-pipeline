"""Support code for the interactive filter playground."""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass
from typing import Iterable

from realtime_filter_pipeline import (
    AverageFilter,
    EMAFilter,
    FilterPipeline,
    GaussianFilter,
    LowPassFilter,
    MedianFilter,
)


@dataclass
class SmoothingConfig:
    average_enabled: bool = True
    average_window: int = 5
    ema_enabled: bool = True
    ema_alpha: float = 0.2
    median_enabled: bool = False
    median_window: int = 5
    gaussian_enabled: bool = False
    gaussian_window: int = 5
    gaussian_std_dev: float = 1.0
    low_pass_enabled: bool = False
    low_pass_window: int = 5
    signal_type: str = "Composite"


class SignalGenerator:
    """Generate a repeatable noisy data stream for UI demos."""

    def __init__(self, dt: float = 0.05, seed: int = 7) -> None:
        self.dt = dt
        self.rng = random.Random(seed)
        self.t = 0.0

    def reset(self) -> None:
        self.t = 0.0

    def next_value(self, noise_level: float = 0.2, signal_type: str = "Composite") -> float:
        value = self._base_signal(signal_type)
        noise = self.rng.gauss(0.0, noise_level)
        self.t += self.dt
        return value + noise

    def _base_signal(self, signal_type: str) -> float:
        if signal_type == "Sine":
            return 1.1 * math.sin(self.t * 1.25)
        if signal_type == "Step":
            if self.t < 2.0:
                return 0.15
            if self.t < 5.0:
                return 1.2
            return 0.55
        if signal_type == "Ramp":
            cycle = self.t % 8.0
            if cycle < 4.0:
                return -0.8 + 0.45 * cycle
            return 1.0 - 0.45 * (cycle - 4.0)
        if signal_type == "Spikes":
            base = 0.45 * math.sin(self.t * 0.8)
            cycle = self.t % 3.2
            spike = 1.35 if 0.0 <= cycle < 0.18 else 0.0
            return base + spike

        base = 0.85 * math.sin(self.t * 1.15)
        harmonic = 0.28 * math.sin(self.t * 2.9 + 0.5)
        drift = 0.015 * self.t
        step = 0.7 if self.t >= 6.0 else 0.0
        return base + harmonic + drift + step


def _odd(value: int) -> int:
    value = max(1, int(value))
    return value if value % 2 == 1 else value + 1


def build_filter_pipeline(config: SmoothingConfig) -> FilterPipeline:
    """Build a filter pipeline from the current UI configuration."""
    filters = []

    if config.average_enabled:
        filters.append(AverageFilter(window_size=_odd(config.average_window)))
    if config.ema_enabled:
        filters.append(EMAFilter(alpha=float(config.ema_alpha)))
    if config.median_enabled:
        filters.append(MedianFilter(window_size=_odd(config.median_window)))
    if config.gaussian_enabled:
        filters.append(
            GaussianFilter(
                window_size=_odd(config.gaussian_window),
                std_dev=float(config.gaussian_std_dev),
            )
        )
    if config.low_pass_enabled:
        filters.append(LowPassFilter(window_size=_odd(config.low_pass_window)))

    return FilterPipeline(filters)


def replay_pipeline(values: Iterable[float], config: SmoothingConfig) -> list[float]:
    """Recompute filtered history after the user changes filter settings."""
    pipeline = build_filter_pipeline(config)
    return pipeline.update_many(values)


class RollingHistory:
    """Keep raw and filtered samples aligned for plotting."""

    def __init__(self, maxlen: int = 240) -> None:
        self.raw = deque(maxlen=maxlen)
        self.filtered = deque(maxlen=maxlen)

    def append(self, raw_value: float, filtered_value: float) -> None:
        self.raw.append(float(raw_value))
        self.filtered.append(float(filtered_value))

    def reset(self) -> None:
        self.raw.clear()
        self.filtered.clear()
