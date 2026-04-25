import json
from pathlib import Path

from gridlayout.spec.derive import derive_cap_grid, derive_res_grid, expand_cap_devices, expand_res_devices

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_cap_derive_minimal() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    assert expand_cap_devices(spec)["real"] == ["C1_1"]
    grid = derive_cap_grid(spec)
    assert grid["rows"] == 1
    assert grid["cols"] == 1


def test_res_derive_minimal() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    assert expand_res_devices(spec)["real"] == ["R1_1_1"]
    grid = derive_res_grid(spec)
    assert grid["rows"] == 1
    assert grid["cols"] == 1
