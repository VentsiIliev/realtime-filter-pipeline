import unittest

from realtime_filter_pipeline import AverageFilter, FilterPipeline, MedianFilter


class FilterPipelineTests(unittest.TestCase):
    def test_pipeline_composes_filters(self) -> None:
        pipeline = FilterPipeline([MedianFilter(window_size=3), AverageFilter(window_size=3)])
        values = pipeline.update_many([1, 10, 2, 3])
        self.assertEqual(len(values), 4)
        self.assertGreater(values[-1], values[0])

    def test_pipeline_reset_resets_all_filters(self) -> None:
        first = AverageFilter(window_size=3)
        second = MedianFilter(window_size=3)
        pipeline = FilterPipeline([first, second])
        pipeline.update_many([1, 2, 3])
        pipeline.reset()
        self.assertEqual(len(first.buffer), 0)
        self.assertEqual(len(second.buffer), 0)


if __name__ == "__main__":
    unittest.main()
