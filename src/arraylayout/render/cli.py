"""Developer CLI: spec JSON -> minimal layout -> ASCII/PNG/HTML render outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from layout3d.parser import layout_to_json
from layout3d.render import render_layout_ascii, render_layout_png_layers, render_layout_png_stacked
from layout3d.render_html import write_layer_gallery_html

from ..generators import generate_minimal_layout
from ..spec.parser import build_model, parse_circuit_array_spec, parse_circuit_array_spec_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render spec JSON through minimal layout pipeline as ASCII and PNG"
    )
    parser.add_argument("spec", type=Path, help="Path to cap-array/res-array spec JSON file")
    parser.add_argument("--layers", type=int, default=1, help="Number of layers to generate (default: 1)")
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
    parser.add_argument("--dump-layout-json", type=Path, default=None)
    return parser


def _load_spec(path: Path):
    parsed = parse_circuit_array_spec_json(path.read_text(encoding="utf-8"))
    parsed = parse_circuit_array_spec(parsed)
    return build_model(parsed)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    spec_model = _load_spec(args.spec)
    layout = generate_minimal_layout(spec_model, layers=args.layers)

    if args.dump_layout_json is not None:
        args.dump_layout_json.parent.mkdir(parents=True, exist_ok=True)
        args.dump_layout_json.write_text(layout_to_json(layout), encoding="utf-8")

    tile_px = args.tile_px if args.tile_size is None else args.tile_size

    print(render_layout_ascii(layout, mode=args.ascii_mode))
    layer_pngs: list[Path] = []
    stacked_path: Path | None = None

    if args.png_out is not None:
        layer_pngs = render_layout_png_layers(
            layout,
            output_dir=args.png_out,
            prefix=args.prefix,
            tile_size=tile_px,
            draw_ports=args.draw_ports,
            show_coords=args.show_coords,
        )
        print("\nPNG files:")
        for path in layer_pngs:
            print(f"- {path}")

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

    if args.html_out is not None:
        if layer_pngs:
            write_layer_gallery_html(
                out_html=args.html_out,
                png_files=layer_pngs,
                stacked_png=stacked_path,
            )
            print(f"\nHTML gallery:\n- {args.html_out}")
        else:
            print("\nSkipping HTML gallery: no layer PNGs available (use --png-out).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
