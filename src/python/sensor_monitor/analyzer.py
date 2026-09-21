from collections.abc import Iterable
from math import isfinite

from .models import AnalysisResult, Measurement, SuddenChange


def analyze_measurements(
    measurements: Iterable[Measurement], threshold: float
) -> AnalysisResult:
    """Summarize measurements and find changes greater than ``threshold``.

    Invalid records are counted but excluded from statistics. They also do not
    reset the comparison: consecutive valid measurements may have invalid
    records between them.
    """
    if not isfinite(threshold) or threshold < 0:
        raise ValueError("O limite deve ser um número finito maior ou igual a zero.")

    measurements = list(measurements)
    valid_measurements = [measurement for measurement in measurements if measurement.is_valid]
    invalid_count = len(measurements) - len(valid_measurements)
    values = [measurement.value for measurement in valid_measurements]

    sudden_changes: list[SuddenChange] = []
    for previous, current in zip(valid_measurements, valid_measurements[1:]):
        difference = abs(current.value - previous.value)
        if difference > threshold:
            sudden_changes.append(SuddenChange(previous, current, difference))

    return AnalysisResult(
        valid_count=len(valid_measurements),
        invalid_count=invalid_count,
        minimum=min(values) if values else None,
        maximum=max(values) if values else None,
        average=sum(values) / len(values) if values else None,
        sudden_changes=tuple(sudden_changes),
    )
