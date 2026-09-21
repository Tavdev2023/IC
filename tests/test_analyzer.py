import unittest

import _paths  # noqa: F401

from sensor_monitor.analyzer import analyze_measurements
from sensor_monitor.models import Measurement
from sensor_monitor.simulator import generate_measurements


class AnalyzeMeasurementsTests(unittest.TestCase):
    def test_counts_statistics_and_sudden_changes(self):
        result = analyze_measurements(generate_measurements(), threshold=10.0)

        self.assertEqual(result.valid_count, 19)
        self.assertEqual(result.invalid_count, 1)
        self.assertEqual(result.minimum, 68.0)
        self.assertEqual(result.maximum, 101.5)
        self.assertAlmostEqual(result.average, 72.77, places=2)
        self.assertEqual(len(result.sudden_changes), 2)
        self.assertEqual(result.sudden_changes[0].previous.timestamp, "10:50")
        self.assertEqual(result.sudden_changes[0].current.timestamp, "10:55")
        self.assertEqual(result.sudden_changes[1].current.timestamp, "11:00")

    def test_invalid_measurement_is_skipped_between_valid_measurements(self):
        measurements = [
            Measurement("10:00", 10.0),
            Measurement("10:05", None),
            Measurement("10:10", 12.0),
        ]

        result = analyze_measurements(measurements, threshold=2.0)

        self.assertEqual(result.valid_count, 2)
        self.assertEqual(result.invalid_count, 1)
        self.assertEqual(len(result.sudden_changes), 0)

    def test_change_across_an_invalid_measurement_is_detected(self):
        measurements = [
            Measurement("10:00", 10.0),
            Measurement("10:05", None),
            Measurement("10:10", 20.0),
        ]

        result = analyze_measurements(measurements, threshold=5.0)

        self.assertEqual(len(result.sudden_changes), 1)
        self.assertEqual(result.sudden_changes[0].previous.timestamp, "10:00")
        self.assertEqual(result.sudden_changes[0].current.timestamp, "10:10")

    def test_difference_equal_to_threshold_is_not_a_sudden_change(self):
        measurements = [Measurement("10:00", 10.0), Measurement("10:05", 15.0)]

        self.assertEqual(len(analyze_measurements(measurements, threshold=5.0).sudden_changes), 0)
        self.assertEqual(len(analyze_measurements(measurements, threshold=4.99).sudden_changes), 1)

    def test_drop_is_detected_as_absolute_difference(self):
        measurements = [Measurement("10:00", 20.0), Measurement("10:05", 10.0)]

        result = analyze_measurements(measurements, threshold=5.0)

        self.assertEqual(len(result.sudden_changes), 1)
        self.assertEqual(result.sudden_changes[0].difference, 10.0)

    def test_nan_and_infinite_values_are_invalid(self):
        measurements = [
            Measurement("10:00", 10.0),
            Measurement("10:05", float("nan")),
            Measurement("10:10", float("inf")),
            Measurement("10:15", 11.0),
        ]

        result = analyze_measurements(measurements, threshold=5.0)

        self.assertEqual(result.valid_count, 2)
        self.assertEqual(result.invalid_count, 2)
        self.assertEqual(result.maximum, 11.0)

    def test_non_numeric_values_are_invalid_instead_of_raising(self):
        for value in ("abc", "12", True, [1.0]):
            with self.subTest(value=value):
                self.assertFalse(Measurement("10:00", value).is_valid)

    def test_empty_valid_set_has_no_statistics(self):
        result = analyze_measurements([Measurement("10:00", None)], threshold=1.0)

        self.assertEqual(result.valid_count, 0)
        self.assertEqual(result.invalid_count, 1)
        self.assertIsNone(result.minimum)
        self.assertIsNone(result.maximum)
        self.assertIsNone(result.average)
        self.assertEqual(result.sudden_changes, ())

    def test_single_valid_measurement_has_no_sudden_change(self):
        result = analyze_measurements([Measurement("10:00", 10.0)], threshold=0.0)

        self.assertEqual(result.valid_count, 1)
        self.assertEqual(result.sudden_changes, ())

    def test_invalid_threshold_is_rejected(self):
        for threshold in (-1.0, float("nan"), float("inf")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                analyze_measurements([], threshold=threshold)


if __name__ == "__main__":
    unittest.main()
