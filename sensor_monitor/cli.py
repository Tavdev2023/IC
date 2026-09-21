import argparse
import random
import sys
from typing import Optional

from .analyzer import analyze_measurements
from .csv_input import read_measurements
from .report import format_temperature, measurements_table
from .simulator import generate_measurements


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analisa medições válidas, inválidas e mudanças bruscas entre medições válidas consecutivas."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="limite absoluto para considerar uma mudança brusca (padrão: 5.0)",
    )
    parser.add_argument(
        "--input",
        metavar="ARQUIVO",
        help="CSV com colunas 'horário,valor' (use '-' para ler da entrada padrão); "
        "sem esta opção, usa o simulador térmico",
    )
    parser.add_argument(
        "--seed",
        type=int,
        metavar="N",
        help="semente do simulador; a mesma semente repete a mesma sequência "
        "(sem esta opção, a semente é perguntada no terminal)",
    )
    return parser


def ask_seed() -> Optional[int]:
    """Ask for a seed on the terminal. ``None`` means 'draw one'.

    The prompt goes to standard error so that redirecting the output of the
    program does not capture the question along with the analysis.
    """
    while True:
        print("Semente do simulador (Enter para sortear): ", end="", file=sys.stderr, flush=True)
        try:
            answer = input().strip()
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            return None

        if not answer:
            return None
        try:
            return int(answer)
        except ValueError:
            print(f"'{answer}' não é um número inteiro.", file=sys.stderr)


def resolve_seed(seed: Optional[int]) -> int:
    """Return the seed to use, asking on the terminal when none was given.

    The question is only asked when standard input is a terminal, so piped and
    automated runs draw a seed instead of waiting for an answer that never comes.
    """
    if seed is None and sys.stdin.isatty():
        seed = ask_seed()
    return random.randrange(1_000_000) if seed is None else seed


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    seed = None
    try:
        if args.input:
            measurements = read_measurements(args.input)
        else:
            seed = resolve_seed(args.seed)
            measurements = list(generate_measurements(seed))
        result = analyze_measurements(measurements, args.threshold)
    except (OSError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2

    if not args.input:
        source = f"simuladas (semente {seed})"
    elif args.input == "-":
        source = "da entrada padrão"
    else:
        source = f"de {args.input}"
    print(f"Análise das medições {source}")
    print(f"Medições válidas: {result.valid_count}")
    print(f"Medições inválidas: {result.invalid_count}")

    table = measurements_table(measurements, result)
    if table:
        print()
        print(table)
        print()

    print(f"Valor mínimo: {format_temperature(result.minimum)}")
    print(f"Valor máximo: {format_temperature(result.maximum)}")
    print(f"Valor médio: {format_temperature(result.average)}")
    print(f"Mudanças bruscas: {len(result.sudden_changes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
