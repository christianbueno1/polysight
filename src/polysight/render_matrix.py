"""Renderiza una matriz normalizada desde conteos CSV ya calculados."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import load_confusion_matrix_csv, save_normalized_confusion_matrix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="confusion-matrix.csv")
    parser.add_argument("--output", type=Path, help="PNG de salida")
    parser.add_argument(
        "--annotation-threshold",
        type=float,
        default=0.02,
        help="Ocultar texto fuera de la diagonal por debajo de esta proporción (default: 0.02)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    matrix, class_names = load_confusion_matrix_csv(args.input)
    output = args.output or args.input.with_name("confusion-matrix-normalized-readable.png")
    save_normalized_confusion_matrix(
        output,
        matrix,
        class_names,
        annotation_threshold=args.annotation_threshold,
    )
    print(
        json.dumps(
            {"classes": len(class_names), "input": str(args.input), "output": str(output)},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
