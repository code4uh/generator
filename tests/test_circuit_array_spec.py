import json
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")

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

    derived = derive_cap_grid(spec)
    assert derived["rows"] == 3
    assert derived["cols"] == 4
    assert len(derived["grid"]) == 3
    assert all(len(row) == 4 for row in derived["grid"])


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


def test_invalid_cap_array_capabilities_placement_requires_fields() -> None:
    spec = load_example("cap_array.example.json")
    spec["capabilities"]["placement"] = {}

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at capabilities\\.placement: missing required property 'supported_algorithms'",
    ):
        validate_spec(spec)


def test_invalid_res_array_capabilities_advanced_requires_supported_fields() -> None:
    spec = load_example("res_array.example.json")
    spec["capabilities"]["advanced"].pop("supported_fields", None)

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at capabilities\\.advanced: missing required property 'supported_fields'",
    ):
        validate_spec(spec)


def test_invalid_cap_array_extra_routing_option_field() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["routing_options"]["unexpectedField"] = True

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.routing_options: additional properties not allowed",
    ):
        validate_spec(spec)


def test_invalid_res_array_extra_advanced_field() -> None:
    spec = load_example("res_array.example.json")
    spec["inputs"]["advanced"]["unexpectedField"] = 1

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.advanced: additional properties not allowed",
    ):
        validate_spec(spec)


def test_invalid_cap_array_boundary_caps_requires_valid_boundary_size() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["topology"]["boundary_caps"]["boundary_size"] = "Large"

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.topology\\.boundary_caps\\.boundary_size: must be one of: 'Unit', 'Minimum'",
    ):
        validate_spec(spec)


def test_invalid_res_array_boundary_resistors_requires_boolean_flags() -> None:
    spec = load_example("res_array.example.json")
    spec["inputs"]["topology"]["boundary_resistors"]["left"] = "yes"

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.topology\\.boundary_resistors\\.left: expected type boolean",
    ):
        validate_spec(spec)


def test_invalid_cap_array_boundary_caps_missing_required_key() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["topology"]["boundary_caps"].pop("top", None)

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.topology\\.boundary_caps: missing required property 'top'",
    ):
        validate_spec(spec)


def test_invalid_cap_array_user_pattern_must_be_array() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["placement"]["algorithm"] = "user"
    spec["inputs"]["placement"]["pattern"] = "C1_1"

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.placement\\.pattern: expected type array",
    ):
        validate_spec(spec)


def test_invalid_cap_array_routing_options_type_check() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["routing_options"]["nVias"] = "2"

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.routing_options\\.nVias: expected type integer",
    ):
        validate_spec(spec)


def test_invalid_res_array_advanced_field_type_check() -> None:
    spec = load_example("res_array.example.json")
    spec["inputs"]["advanced"]["onlyVerticalWires"] = "false"

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.advanced\\.onlyVerticalWires: expected type boolean",
    ):
        validate_spec(spec)


def test_invalid_cap_array_guard_ring_options_structure() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["routing_options"]["guardRingOptions"].pop("left", None)

    with pytest.raises(
        SpecValidationError,
        match="Schema validation failed at inputs\\.routing_options\\.guardRingOptions: missing required property 'left'",
    ):
        validate_spec(spec)


def test_invalid_cap_array_plus_connected_rejects_free_text() -> None:
    spec = load_example("cap_array.example.json")
    spec["inputs"]["topology"]["plusConnected"] = "(1, 2) free text"

    with pytest.raises(SpecValidationError, match="invalid format"):
        validate_spec(spec)
