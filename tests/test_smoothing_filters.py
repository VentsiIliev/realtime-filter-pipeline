import unittest

import numpy as np

from realtime_filter_pipeline import (
    AverageFilter,
    EMAFilter,
    GaussianFilter,
    LowPassFilter,
    MedianFilter,
    ModeFilter,
    SavitzkyGolayFilter,
)


class AverageFilterTests(unittest.TestCase):
    def test_average_tracks_sliding_window_mean(self) -> None:
        filt = AverageFilter(window_size=3)
        outputs = [filt.update(value) for value in [1, 2, 4, 7]]
        self.assertEqual(outputs[0], 1.0)
        self.assertEqual(outputs[1], 1.5)
        self.assertAlmostEqual(outputs[2], 7 / 3)
        self.assertAlmostEqual(outputs[3], 13 / 3)


class EMAFilterTests(unittest.TestCase):
    def test_rejects_invalid_alpha(self) -> None:
        with self.assertRaises(ValueError):
            EMAFilter(alpha=0)
        with self.assertRaises(ValueError):
            EMAFilter(alpha=1.5)

    def test_ema_updates_incrementally(self) -> None:
        filt = EMAFilter(alpha=0.5)
        self.assertEqual(filt.update(10), 10.0)
        self.assertEqual(filt.update(14), 12.0)
        self.assertEqual(filt.update(18), 15.0)

    def test_reset_clears_previous_ema(self) -> None:
        filt = EMAFilter(alpha=0.5)
        filt.update(10)
        filt.update(14)
        filt.reset()
        self.assertEqual(filt.update(5), 5.0)


class MedianAndModeFilterTests(unittest.TestCase):
    def test_median_filter_reduces_spike(self) -> None:
        filt = MedianFilter(window_size=3)
        outputs = [filt.update(value) for value in [2, 80, 6, 3, 100]]
        self.assertEqual(outputs[-1], 6.0)

    def test_mode_filter_returns_most_common_value(self) -> None:
        filt = ModeFilter(window_size=5)
        outputs = [filt.update(value) for value in [2, 2, 3, 3, 3, 2, 1]]
        self.assertEqual(outputs[0], 2.0)
        self.assertEqual(outputs[4], 3.0)
        self.assertEqual(outputs[-1], 3.0)


class WeightedFilterTests(unittest.TestCase):
    def test_gaussian_rejects_invalid_std_dev(self) -> None:
        with self.assertRaises(ValueError):
            GaussianFilter(window_size=5, std_dev=0)

    def test_gaussian_kernel_is_normalized(self) -> None:
        filt = GaussianFilter(window_size=5, std_dev=1.0)
        self.assertAlmostEqual(float(np.sum(filt.kernel)), 1.0)

    def test_low_pass_normalizes_custom_kernel(self) -> None:
        filt = LowPassFilter(window_size=3, kernel=[1, 2, 1])
        np.testing.assert_allclose(filt.kernel, np.array([0.25, 0.5, 0.25]))

    def test_low_pass_rejects_bad_kernel_length(self) -> None:
        with self.assertRaises(ValueError):
            LowPassFilter(window_size=3, kernel=[1, 1])

    def test_low_pass_rejects_zero_sum_kernel(self) -> None:
        filt = LowPassFilter(window_size=3)
        with self.assertRaises(ValueError):
            filt.set_kernel([0, 0, 0])

    def test_low_pass_window_size_reset_rebuilds_uniform_kernel(self) -> None:
        filt = LowPassFilter(window_size=3, kernel=[1, 2, 1])
        filt.window_size = 5
        np.testing.assert_allclose(filt.kernel, np.ones(5) / 5)

    def test_low_pass_partial_window_returns_weighted_output(self) -> None:
        filt = LowPassFilter(window_size=3, kernel=[1, 2, 1])
        self.assertAlmostEqual(filt.update(10), 10.0)
        self.assertAlmostEqual(filt.update(20), (2 / 3) * 10 + (1 / 3) * 20)


class SavitzkyGolayFilterTests(unittest.TestCase):
    def test_rejects_poly_order_not_less_than_window(self) -> None:
        with self.assertRaises(ValueError):
            SavitzkyGolayFilter(window_size=5, poly_order=5)

    def test_preserves_linear_ramp_after_startup(self) -> None:
        filt = SavitzkyGolayFilter(window_size=5, poly_order=2)
        outputs = [filt.update(value) for value in [1, 2, 3, 4, 5, 6]]
        self.assertAlmostEqual(outputs[-1], 6.0, places=6)


if __name__ == "__main__":
    unittest.main()
