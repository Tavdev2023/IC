from dataclasses import dataclass
from math import isfinite
from typing import Optional


@dataclass(frozen=True)
class Measurement:
    """A timestamped sensor measurement. ``None`` represents a missing value."""

    timestamp: str
    value: Optional[float]

    @property
    def is_valid(self) -> bool:
        """A value is valid only if it is a finite real number (not text, ``bool`` or ``None``)."""
        value = self.value
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
        )


@dataclass(frozen=True)
class SuddenChange:
    previous: Measurement
    current: Measurement
    difference: float


@dataclass(frozen=True)
class AnalysisResult:
    valid_count: int
    invalid_count: int
    minimum: Optional[float]
    maximum: Optional[float]
    average: Optional[float]
    sudden_changes: tuple[SuddenChange, ...]
