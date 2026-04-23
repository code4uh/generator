from __future__ import annotations

import json
from pathlib import Path

import pytest

from arraylayout.render_cli import main

ROOT = Path(__file__).resolve().parents[1]


def _example(rel: str) -> str:
    return str(ROOT / rel)


def test_render_cli_runs_for_cap_spec_ascii(capsys) -> None:
    exit_code = main([
        _example("examples/json/cap_array_v0_1.json"),
        "--layers",
        "2",
        "--ascii-mode",
        "compact",
    ])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Layer 0" in out


def test_render_cli_runs_for_res_spec_ascii(capsys) -> None:
    exit_code = main([
        _example("examples/json/res_array_v0_1.json"),
        "--layers",
        "2",
        "--ascii-mode",
        "detailed",
    ])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Layer 0" in out
    assert "details:" in out


def test_render_cli_passes_render_options_and_writes_html(monkeypatch, tmp_path: Path) -> None:
    calls: dict[str, object] = {}

    png_dir = tmp_path / "layers"
    html_out = tmp_path / "gallery.html"
    stacked_out = tmp_path / "stacked.png"
    layer0 = png_dir / "spec_layer0.png"

    def _fake_render_layers(layout, output_dir, prefix, tile_size, draw_ports, show_coords):
        calls["layers"] = {
            "output_dir": output_dir,
            "prefix": prefix,
            "tile_size": tile_size,
            "draw_ports": draw_ports,
            "show_coords": show_coords,
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        layer0.write_bytes(b"png")
        return [layer0]

    def _fake_render_stacked(layout, output_path, tile_px, stack_direction, draw_ports, show_coords, show_legend):
        calls["stacked"] = {
            "output_path": output_path,
            "tile_px": tile_px,
            "stack_direction": stack_direction,
            "draw_ports": draw_ports,
            "show_coords": show_coords,
            "show_legend": show_legend,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"png")
        return output_path

    def _fake_write_html(out_html, png_files, title="Layout-Layer", stacked_png=None):
        calls["html"] = {
            "out_html": out_html,
            "png_files": png_files,
            "stacked_png": stacked_png,
        }
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr("arraylayout.render_cli.render_layout_png_layers", _fake_render_layers)
    monkeypatch.setattr("arraylayout.render_cli.render_layout_png_stacked", _fake_render_stacked)
    monkeypatch.setattr("arraylayout.render_cli.write_layer_gallery_html", _fake_write_html)

    exit_code = main([
        _example("examples/json/cap_array_v0_1.json"),
        "--layers",
        "1",
        "--png-out",
        str(png_dir),
        "--prefix",
        "spec",
        "--tile-px",
        "48",
        "--draw-ports",
        "--show-coords",
        "--png-stacked-out",
        str(stacked_out),
        "--stack-direction",
        "horizontal",
        "--show-legend",
        "--html-out",
        str(html_out),
    ])

    assert exit_code == 0
    assert calls["layers"] == {
        "output_dir": png_dir,
        "prefix": "spec",
        "tile_size": 48,
        "draw_ports": True,
        "show_coords": True,
    }
    assert calls["stacked"] == {
        "output_path": stacked_out,
        "tile_px": 48,
        "stack_direction": "horizontal",
        "draw_ports": True,
        "show_coords": True,
        "show_legend": True,
    }
    assert calls["html"] == {
        "out_html": html_out,
        "png_files": [layer0],
        "stacked_png": stacked_out,
    }


def test_render_cli_dump_layout_json_writes_file(tmp_path: Path) -> None:
    dump_path = tmp_path / "layout.json"

    exit_code = main([
        _example("examples/json/res_array_v0_1.json"),
        "--layers",
        "1",
        "--dump-layout-json",
        str(dump_path),
    ])

    assert exit_code == 0
    assert dump_path.exists()

    dumped = json.loads(dump_path.read_text(encoding="utf-8"))
    assert dumped["grid"]["layers"] == 1
    assert "devices" in dumped
