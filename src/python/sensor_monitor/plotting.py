from collections.abc import Sequence

from .models import AnalysisResult, Measurement


def _valid_measurements(measurements: Sequence[Measurement]) -> list[Measurement]:
    return [measurement for measurement in measurements if measurement.is_valid]


def draw_dashboard(axes, measurements: Sequence[Measurement], result: AnalysisResult) -> None:
    """Draw the time series and distribution charts on supplied Matplotlib axes.

    ``result`` must come from analyzing the same ``measurements`` objects: sudden
    changes are matched by identity, so repeated timestamps are not confused.
    """
    valid = _valid_measurements(measurements)
    axes[0].clear()
    axes[1].clear()

    timestamps = [measurement.timestamp for measurement in valid]
    values = [measurement.value for measurement in valid]
    sudden = {id(change.current) for change in result.sudden_changes}
    colors = ["#ef8354" if id(measurement) in sudden else "#2d6a4f" for measurement in valid]

    axes[0].plot(timestamps, values, color="#264653", linewidth=2, marker="o")
    axes[0].scatter(timestamps, values, color=colors, zorder=3)
    axes[0].set_title("Temperatura do transformador")
    axes[0].set_ylabel("Temperatura (°C)")
    axes[0].set_xlabel("Horário")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(alpha=0.25)

    axes[1].boxplot(
        values,
        orientation="vertical",
        patch_artist=True,
        boxprops={"facecolor": "#90be6d"},
        flierprops={"marker": "o", "markerfacecolor": "#ef8354", "markersize": 8},
    )
    axes[1].set_title("Distribuição das temperaturas")
    axes[1].set_ylabel("Temperatura (°C)")
    axes[1].set_xticks([1], ["Leituras válidas"])
    axes[1].grid(axis="y", alpha=0.25)
