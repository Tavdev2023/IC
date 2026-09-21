import argparse
import sys
from typing import Optional

from sensor_monitor.analyzer import analyze_measurements
from sensor_monitor.csv_input import read_measurements
from sensor_monitor.report import format_value
from sensor_monitor.simulator import generate_measurements


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analisa medições válidas, inválidas e mudanças bruscas entre medições válidas consecutivas."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        required=True,
        help="limite absoluto para considerar uma mudança brusca",
    )
    parser.add_argument(
        "--input",
        metavar="ARQUIVO",
        help="CSV com colunas 'horário,valor' (use '-' para ler da entrada padrão); "
        "sem esta opção, usa o simulador térmico",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        measurements = read_measurements(args.input) if args.input else list(generate_measurements())
        result = analyze_measurements(measurements, args.threshold)
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    source = "simuladas" if not args.input else "da entrada padrão" if args.input == "-" else f"de {args.input}"
    print(f"Análise das medições {source}")
    print(f"Medições válidas: {result.valid_count}")
    print(f"Medições inválidas: {result.invalid_count}")
    print(f"Valor mínimo: {format_value(result.minimum)}")
    print(f"Valor máximo: {format_value(result.maximum)}")
    print(f"Valor médio: {format_value(result.average)}")
    print(f"Mudanças bruscas: {len(result.sudden_changes)}")
    for change in result.sudden_changes:
        print(
            f"- {change.previous.timestamp} -> {change.current.timestamp}: "
            f"diferença absoluta {change.difference:.2f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
