import json
from pathlib import Path

import pytest

from circuit_array_spec.cap_array_grid_generator import CapArrayGridGenerator
from circuit_array_spec.models import CapArraySpecModel
from circuit_array_spec.models.grid_classification import iter_grid_coordinates
from circuit_array_spec.parser import build_model

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def to_cap_model(spec_dict: dict) -> CapArraySpecModel:
    model = build_model(spec_dict)
    assert isinstance(model, CapArraySpecModel)
    return model


def test_generator_uses_cap_array_spec_model_input() -> None:
    spec = to_cap_model(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))

    classification = CapArrayGridGenerator().generate(spec)

    assert classification.cells_x == 1
    assert classification.cells_y == 1
    assert classification.tile_kind_at(0, 0, 0) == "device"


def test_cap_grid_generator_side_by_side_vs_row_wise_differ() -> None:
    base = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    base["inputs"]["topology"]["cap_list"] = [4]
    base["inputs"]["placement"]["rows"] = 3

    spec_side = json.loads(json.dumps(base))
    spec_side["inputs"]["placement"]["algorithm"] = "side-by-side"

    spec_row_wise = json.loads(json.dumps(base))
    spec_row_wise["inputs"]["placement"]["algorithm"] = "side-by-side-row-wise"

    side = CapArrayGridGenerator().generate(to_cap_model(spec_side))
    row_wise = CapArrayGridGenerator().generate(to_cap_model(spec_row_wise))

    assert side.cells_x == row_wise.cells_x == 2
    assert side.cells_y == row_wise.cells_y == 3
    assert side.tiles != row_wise.tiles
    assert side.tile_kind_at(1, 1, 0) == "device"
    assert row_wise.tile_kind_at(1, 1, 0) == "wire"


def test_cap_grid_generator_simple_side_by_side_case() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [3]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator().generate_tile_classification(to_cap_model(spec), layers=1)

    assert classification.cells_x == 2
    assert classification.cells_y == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 0, 0) == "device"
    assert classification.tile_kind_at(0, 1, 0) == "device"
    assert classification.tile_kind_at(1, 1, 0) == "wire"


def test_cap_grid_generator_common_centroid_differs_from_side_by_side() -> None:
    base = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    base["inputs"]["topology"]["cap_list"] = [3]
    base["inputs"]["placement"]["rows"] = 2

    spec_side = json.loads(json.dumps(base))
    spec_side["inputs"]["placement"]["algorithm"] = "side-by-side"

    spec_cc = json.loads(json.dumps(base))
    spec_cc["inputs"]["placement"]["algorithm"] = "common_centroid"

    side = CapArrayGridGenerator().generate(to_cap_model(spec_side))
    cc = CapArrayGridGenerator().generate(to_cap_model(spec_cc))

    assert side.tiles != cc.tiles
    assert side.tile_kind_at(1, 1, 0) == "wire"
    assert cc.tile_kind_at(1, 1, 0) == "device"


def test_cap_grid_generator_uses_user_pattern_shape() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_user_pattern.json")
    spec["inputs"]["placement"]["pattern"] = [["C1_1", "C0_1"], ["C0_2"]]

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=2)

    assert classification.cells_x == 2
    assert classification.cells_y == 2
    assert classification.layers == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 0, 1) == "device"
    assert classification.tile_kind_at(1, 1, 0) == "wire"


def test_cap_grid_generator_boundary_device_size_is_metadata_only_in_v1_geometry() -> None:
    spec_minimum = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_minimum["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": False, "top": True, "bottom": False, "boundary_device_size": "minimum"}
    )
    spec_unit = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_unit["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": False, "top": True, "bottom": False, "boundary_device_size": "unit"}
    )

    minimum = CapArrayGridGenerator().generate(to_cap_model(spec_minimum))
    unit = CapArrayGridGenerator().generate(to_cap_model(spec_unit))

    assert minimum.cells_x == unit.cells_x == 2
    assert minimum.cells_y == unit.cells_y == 2
    assert minimum.tiles == unit.tiles


def test_cap_grid_generator_boundary_side_flags_control_v1_footprint() -> None:
    spec_no_boundary = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_no_boundary["inputs"]["topology"]["boundary_caps"].update(
        {"left": False, "right": False, "top": False, "bottom": False, "boundary_device_size": "unit"}
    )
    spec_left_top = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_left_top["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": False, "top": True, "bottom": False, "boundary_device_size": "unit"}
    )

    no_boundary = CapArrayGridGenerator().generate(to_cap_model(spec_no_boundary))
    left_top = CapArrayGridGenerator().generate(to_cap_model(spec_left_top))

    assert no_boundary.cells_x == 1
    assert no_boundary.cells_y == 1
    assert left_top.cells_x == 2
    assert left_top.cells_y == 2
    assert no_boundary.tiles != left_top.tiles


def test_cap_grid_generator_connect_dummy_caps_is_v1_noop_for_tile_kind() -> None:
    spec_open = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_open["inputs"]["topology"]["connectDummyCaps"] = "open_floating"

    spec_shorted = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_shorted["inputs"]["topology"]["connectDummyCaps"] = "shorted_G1_p"

    open_class = CapArrayGridGenerator().generate(to_cap_model(spec_open))
    short_class = CapArrayGridGenerator().generate(to_cap_model(spec_shorted))

    assert open_class.tiles == short_class.tiles


def test_cap_grid_generator_rejects_unknown_boundary_device_size() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["boundary_caps"]["boundary_device_size"] = "XL"

    with pytest.raises(ValueError, match="BoundaryDeviceSize"):
        CapArrayGridGenerator().generate(to_cap_model(spec))


def test_cap_grid_generator_has_complete_grid_coverage_without_undefined_tiles() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [1, 2]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=2)

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


def test_cap_grid_generator_side_by_side_assigns_group_index_by_xy() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [2, 1]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=1)

    assert classification.group_index_by_xy == {(0, 0): 0, (1, 0): 0, (0, 1): 1}


def test_cap_grid_generator_row_wise_assigns_group_index_by_xy_across_rows() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [2, 1]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side-row-wise"

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=1)

    assert classification.group_index_by_xy == {(0, 0): 0, (0, 1): 0, (1, 0): 1}


def test_cap_grid_generator_boundary_tiles_have_none_group_index() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [1]
    spec["inputs"]["placement"]["rows"] = 1
    spec["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": False, "top": True, "bottom": False, "boundary_device_size": "unit"}
    )

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=2)

    assert (0, 0) in classification.group_index_by_xy
    assert (0, 1) in classification.group_index_by_xy
    assert (1, 0) in classification.group_index_by_xy
    assert classification.group_index_by_xy[(0, 0)] is None
    assert classification.group_index_by_xy[(0, 1)] is None
    assert classification.group_index_by_xy[(1, 0)] is None


def test_cap_grid_generator_group_index_consistency_with_tile_kinds() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [3]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator().generate(to_cap_model(spec), layers=2)

    for (x, y), _group in classification.group_index_by_xy.items():
        assert classification.tile_kind_at(x, y, 0) == "device"
        assert classification.tile_kind_at(x, y, 1) == "device"

    for (x, y, _layer), kind in classification.tiles.items():
        if kind == "wire":
            assert (x, y) not in classification.group_index_by_xy


def test_cap_grid_generator_group_index_mapping_is_deterministic() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [2, 2]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "common_centroid"

    first = CapArrayGridGenerator().generate(to_cap_model(spec), layers=1)
    second = CapArrayGridGenerator().generate(to_cap_model(spec), layers=1)

    assert first.group_index_by_xy == second.group_index_by_xy
