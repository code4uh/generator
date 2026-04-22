import json
from pathlib import Path

import pytest

from circuit_array_spec.models import ResArraySpecModel
from circuit_array_spec.models.grid_classification import iter_grid_coordinates
from circuit_array_spec.parser import build_model
from circuit_array_spec.res_array_grid_generator import ResArrayGridGenerator

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def to_res_model(spec_dict: dict) -> ResArraySpecModel:
    model = build_model(spec_dict)
    assert isinstance(model, ResArraySpecModel)
    return model


def test_res_grid_generator_simple_side_by_side_case() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec["inputs"]["topology"]["res_list"] = [3]
    spec["inputs"]["topology"]["parallelResNo"] = 1

    classification = ResArrayGridGenerator().generate_tile_classification(to_res_model(spec), layers=2)

    assert classification.cells_x == 3
    assert classification.cells_y == 1
    assert classification.layers == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(2, 0, 1) == "device"


def test_res_grid_generator_parallel_res_no_affects_device_footprint() -> None:
    spec_single = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_single["inputs"]["topology"]["res_list"] = [2]
    spec_single["inputs"]["topology"]["parallelResNo"] = 1

    spec_parallel = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_parallel["inputs"]["topology"]["res_list"] = [2]
    spec_parallel["inputs"]["topology"]["parallelResNo"] = 3

    single = ResArrayGridGenerator().generate(to_res_model(spec_single))
    parallel = ResArrayGridGenerator().generate(to_res_model(spec_parallel))

    assert single.cells_x == 2
    assert parallel.cells_x == 6
    assert all(kind == "device" for kind in single.tiles.values())
    assert all(kind == "device" for kind in parallel.tiles.values())


def test_res_grid_generator_boundary_resistors_expand_device_area() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec["inputs"]["topology"]["res_list"] = [2]
    spec["inputs"]["topology"]["parallelResNo"] = 1
    spec["inputs"]["topology"]["boundary_resistors"].update(
        {"left": True, "right": False, "top": True, "bottom": True, "boundary_size": "Minimum"}
    )

    classification = ResArrayGridGenerator().generate(to_res_model(spec), layers=1)

    assert classification.cells_x == 3
    assert classification.cells_y == 3
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 1, 0) == "device"


def test_res_grid_generator_connect_dummy_res_is_v1_noop_for_tile_kind() -> None:
    spec_open = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_open["inputs"]["topology"]["res_list"] = [2]
    spec_open["inputs"]["topology"]["connectDummyRes"] = "open_floating"

    spec_vss = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_vss["inputs"]["topology"]["res_list"] = [2]
    spec_vss["inputs"]["topology"]["connectDummyRes"] = "VSS"

    open_class = ResArrayGridGenerator().generate(to_res_model(spec_open))
    vss_class = ResArrayGridGenerator().generate(to_res_model(spec_vss))

    assert open_class.tiles == vss_class.tiles


def test_res_grid_generator_rejects_unknown_boundary_size() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec["inputs"]["topology"]["boundary_resistors"]["boundary_size"] = "XL"

    with pytest.raises(ValueError, match="unsupported boundary_size"):
        ResArrayGridGenerator().generate(to_res_model(spec))


def test_res_grid_generator_has_complete_grid_coverage_without_undefined_tiles() -> None:
    spec = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec["inputs"]["topology"]["res_list"] = [1, 2]
    spec["inputs"]["topology"]["parallelResNo"] = 2
    spec["inputs"]["topology"]["boundary_resistors"].update(
        {"left": False, "right": False, "top": True, "bottom": False, "boundary_size": "Unit"}
    )

    classification = ResArrayGridGenerator().generate(to_res_model(spec), layers=3)

    expected_coords = set(
        iter_grid_coordinates(
            cells_x=classification.cells_x,
            cells_y=classification.cells_y,
            layers=classification.layers,
        )
    )
    assert set(classification.tiles.keys()) == expected_coords
    assert len(classification.tiles) == (
        classification.cells_x * classification.cells_y * classification.layers
    )
