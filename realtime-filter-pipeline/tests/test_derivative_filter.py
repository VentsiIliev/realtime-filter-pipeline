import unittest

from realtime_filter_pipeline import DerivativeFilter


class DerivativeFilterTests(unittest.TestCase):
    def test_rejects_invalid_derivative_order(self) -> None:
        with self.assertRaises(ValueError):
            DerivativeFilter(derivative_order=4)

    def test_rejects_small_window_for_second_derivative(self) -> None:
        with self.assertRaises(ValueError):
            DerivativeFilter(window_size=1, derivative_order=2)

    def test_rejects_small_window_for_third_derivative(self) -> None:
        with self.assertRaises(ValueError):
            DerivativeFilter(window_size=3, derivative_order=3)

    def test_first_derivative_of_linear_signal_is_constant(self) -> None:
        filt = DerivativeFilter(window_size=3, dt=1.0, derivative_order=1)
        outputs = [filt.update(v, timestamp=float(i)) for i, v in enumerate([0.0, 1.0, 2.0])]
        self.assertEqual(outputs[-1], 1.0)

    def test_second_derivative_of_quadratic_signal_is_constant(self) -> None:
        filt = DerivativeFilter(window_size=3, dt=1.0, derivative_order=2)
        samples = [0.0, 1.0, 4.0]
        outputs = [filt.update(v, timestamp=float(i)) for i, v in enumerate(samples)]
        self.assertEqual(outputs[-1], 2.0)

    def test_third_derivative_of_cubic_signal_is_constant(self) -> None:
        filt = DerivativeFilter(window_size=5, dt=1.0, derivative_order=3)
        samples = [0.0, 1.0, 8.0, 27.0, 64.0]
        outputs = [filt.update(v, timestamp=float(i)) for i, v in enumerate(samples)]
        self.assertEqual(outputs[-1], -6.0)

    def test_smoothing_window_averages_derivative_outputs(self) -> None:
        filt = DerivativeFilter(window_size=3, dt=1.0, derivative_order=1, smooth_window=2)
        outputs = [filt.update(v, timestamp=float(i)) for i, v in enumerate([0.0, 1.0, 2.0, 4.0])]
        self.assertEqual(outputs[2], 1.0)
        self.assertEqual(outputs[3], 1.25)

    def test_reset_clears_runtime_state(self) -> None:
        filt = DerivativeFilter(window_size=3, dt=1.0, derivative_order=1, smooth_window=2, use_dynamic_time=True)
        filt.update(0.0, timestamp=0.0)
        filt.update(1.0, timestamp=1.0)
        filt.reset()
        self.assertEqual(len(filt.buffer), 0)
        self.assertEqual(len(filt.timestamps), 0)
        self.assertIsNone(filt.last_time)
        self.assertEqual(len(filt.smooth_buffer), 0)


if __name__ == "__main__":
    unittest.main()
