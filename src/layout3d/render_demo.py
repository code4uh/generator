"""Kleiner CLI-Einstiegspunkt für ASCII/PNG-Rendering von Demo-Layouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .parser import parse_layout
from .render_html import write_layer_gallery_html
from .render import render_layout_ascii, render_layout_png_layers, render_layout_png_stacked


def main() -> int:
    parser = argparse.ArgumentParser(description="Render layout JSON as ASCII and PNG")
    parser.add_argument("layout", type=Path, help="Path to layout JSON file")
    parser.add_argument("--ascii-mode", choices=["compact", "detailed"], default="compact")
    parser.add_argument("--png-out", type=Path, default=None)
    parser.add_argument("--html-out", type=Path, default=None)
    parser.add_argument("--png-stacked-out", type=Path, default=None)
    parser.add_argument("--prefix", default="layout")
    parser.add_argument("--tile-px", type=int, default=72)
    parser.add_argument("--stack-direction", choices=["vertical", "horizontal"], default="vertical")
    parser.add_argument("--tile-size", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--draw-ports", action="store_true")
    parser.add_argument("--show-coords", action="store_true")
    parser.add_argument("--show-legend", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.layout.read_text(encoding="utf-8"))
    layout = parse_layout(data)

    tile_px = args.tile_px if args.tile_size is None else args.tile_size

    print(render_layout_ascii(layout, mode=args.ascii_mode))
    layer_pngs: list[Path] = []
    if args.png_out is not None:
        files = render_layout_png_layers(
            layout,
            output_dir=args.png_out,
            prefix=args.prefix,
            tile_size=tile_px,
            draw_ports=args.draw_ports,
            show_coords=args.show_coords,
        )
        print("\nPNG files:")
        for path in files:
            print(f"- {path}")
        layer_pngs = files

    if args.html_out is not None:
        if layer_pngs:
            write_layer_gallery_html(out_html=args.html_out, png_files=layer_pngs)
            print(f"\nHTML gallery:\n- {args.html_out}")
        else:
            print("\nSkipping HTML gallery: no layer PNGs available (use --png-out).")
    if args.png_stacked_out is not None:
        stacked_path = render_layout_png_stacked(
            layout,
            output_path=args.png_stacked_out,
            tile_px=tile_px,
            stack_direction=args.stack_direction,
            draw_ports=args.draw_ports,
            show_coords=args.show_coords,
            show_legend=args.show_legend,
        )
        print(f"\nStacked PNG:\n- {stacked_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
