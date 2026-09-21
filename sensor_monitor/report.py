from typing import Optional

from .models import AnalysisResult


def format_value(value: Optional[float]) -> str:
    return "sem dados" if value is None else f"{value:.2f}"


def summary_text(result: AnalysisResult) -> str:
    """One-line summary shown by the graphical interface."""
    return (
        f"Válidas: {result.valid_count} | Inválidas: {result.invalid_count} | "
        f"Mín: {format_value(result.minimum)} | Máx: {format_value(result.maximum)} | "
        f"Média: {format_value(result.average)} | Mudanças bruscas: {len(result.sudden_changes)}"
    )
