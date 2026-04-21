from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from layout3d import parse_layout
from layout3d.render import build_render_view, render_ascii, render_png_layers, render_png_stacked

ROOT = Path(__file__).resolve().parents[1]


def _load_layout(rel_path: str):
    raw = json.loads((ROOT / rel_path).read_text(encoding="utf-8"))
    return parse_layout(raw)


def test_ascii_compact_snapshot_minimal_layout() -> None:
    layout = _load_layout("examples/layout3d_valid_minimal.json")
    view = build_render_view(layout)

    rendered = render_ascii(view, mode="compact")

    assert rendered == (
        "Layer 0\n"
        ". . .\n"
        ". D W\n"
        ". . .\n\n"
        "Layer 1\n"
        ". . .\n"
        ". D .\n"
        ". . .\n\n"
        "Layer 2\n"
        ". . .\n"
        ". . .\n"
        ". . ."
    )


def test_ascii_detailed_snapshot_minimal_layout() -> None:
    layout = _load_layout("examples/layout3d_valid_minimal.json")
    view = build_render_view(layout)

    rendered = render_ascii(view, mode="detailed")

    assert rendered == (
        "Layer 0\n"
        "[  ] [  ] [  ]\n"
        "[  ] [D ] [ W]\n"
        "[  ] [  ] [  ]\n"
        "details:\n"
        "  - (1,1) | device=dev1:amp | pins=[p1@(0,0)<north:0,east:1>]\n"
        "  - (2,1) | wires=[w1:n1:horizontal]\n\n"
        "Layer 1\n"
        "[  ] [  ] [  ]\n"
        "[  ] [D ] [  ]\n"
        "[  ] [  ] [  ]\n"
        "details:\n"
        "  - (1,1) | device=dev1:amp | pins=[]\n\n"
        "Layer 2\n"
        "[  ] [  ] [  ]\n"
        "[  ] [  ] [  ]\n"
        "[  ] [  ] [  ]\n"
        "details:"
    )




def test_build_render_view_maps_pins_to_pin_tile_layer_for_multilayer_device() -> None:
    layout = _load_layout("examples/complex_layout.json")
    view = build_render_view(layout)

    layer0_cell = view.by_layer[0].cells[(1, 1)]
    layer1_cell = view.by_layer[1].cells[(1, 1)]
    layer2_cell = view.by_layer[2].cells[(1, 1)]
    layer3_cell = view.by_layer[3].cells[(1, 1)]

    assert layer0_cell.device_id == "ctrl0"
    assert layer1_cell.device_id == "ctrl0"
    assert layer2_cell.device_id == "ctrl0"
    assert layer3_cell.device_id == "ctrl0"

    assert {pin.pin_id for pin in layer0_cell.pins} == {"ctrl_sync"}
    assert {pin.pin_id for pin in layer1_cell.pins} == set()
    assert {pin.pin_id for pin in layer2_cell.pins} == {"ctrl_bus"}
    assert {pin.pin_id for pin in layer3_cell.pins} == set()

def test_render_png_layers_smoke(tmp_path: Path) -> None:
    pytest.importorskip("PIL")

    layout = _load_layout("examples/simple_layout.json")
    view = build_render_view(layout)

    paths = render_png_layers(view, output_dir=tmp_path, prefix="simple", tile_size=48, draw_ports=True)

    assert len(paths) == layout.grid.layers
    for path in paths:
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0


def test_render_png_stacked_vertical_smoke(tmp_path: Path) -> None:
    pil_image = pytest.importorskip("PIL.Image")

    layout = _load_layout("examples/simple_layout.json")
    view = build_render_view(layout)
    out_path = tmp_path / "stacked_vertical.png"

    render_png_stacked(
        view,
        output_path=out_path,
        tile_px=48,
        stack_direction="vertical",
        show_coords=True,
        show_legend=True,
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0

    with pil_image.open(out_path) as image:
        width, height = image.size

    assert width > 0
    assert height > width


def test_render_png_stacked_legend_fits_small_grid(tmp_path: Path) -> None:
    pil_image = pytest.importorskip("PIL.Image")

    layout = _load_layout("examples/layout3d_valid_minimal.json")
    view = build_render_view(layout)
    out_path = tmp_path / "stacked_with_legend.png"

    render_png_stacked(
        view,
        output_path=out_path,
        tile_px=16,
        stack_direction="vertical",
        show_legend=True,
    )

    with pil_image.open(out_path) as image:
        width, _ = image.size

    assert width >= 20 * 2 + 230


def test_render_png_stacked_horizontal_smoke(tmp_path: Path) -> None:
    pil_image = pytest.importorskip("PIL.Image")

    layout = _load_layout("examples/complex_layout.json")
    view = build_render_view(layout)
    out_path = tmp_path / "stacked_horizontal.png"

    render_png_stacked(
        view,
        output_path=out_path,
        tile_px=64,
        stack_direction="horizontal",
    )

    assert out_path.exists()
    assert out_path.stat().st_size > 0

    with pil_image.open(out_path) as image:
        width, height = image.size

    assert width > height


def test_render_demo_cli_help_lists_new_options() -> None:
    env = dict(os.environ)
    src_dir = ROOT / "src"
    env["PYTHONPATH"] = str(src_dir) if "PYTHONPATH" not in env else f"{src_dir}:{env['PYTHONPATH']}"

    proc = subprocess.run(
        [sys.executable, "-m", "layout3d.render_demo", "-h"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    stdout = proc.stdout
    assert "--png-stacked-out" in stdout
    assert "--stack-direction" in stdout
    assert "--show-coords" in stdout
    assert "--show-legend" in stdout


def test_render_demo_cli_writes_layer_pngs_and_stacked_png(tmp_path: Path) -> None:
    pytest.importorskip("PIL")

    env = dict(os.environ)
    src_dir = ROOT / "src"
    env["PYTHONPATH"] = str(src_dir) if "PYTHONPATH" not in env else f"{src_dir}:{env['PYTHONPATH']}"

    out_dir = tmp_path / "layers"
    stacked = tmp_path / "stacked.png"
    layout = ROOT / "examples" / "simple_layout.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "layout3d.render_demo",
            str(layout),
            "--png-out",
            str(out_dir),
            "--prefix",
            "demo",
            "--png-stacked-out",
            str(stacked),
            "--stack-direction",
            "horizontal",
            "--show-coords",
            "--show-legend",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    layer_files = sorted(out_dir.glob("demo_layer*.png"))
    assert layer_files
    assert stacked.exists()
    assert stacked.stat().st_size > 0


def test_render_demo_cli_only_stacked_out_writes_no_layer_pngs(tmp_path: Path) -> None:
    pytest.importorskip("PIL")

    env = dict(os.environ)
    src_dir = ROOT / "src"
    env["PYTHONPATH"] = str(src_dir) if "PYTHONPATH" not in env else f"{src_dir}:{env['PYTHONPATH']}"

    stacked = tmp_path / "stacked_only.png"
    layout = ROOT / "examples" / "simple_layout.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "layout3d.render_demo",
            str(layout),
            "--png-stacked-out",
            str(stacked),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert stacked.exists()
    assert stacked.stat().st_size > 0
    assert list(tmp_path.rglob("*_layer*.png")) == []
