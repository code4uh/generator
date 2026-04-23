import json
from pathlib import Path

import pytest

from arraylayout.validator import SpecValidationError, validate_spec

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_valid_cap_user_pattern() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_user_pattern.json")
    validate_spec(spec)


def test_valid_cap_without_plus_connected_when_not_user_defined() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    assert "plusConnected" not in spec["inputs"]["topology"]
    validate_spec(spec)


def test_invalid_cap_missing_plus_connected() -> None:
    spec = load_fixture("spec/fixtures/invalid/cap_array_missing_plus_connected.json")
    with pytest.raises(SpecValidationError, match="plusConnected"):
        validate_spec(spec)


def test_invalid_res_connect_dummy() -> None:
    spec = load_fixture("spec/fixtures/invalid/res_array_invalid_connect_dummy.json")
    with pytest.raises(SpecValidationError):
        validate_spec(spec)


def test_cap_boundary_size_legacy_field_is_rejected() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    boundary = spec["inputs"]["topology"]["boundary_caps"]
    boundary["boundary_size"] = boundary.pop("boundary_device_size")

    with pytest.raises(SpecValidationError, match="boundary_device_size|additional properties"):
        validate_spec(spec)


def test_res_boundary_size_legacy_field_is_rejected() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    boundary = spec["inputs"]["topology"]["boundary_resistors"]
    boundary["boundary_size"] = boundary.pop("boundary_device_size")

    with pytest.raises(SpecValidationError, match="boundary_device_size|additional properties"):
        validate_spec(spec)


@pytest.mark.parametrize("invalid_value", ["MINIMUM", "foo", "1"])
def test_boundary_device_size_invalid_values_are_rejected(invalid_value: str) -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["boundary_caps"]["boundary_device_size"] = invalid_value

    with pytest.raises(SpecValidationError, match="BoundaryDeviceSize|must be one of"):
        validate_spec(spec)


def test_oneof_error_includes_sub_causes() -> None:
    pytest.importorskip("jsonschema")
    spec = {
        "version": "0.1",
        "type": "cap_array",
        "inputs": {},
        "capabilities": {},
        "output": {},
    }
    with pytest.raises(SpecValidationError, match="candidates failed"):
        validate_spec(spec)
