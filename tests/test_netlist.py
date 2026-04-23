import json
from pathlib import Path

import pytest

from arraylayout.spec.netlist import generate_netlist

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _cap_spec() -> dict:
    return load_fixture("spec/fixtures/valid/cap_array_minimal.json")


def _res_spec() -> dict:
    return load_fixture("spec/fixtures/valid/res_array_minimal.json")


def test_generate_cap_netlist_minimal() -> None:
    spec = _cap_spec()

    netlist = generate_netlist(spec)

    assert "C1_1 G1_p GND 1f W=1u L=1u" in netlist
    assert ".SUBCKT cap_array" in netlist
    assert ".ENDS cap_array" in netlist


def test_generate_cap_netlist_short_plus_pins() -> None:
    spec = _cap_spec()
    spec["inputs"]["topology"]["cap_list"] = [1, 1]
    spec["inputs"]["topology"]["connection"] = "shortPlusPins"

    netlist = generate_netlist(spec)

    assert "C1_1 G1_p GND 1f W=1u L=1u" in netlist
    assert "C2_1 G1_p GND 1f W=1u L=1u" in netlist


def test_generate_cap_netlist_user_defined() -> None:
    spec = _cap_spec()
    spec["inputs"]["topology"]["cap_list"] = [1, 1]
    spec["inputs"]["topology"]["connection"] = "userDefined"
    spec["inputs"]["topology"]["plusConnected"] = "(1, 2)"

    netlist = generate_netlist(spec)

    assert "C1_1 G1_p GND 1f W=1u L=1u" in netlist
    assert "C2_1 G1_p GND 1f W=1u L=1u" in netlist


def test_generate_cap_netlist_open_floating_skips_dummy_caps() -> None:
    spec = _cap_spec()
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["topology"]["connectDummyCaps"] = "open_floating"

    netlist = generate_netlist(spec)

    assert "C1_1 G1_p GND 1f W=1u L=1u" in netlist
    assert "C0_" not in netlist


@pytest.mark.parametrize(
    ("connect_dummy", "expected"),
    [
        ("open_shorted", "C0_1 C0_1 C0_1 1f W=1u L=1u"),
        ("shorted_G1_p", "C0_1 G1_p G1_p 1f W=1u L=1u"),
        ("shorted_Cdmy_p", "C0_1 Cdmy_p Cdmy_p 1f W=1u L=1u"),
        ("Cdmy_p+Cdmy_n", "C0_1 Cdmy_p Cdmy_n 1f W=1u L=1u"),
    ],
)
def test_generate_cap_netlist_dummy_modes(connect_dummy: str, expected: str) -> None:
    spec = _cap_spec()
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["topology"]["connectDummyCaps"] = connect_dummy

    netlist = generate_netlist(spec)

    assert expected in netlist


def test_generate_res_netlist_default_values() -> None:
    spec = _res_spec()

    netlist = generate_netlist(spec)

    assert "R1_1_1 G1_p D1_n 1k W=1u L=1u" in netlist
    assert ".SUBCKT res_array" in netlist
    assert ".ENDS res_array" in netlist


def test_generate_res_netlist_dummy_vss() -> None:
    spec = _res_spec()
    spec["inputs"]["topology"]["res_list"] = [2, 1]
    spec["inputs"]["topology"]["connectDummyRes"] = "VSS"

    netlist = generate_netlist(spec)

    assert "R0_1 VSS VSS 1k W=1u L=1u" in netlist


def test_generate_netlist_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported spec type"):
        generate_netlist({"type": "unknown"})
