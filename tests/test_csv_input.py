import io
import unittest
from unittest import mock

import _paths

from sensor_monitor.analyzer import analyze_measurements
from sensor_monitor.csv_input import parse_measurements, read_measurements


class ParseMeasurementsTests(unittest.TestCase):
    def test_reads_header_values_and_missing_values(self):
        measurements = parse_measurements(["timestamp,value", "10:00,10.5", "10:05,", "10:10,NA"])

        self.assertEqual([m.timestamp for m in measurements], ["10:00", "10:05", "10:10"])
        self.assertEqual([m.value for m in measurements], [10.5, None, None])

    def test_header_is_optional_and_blank_lines_are_ignored(self):
        measurements = parse_measurements(["10:00,1.0", "", "  ", "10:05,2.0"])

        self.assertEqual(len(measurements), 2)

    def test_non_numeric_value_becomes_invalid_measurement(self):
        measurements = parse_measurements(["10:00,abc", "10:05,inf", "10:10,3.0"])

        self.assertEqual([m.is_valid for m in measurements], [False, False, True])

    def test_row_with_timestamp_only_has_missing_value(self):
        (measurement,) = parse_measurements(["10:00"])

        self.assertIsNone(measurement.value)

    def test_windows_line_endings_and_bom_are_accepted(self):
        measurements = parse_measurements("﻿timestamp,value\r\n10:00,1.5\r\n10:05,\r\n".splitlines(keepends=True))

        self.assertEqual([m.value for m in measurements], [1.5, None])

    def test_malformed_rows_report_the_line_number(self):
        for lines in (["10:00,1.0", "10:05,2.0,3.0"], ["10:00,1.0", ",2.0"]):
            with self.subTest(lines=lines), self.assertRaisesRegex(ValueError, "Linha 2"):
                parse_measurements(lines)

    def test_briefing_example_file(self):
        measurements = read_measurements(str(_paths.ROOT / "examples" / "exemplo_briefing.csv"))

        result = analyze_measurements(measurements, threshold=5.0)

        self.assertEqual(result.valid_count, 4)
        self.assertEqual(result.invalid_count, 1)
        self.assertEqual(result.minimum, 10.0)
        self.assertEqual(result.maximum, 18.0)
        self.assertAlmostEqual(result.average, 14.25)
        self.assertEqual(len(result.sudden_changes), 1)
        self.assertEqual(result.sudden_changes[0].previous.timestamp, "10:05")
        self.assertEqual(result.sudden_changes[0].current.timestamp, "10:15")

    def test_dash_reads_standard_input(self):
        with mock.patch("sys.stdin", io.StringIO("10:00,1.0\n10:05,2.0\n")):
            self.assertEqual(len(read_measurements("-")), 2)

    def test_missing_file_raises_os_error(self):
        with self.assertRaises(OSError):
            read_measurements(str(_paths.ROOT / "examples" / "nao_existe.csv"))


if __name__ == "__main__":
    unittest.main()
