import json
from pathlib import Path

import pytest

from circuit_array_spec.netlist import generate_netlist

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_generate_cap_netlist_minimal() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")

    netlist = generate_netlist(spec)

    assert "C1_1 G1_p GND CUNIT" in netlist
    assert ".SUBCKT cap_array" in netlist
    assert ".ENDS cap_array" in netlist


def test_generate_res_netlist_minimal() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")

    netlist = generate_netlist(spec)

    assert "R1_1_1 G1_p D1_n RUNIT" in netlist
    assert ".SUBCKT res_array" in netlist
    assert ".ENDS res_array" in netlist


def test_generate_netlist_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported spec type"):
        generate_netlist({"type": "unknown"})
