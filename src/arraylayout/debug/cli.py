"""Tiny developer CLI to print debug pipeline stages for a spec JSON file."""

from __future__ import annotations

import argparse
from pathlib import Path

from .helpers import (
    debug_grid_classification,
    debug_layout,
    debug_layout_skeleton,
    debug_spec,
)
from ..generators import (
    classification_to_layout_skeleton,
    generate_grid_classification,
    skeleton_to_layout,
)
from ..spec.parser import build_model, parse_circuit_array_spec, parse_circuit_array_spec_json


Stage = str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print deterministic debug outputs for pipeline stages")
    parser.add_argument("json_path", help="Path to cap-array/res-array spec JSON file")
    parser.add_argument("--layers", type=int, default=1, help="Number of layers to generate (default: 1)")
    parser.add_argument(
        "--stage",
        choices=("spec", "grid", "skeleton", "layout", "all"),
        default="all",
        help="Pipeline stage to print",
    )
    return parser


def _load_spec_model(json_path: Path):
    raw_json = json_path.read_text(encoding="utf-8")
    parsed = parse_circuit_array_spec_json(raw_json)
    parsed = parse_circuit_array_spec(parsed)
    return build_model(parsed)


def _print_header(name: str) -> None:
    print(f"=== {name} ===")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    spec = _load_spec_model(Path(args.json_path))

    if args.stage == "spec":
        print(debug_spec(spec))
        return 0

    classification = generate_grid_classification(spec, layers=args.layers)
    if args.stage == "grid":
        print(debug_grid_classification(classification))
        return 0

    skeleton = classification_to_layout_skeleton(classification)
    if args.stage == "skeleton":
        print(debug_layout_skeleton(skeleton))
        return 0

    layout = skeleton_to_layout(skeleton)
    if args.stage == "layout":
        print(debug_layout(layout))
        return 0

    _print_header("SPEC")
    print(debug_spec(spec))
    print()

    _print_header("GRID")
    print(debug_grid_classification(classification))
    print()

    _print_header("SKELETON")
    print(debug_layout_skeleton(skeleton))
    print()

    _print_header("LAYOUT")
    print(debug_layout(layout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
