from __future__ import annotations

import argparse
from pathlib import Path

from .analyzer import CapacityAnalyzer, parse_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisa pacotes, pessoas, forecast e capacidade.")
    parser.add_argument("csv", type=Path, help="Arquivo CSV com período, pacotes e pessoas.")
    parser.add_argument("--question", "-q", help="Pergunta em linguagem natural sobre a análise.")
    args = parser.parse_args()

    points = parse_csv(args.csv.read_text(encoding="utf-8"))
    analyzer = CapacityAnalyzer(points)
    if args.question:
        print(analyzer.answer(args.question))
    else:
        print(analyzer.analyze().to_markdown())


if __name__ == "__main__":
    main()
