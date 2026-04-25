import json
from pathlib import Path

from gridlayout.generators import (
    generate_grid_classification,
    generate_layout_skeleton,
    generate_minimal_layout,
)
from gridlayout.spec.parser import build_model
from gridlayout.skeleton.transform import classification_to_layout_skeleton

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_pipeline_stages_are_coordinate_consistent() -> None:
    spec_dict = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_dict["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": True, "top": True, "bottom": True}
    )
    spec = build_model(spec_dict)

    classification = generate_grid_classification(spec, layers=2)
    skeleton_direct = classification_to_layout_skeleton(classification)
    skeleton_generated = generate_layout_skeleton(spec, layers=2)
    layout = generate_minimal_layout(spec, layers=2)

    assert skeleton_direct == skeleton_generated

    classified_device_tiles = {
        coord for coord, kind in classification.tiles.items() if kind == "device"
    }
    layout_device_tiles = {
        (device.x, device.y, layer)
        for device in layout.devices
        for layer in range(device.from_layer, device.to_layer + 1)
    }
    assert layout_device_tiles == classified_device_tiles

    classified_wire_tiles = {
        coord for coord, kind in classification.tiles.items() if kind == "wire"
    }
    layout_wire_tiles = {(tile.x, tile.y, tile.layer) for tile in layout.wire_tiles}
    assert layout_wire_tiles == classified_wire_tiles


def test_classification_stage_contains_geometry_only() -> None:
    spec = build_model(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))
    classification = generate_grid_classification(spec, layers=1)

    assert set(classification.__dataclass_fields__) == {"cells_x", "cells_y", "layers", "tiles"}
    assert set(classification.tiles.values()) <= {"device", "wire"}
