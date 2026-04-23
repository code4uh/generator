import json
from pathlib import Path

from arraylayout.models import BoundaryDeviceSize, CapArraySpecModel, ResArraySpecModel
from arraylayout.spec.validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_cap_model_from_minimal_fixture() -> None:
    model = validate_spec(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))
    assert isinstance(model, CapArraySpecModel)
    assert model.type == "cap_array"
    assert "boundary_device_size" in model.topology.boundary_caps
    assert "boundary_size" not in model.topology.boundary_caps
    assert model.topology.boundary_caps["boundary_device_size"] is BoundaryDeviceSize.UNIT


def test_res_model_from_minimal_fixture() -> None:
    model = validate_spec(load_fixture("spec/fixtures/valid/res_array_minimal.json"))
    assert isinstance(model, ResArraySpecModel)
    assert model.type == "res_array"
    assert "boundary_device_size" in model.topology.boundary_resistors
    assert "boundary_size" not in model.topology.boundary_resistors
    assert model.topology.boundary_resistors["boundary_device_size"] is BoundaryDeviceSize.UNIT


def test_boundary_device_size_serializes_to_lowercase_string_values() -> None:
    model = validate_spec(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))
    assert model.topology.boundary_caps["boundary_device_size"].value == "unit"


def test_boundary_device_size_parses_minimum_enum_value() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec["inputs"]["topology"]["boundary_resistors"]["boundary_device_size"] = "minimum"

    model = validate_spec(spec)

    assert model.topology.boundary_resistors["boundary_device_size"] is BoundaryDeviceSize.MINIMUM
