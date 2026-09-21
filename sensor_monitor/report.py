from collections.abc import Sequence
from typing import Optional

from .models import AnalysisResult, Measurement


def format_value(value: Optional[float]) -> str:
    return "sem dados" if value is None else f"{value:.2f}"


def format_temperature(value: Optional[float]) -> str:
    """Format a temperature in degrees Celsius, or ``sem dados`` when missing."""
    return "sem dados" if value is None else f"{value:.2f} °C"


def measurements_table(
    measurements: Sequence[Measurement], result: AnalysisResult
) -> str:
    """One line per measurement, flagging sudden changes where they happen.

    The flag goes on the later of the two measurements compared, which is the
    one whose reading moved beyond the threshold.
    """
    if not measurements:
        return ""

    notes = {
        id(change.current): f"mudança brusca ({change.difference:.2f} °C)"
        for change in result.sudden_changes
    }
    values = [
        format_temperature(measurement.value if measurement.is_valid else None)
        for measurement in measurements
    ]
    time_width = max([len("Horário")] + [len(m.timestamp) for m in measurements])
    value_width = max([len("Valor")] + [len(value) for value in values])

    header = f"{'Horário':<{time_width}}  {'Valor':>{value_width}}"
    separator = f"{'-' * time_width}  {'-' * value_width}"
    if notes:
        note_width = max([len("Observação")] + [len(note) for note in notes.values()])
        header = f"{header}  Observação"
        separator = f"{separator}  {'-' * note_width}"

    lines = [header, separator]
    for measurement, value in zip(measurements, values):
        row = f"{measurement.timestamp:<{time_width}}  {value:>{value_width}}"
        note = notes.get(id(measurement))
        lines.append(f"{row}  {note}" if note else row)
    return "\n".join(lines)


def summary_text(result: AnalysisResult) -> str:
    """One-line summary shown by the graphical interface."""
    return (
        f"Válidas: {result.valid_count} | Inválidas: {result.invalid_count} | "
        f"Mín: {format_value(result.minimum)} | Máx: {format_value(result.maximum)} | "
        f"Média: {format_value(result.average)} | Mudanças bruscas: {len(result.sudden_changes)}"
    )
