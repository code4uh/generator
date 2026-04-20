import json
from pathlib import Path

import pytest

from circuit_array_spec.derive import (
    derive_cap_grid,
    derive_res_grid,
    expand_cap_devices,
    expand_res_devices,
)
from circuit_array_spec.models import CapArraySpecModel, ResArraySpecModel
from circuit_array_spec.validator import SpecValidationError, validate_spec

ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str) -> dict:
    return json.loads((ROOT / "spec" / "examples" / name).read_text(encoding="utf-8"))


def test_valid_cap_array_example() -> None:
    spec = load_example("cap_array.example.json")

    model = validate_spec(spec)

    assert isinstance(model, CapArraySpecModel)
    expanded = expand_cap_devices(spec)
    assert expanded["real"][0] == "C1_1"
    assert expanded["real"][-1] == "C4_2"
    assert len(expanded["real"]) == 12

    grid = derive_cap_grid(spec)
    assert len(grid) == 3
    assert all(len(row) == 4 for row in grid)


def test_valid_res_array_example() -> None:
    spec = load_example("res_array.example.json")

    model = validate_spec(spec)

    assert isinstance(model, ResArraySpecModel)
    expanded = expand_res_devices(spec)
    assert expanded["real"][0] == "R1_1_1"
    assert expanded["real"][-1] == "R3_2_2"
    assert len(expanded["real"]) == (3 + 4 + 2) * 2

    derived = derive_res_grid(spec)
    assert derived["rows"] == 6
    assert derived["cols"] == 4
    assert len(derived["grid"]) == 6
    assert all(len(row) == 4 for row in derived["grid"])


def test_invalid_cap_array_plus_connected_not_allowed() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["topology"]["connection"] = "open"

    with pytest.raises(SpecValidationError, match="plusConnected"):
        validate_spec(spec)


def test_invalid_cap_array_duplicate_plus_connected_index() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["topology"]["plusConnected"] = "(1, 2) (2, 4)"

    with pytest.raises(SpecValidationError, match="doppelten"):
        validate_spec(spec)


def test_invalid_res_array_wrong_algorithm() -> None:
    spec = load_example("res_array.example.json")
    spec["inputs"]["placement"]["algorithm"] = "user"

    with pytest.raises(SpecValidationError):
        validate_spec(spec)


def test_invalid_res_array_pattern_not_null() -> None:
    spec = load_example("res_array.example.json")
    spec["inputs"]["placement"]["pattern"] = [["R1_1_1"]]

    with pytest.raises(SpecValidationError):
        validate_spec(spec)
