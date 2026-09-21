import unittest
import warnings

import _paths  # noqa: F401

from matplotlib.figure import Figure

from sensor_monitor.analyzer import analyze_measurements
from sensor_monitor.models import Measurement
from sensor_monitor.plotting import draw_dashboard
from sensor_monitor.report import summary_text
from sensor_monitor.simulator import generate_measurements

SUDDEN_COLOR = "#ef8354"


def draw(measurements, threshold):
    axes = Figure().subplots(1, 2)
    result = analyze_measurements(measurements, threshold)
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # deprecated Matplotlib arguments must not creep back in
        draw_dashboard(axes, measurements, result)
    return axes, result


def point_colors(axes):
    (collection,) = axes[0].collections
    return [tuple(round(channel, 3) for channel in color) for color in collection.get_facecolors()]


class DrawDashboardTests(unittest.TestCase):
    def test_draws_time_series_and_box_plot_from_valid_measurements(self):
        axes, _ = draw(list(generate_measurements()), threshold=10.0)

        (line,) = axes[0].lines
        self.assertEqual(len(line.get_xdata()), 19)
        self.assertEqual(len(axes[1].patches), 1)  # the box
        self.assertEqual(max(flier.get_ydata().max() for flier in axes[1].lines if len(flier.get_ydata())), 101.5)

    def test_sudden_changes_are_highlighted_by_identity(self):
        # Repeated timestamps must not highlight the wrong point.
        measurements = [
            Measurement("10:00", 10.0),
            Measurement("10:00", 50.0),
            Measurement("10:05", 50.5),
        ]

        axes, _ = draw(measurements, threshold=10.0)

        colors = point_colors(axes)
        highlighted = [index for index, color in enumerate(colors) if color != colors[0]]
        self.assertEqual(highlighted, [1])

    def test_draws_without_valid_measurements(self):
        axes, result = draw([Measurement("10:00", None)], threshold=1.0)

        self.assertEqual(len(axes[0].lines[0].get_xdata()), 0)
        self.assertIn("Mín: sem dados", summary_text(result))


class SummaryTextTests(unittest.TestCase):
    def test_includes_min_max_and_average(self):
        _, result = draw(list(generate_measurements()), threshold=10.0)

        text = summary_text(result)

        for expected in ("Válidas: 19", "Inválidas: 1", "Mín: 68.00", "Máx: 101.50", "Média: 72.77", "Mudanças bruscas: 2"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
