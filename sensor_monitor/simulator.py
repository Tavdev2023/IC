import random
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Optional

from .models import Measurement

READING_COUNT = 20
INTERVAL_MINUTES = 5
BASE_RANGE = (66.0, 72.0)
DRIFT_DEVIATION = 0.6
MISSING_CHANCE = 0.08
SPIKE_CHANCE = 0.08
SPIKE_RANGE = (20.0, 35.0)


def generate_transformer_measurements(seed: Optional[int] = None) -> Iterator[Measurement]:
    """Generate simulated transformer temperatures in degrees Celsius.

    Each reading drifts slightly from the previous one. A reading may be
    missing, or carry a transient spike that does not move the baseline, so the
    temperature returns to its earlier level right after a spike.

    Without ``seed`` every run differs. The same ``seed`` always reproduces the
    same sequence.
    """
    rng = random.Random(seed)
    start = datetime(2026, 9, 20, 10, 0)
    temperature = rng.uniform(*BASE_RANGE)

    for index in range(READING_COUNT):
        timestamp = (start + timedelta(minutes=INTERVAL_MINUTES * index)).strftime("%H:%M")
        if rng.random() < MISSING_CHANCE:
            yield Measurement(timestamp, None)
            continue

        temperature += rng.gauss(0.0, DRIFT_DEVIATION)
        reading = temperature
        if rng.random() < SPIKE_CHANCE:
            reading += rng.uniform(*SPIKE_RANGE)
        yield Measurement(timestamp, round(reading, 1))


def generate_measurements(seed: Optional[int] = None) -> Iterator[Measurement]:
    """Backward-compatible entry point for the thermal simulator."""
    yield from generate_transformer_measurements(seed)
