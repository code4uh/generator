import json
from pathlib import Path

from circuit_array_spec.models import CapArraySpecModel, ResArraySpecModel
from circuit_array_spec.validator import validate_spec

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_cap_model_from_minimal_fixture() -> None:
    model = validate_spec(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))
    assert isinstance(model, CapArraySpecModel)
    assert model.type == "cap_array"
    assert "boundary_device_size" in model.topology.boundary_caps
    assert "boundary_size" not in model.topology.boundary_caps


def test_res_model_from_minimal_fixture() -> None:
    model = validate_spec(load_fixture("spec/fixtures/valid/res_array_minimal.json"))
    assert isinstance(model, ResArraySpecModel)
    assert model.type == "res_array"
    assert "boundary_device_size" in model.topology.boundary_resistors
    assert "boundary_size" not in model.topology.boundary_resistors
