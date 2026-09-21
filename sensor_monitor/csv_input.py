import csv
import sys
from collections.abc import Iterable
from pathlib import Path

from .models import Measurement

_HEADER_NAMES = {"timestamp", "horario", "horário", "hora"}
_MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-"}


def _parse_value(text: str):
    """Return the float in ``text``, or ``None`` when it is missing or not numeric."""
    text = text.strip()
    if text.lower() in _MISSING_TOKENS:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_measurements(lines: Iterable[str]) -> list[Measurement]:
    """Parse ``timestamp,value`` rows.

    A header row and blank lines are ignored. A missing or non-numeric value
    becomes an invalid measurement; a row without a timestamp or with more than
    two columns is a format error.
    """
    reader = csv.reader(lines)
    measurements: list[Measurement] = []
    seen_row = False
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue

        timestamp = row[0].lstrip("﻿").strip()
        if not seen_row:
            seen_row = True
            if timestamp.lower() in _HEADER_NAMES:
                continue
        if not timestamp or len(row) > 2:
            raise ValueError(
                f"Linha {reader.line_num}: esperado 'horário,valor', recebido {','.join(row)!r}."
            )

        value = _parse_value(row[1]) if len(row) == 2 else None
        measurements.append(Measurement(timestamp, value))
    return measurements


def read_measurements(source: str) -> list[Measurement]:
    """Read measurements from a CSV file path, or from standard input when ``source`` is ``-``."""
    if source == "-":
        return parse_measurements(sys.stdin)
    with Path(source).open(encoding="utf-8-sig", newline="") as file:
        return parse_measurements(file)
