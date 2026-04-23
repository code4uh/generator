from __future__ import annotations

from pathlib import Path

from arraylayout.debug_cli import main

ROOT = Path(__file__).resolve().parents[1]


def _fixture(rel: str) -> str:
    return str(ROOT / rel)


def test_debug_cli_runs_for_cap_example(capsys) -> None:
    exit_code = main([_fixture("spec/fixtures/valid/cap_array_minimal.json"), "--stage", "spec"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "SpecModel" in out
    assert "type=cap_array" in out


def test_debug_cli_runs_for_res_example(capsys) -> None:
    exit_code = main([_fixture("spec/fixtures/valid/res_array_minimal.json"), "--stage", "spec"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "SpecModel" in out
    assert "type=res_array" in out


def test_debug_cli_stage_grid_prints_grid_output(capsys) -> None:
    exit_code = main([_fixture("spec/fixtures/valid/cap_array_minimal.json"), "--stage", "grid", "--layers", "2"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "GeneratedGridClassification" in out
    assert "Layer 1" in out


def test_debug_cli_stage_all_prints_all_headers(capsys) -> None:
    exit_code = main([_fixture("spec/fixtures/valid/cap_array_minimal.json"), "--stage", "all"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "=== SPEC ===" in out
    assert "=== GRID ===" in out
    assert "=== SKELETON ===" in out
    assert "=== LAYOUT ===" in out
