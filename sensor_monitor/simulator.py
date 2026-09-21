from collections.abc import Iterator
from datetime import datetime, timedelta

from .models import Measurement


def generate_transformer_measurements() -> Iterator[Measurement]:
    """Generate deterministic transformer temperatures in degrees Celsius."""
    temperatures = (
        68.0, 69.2, 68.7, 69.8, 70.1, None, 70.6, 71.0,
        71.4, 70.9, 71.2, 101.5, 73.0, 72.4, 72.0, 71.8,
        72.2, 73.1, 72.7, 73.0,
    )
    start = datetime(2026, 9, 20, 10, 0)
    for index, temperature in enumerate(temperatures):
        timestamp = (start + timedelta(minutes=5 * index)).strftime("%H:%M")
        yield Measurement(timestamp, temperature)


def generate_measurements() -> Iterator[Measurement]:
    """Backward-compatible entry point for the thermal simulator."""
    yield from generate_transformer_measurements()
