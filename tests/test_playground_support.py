import unittest

from realtime_filter_pipeline.examples.playground_support import (
    RollingHistory,
    SignalGenerator,
    SmoothingConfig,
    build_filter_pipeline,
    replay_pipeline,
)


class PlaygroundSupportTests(unittest.TestCase):
    def test_signal_generator_is_repeatable_after_reset(self) -> None:
        generator = SignalGenerator(dt=0.1, seed=3)
        values_a = [generator.next_value(noise_level=0.0) for _ in range(3)]
        generator.reset()
        values_b = [generator.next_value(noise_level=0.0) for _ in range(3)]
        self.assertEqual(values_a, values_b)

    def test_signal_generator_supports_all_named_signal_types(self) -> None:
        generator = SignalGenerator(dt=0.1, seed=3)
        signal_types = ["Composite", "Sine", "Step", "Ramp", "Spikes"]

        for signal_type in signal_types:
            generator.reset()
            values = [generator.next_value(noise_level=0.0, signal_type=signal_type) for _ in range(5)]
            self.assertEqual(len(values), 5)
            self.assertTrue(all(isinstance(value, float) for value in values))

    def test_signal_generator_repeatability_applies_to_specific_signal_type(self) -> None:
        generator = SignalGenerator(dt=0.1, seed=11)
        values_a = [generator.next_value(noise_level=0.0, signal_type="Step") for _ in range(6)]
        generator.reset()
        values_b = [generator.next_value(noise_level=0.0, signal_type="Step") for _ in range(6)]
        self.assertEqual(values_a, values_b)

    def test_build_filter_pipeline_uses_enabled_filters_only(self) -> None:
        config = SmoothingConfig(
            average_enabled=True,
            average_window=5,
            ema_enabled=False,
            median_enabled=True,
            median_window=5,
            gaussian_enabled=False,
            low_pass_enabled=False,
        )
        pipeline = build_filter_pipeline(config)
        self.assertEqual(len(pipeline.filters), 2)

    def test_replay_pipeline_matches_input_length(self) -> None:
        config = SmoothingConfig(average_enabled=True, ema_enabled=True)
        replayed = replay_pipeline([1.0, 2.0, 3.0, 4.0], config)
        self.assertEqual(len(replayed), 4)

    def test_rolling_history_reset_clears_samples(self) -> None:
        history = RollingHistory(maxlen=5)
        history.append(1.0, 1.5)
        history.append(2.0, 2.5)
        history.reset()
        self.assertEqual(len(history.raw), 0)
        self.assertEqual(len(history.filtered), 0)


if __name__ == "__main__":
    unittest.main()
