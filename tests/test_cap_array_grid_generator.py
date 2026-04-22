import json
from pathlib import Path

from circuit_array_spec.cap_array_grid_generator import CapArrayGridGenerator
from circuit_array_spec.models.grid_classification import iter_grid_coordinates

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_cap_grid_generator_side_by_side_plans_devices_then_wires() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [3]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator(layers=1).generate(spec)

    assert classification.cells_x == 2
    assert classification.cells_y == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 0, 0) == "device"
    assert classification.tile_kind_at(0, 1, 0) == "device"
    assert classification.tile_kind_at(1, 1, 0) == "wire"


def test_cap_grid_generator_uses_user_pattern_shape() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_user_pattern.json")
    spec["inputs"]["placement"]["pattern"] = [["C1_1", "C0_1"], ["C0_2"]]

    classification = CapArrayGridGenerator(layers=2).generate(spec)

    assert classification.cells_x == 2
    assert classification.cells_y == 2
    assert classification.layers == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 0, 1) == "device"
    assert classification.tile_kind_at(1, 1, 0) == "wire"


def test_cap_grid_generator_applies_boundary_caps() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["boundary_caps"].update({"left": True, "right": False, "top": True, "bottom": False})

    classification = CapArrayGridGenerator(layers=1).generate(spec)

    assert classification.cells_x == 2
    assert classification.cells_y == 2
    assert classification.tile_kind_at(0, 0, 0) == "device"  # top-left boundary
    assert classification.tile_kind_at(1, 0, 0) == "device"  # top boundary
    assert classification.tile_kind_at(0, 1, 0) == "device"  # left boundary
    assert classification.tile_kind_at(1, 1, 0) == "device"  # shifted core device


def test_cap_grid_generator_has_complete_grid_coverage_without_undefined_tiles() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec["inputs"]["topology"]["cap_list"] = [1, 2]
    spec["inputs"]["placement"]["rows"] = 2
    spec["inputs"]["placement"]["algorithm"] = "side-by-side"

    classification = CapArrayGridGenerator(layers=2).generate(spec)

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
