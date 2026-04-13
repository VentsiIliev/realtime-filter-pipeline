import unittest

from realtime_filter_pipeline import StreamingFilterBase, WindowedAggregationFilter


class DummyFilter(StreamingFilterBase):
    def update(self, value: float) -> float:
        self.buffer.append(float(value))
        return float(value)


class StreamingFilterBaseTests(unittest.TestCase):
    def test_rejects_non_positive_window_size(self) -> None:
        with self.assertRaises(ValueError):
            DummyFilter(window_size=0)

    def test_rejects_even_window_size(self) -> None:
        with self.assertRaises(ValueError):
            DummyFilter(window_size=4)

    def test_reset_clears_buffer(self) -> None:
        filt = DummyFilter(window_size=3)
        filt.update(1.0)
        filt.update(2.0)
        self.assertEqual(len(filt.buffer), 2)
        filt.reset()
        self.assertEqual(len(filt.buffer), 0)

    def test_window_size_setter_rebuilds_buffer(self) -> None:
        filt = DummyFilter(window_size=3)
        filt.update(1.0)
        filt.window_size = 5
        self.assertEqual(filt.window_size, 5)
        self.assertEqual(len(filt.buffer), 0)
        self.assertEqual(filt.buffer.maxlen, 5)


class WindowedAggregationFilterTests(unittest.TestCase):
    def test_uses_custom_aggregator(self) -> None:
        filt = WindowedAggregationFilter(aggregator=max, window_size=3)
        outputs = [filt.update(value) for value in [1.0, 3.0, 2.0, 4.0]]
        self.assertEqual(outputs, [1.0, 3.0, 3.0, 4.0])


if __name__ == "__main__":
    unittest.main()
