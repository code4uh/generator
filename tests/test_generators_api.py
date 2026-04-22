import json
from pathlib import Path

import pytest

from circuit_array_spec.generators import generate_grid_classification
from circuit_array_spec.models import CapArraySpecModel, ResArraySpecModel
from circuit_array_spec.parser import build_model

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_generate_grid_classification_dispatches_to_cap_generator() -> None:
    spec = build_model(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))
    assert isinstance(spec, CapArraySpecModel)

    classification = generate_grid_classification(spec, layers=2)

    assert classification.cells_x == 1
    assert classification.cells_y == 1
    assert classification.layers == 2
    assert classification.tile_kind_at(0, 0, 1) == "device"


def test_generate_grid_classification_dispatches_to_res_generator() -> None:
    spec_dict = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_dict["inputs"]["topology"]["res_list"] = [3]
    spec = build_model(spec_dict)
    assert isinstance(spec, ResArraySpecModel)

    classification = generate_grid_classification(spec, layers=1)

    assert classification.cells_x == 3
    assert classification.cells_y == 1
    assert classification.tile_kind_at(2, 0, 0) == "device"


def test_generate_grid_classification_rejects_unsupported_spec_type() -> None:
    with pytest.raises(TypeError, match="Unsupported spec model type"):
        generate_grid_classification(object())  # type: ignore[arg-type]
