"""Kleiner CLI-Einstiegspunkt für ASCII/PNG-Rendering von Demo-Layouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .parser import parse_layout
from .render import render_layout_ascii, render_layout_png_layers


def main() -> int:
    parser = argparse.ArgumentParser(description="Render layout JSON as ASCII and PNG")
    parser.add_argument("layout", type=Path, help="Path to layout JSON file")
    parser.add_argument("--ascii-mode", choices=["compact", "detailed"], default="compact")
    parser.add_argument("--png-out", type=Path, default=Path("out/render"))
    parser.add_argument("--prefix", default="layout")
    parser.add_argument("--tile-size", type=int, default=72)
    parser.add_argument("--draw-ports", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.layout.read_text(encoding="utf-8"))
    layout = parse_layout(data)

    print(render_layout_ascii(layout, mode=args.ascii_mode))
    files = render_layout_png_layers(
        layout,
        output_dir=args.png_out,
        prefix=args.prefix,
        tile_size=args.tile_size,
        draw_ports=args.draw_ports,
    )
    print("\nPNG files:")
    for path in files:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
