from __future__ import annotations

import json
from pathlib import Path

import pytest

from layout3d import (
    LayoutPipeline,
    LayoutValidationError,
    LayoutValidator,
    ParseError,
    layout_to_dict,
    parse_layout,
    parse_layout_json,
)
from layout3d.normalize import normalize_layout
from layout3d.representation import build_tile_representation

ROOT = Path(__file__).resolve().parents[1]


def _load_json(rel_path: str) -> dict:
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def _validate(data: dict):
    parsed = parse_layout(data)
    normalized = normalize_layout(parsed)
    return LayoutValidator().validate(normalized)


def _codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def test_valid_minimal_example() -> None:
    raw = (ROOT / "examples/json/layout3d_valid_minimal.json").read_text(encoding="utf-8")
    parsed_from_json = parse_layout(parse_layout_json(raw))
    report = _validate(layout_to_dict(parsed_from_json))
    assert report.ok


def test_device_outside_grid() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["x"] = 99
    report = _validate(data)
    assert "OUT_OF_GRID" in _codes(report)


def test_device_outside_slot() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["y"] = 0
    report = _validate(data)
    assert "DEVICE_OUTSIDE_SLOT" in _codes(report)


def test_device_overlap() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"].append(
        {
            "deviceId": "dev2",
            "deviceType": "amp",
            "slotId": "slotA",
            "x": 1,
            "y": 1,
            "fromLayer": 1,
            "toLayer": 2,
            "pinGrid": {"cellsX": 2, "cellsY": 2},
            "pins": [],
        }
    )
    report = _validate(data)
    assert "DEVICE_OVERLAP" in _codes(report)


def test_pin_outside_pingrid() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["pins"][0]["localPos"] = {"px": 2, "py": 0}
    report = _validate(data)
    assert "PIN_LOCAL_POS" in _codes(report)


def test_duplicate_port() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["pins"][0]["attachment"]["ports"].append({"side": "north", "pos_idx": 0})
    report = _validate(data)
    assert "DUPLICATE_PORT" in _codes(report)


def test_multiple_distinct_ports_are_valid_or_semantics() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["pins"][0]["attachment"]["ports"] = [
        {"side": "north", "pos_idx": 0},
        {"side": "south", "pos_idx": 1},
    ]
    report = _validate(data)
    assert report.ok


def test_duplicate_wire_tile_on_same_coord() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    second = dict(data["wireTiles"][0])
    second["wireTileId"] = "wt2"
    data["wireTiles"].append(second)
    report = _validate(data)
    assert "DUPLICATE_WIRE_TILE_COORD" in _codes(report)


def test_duplicate_wire_tile_coord_never_silently_overwritten_in_representation() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    second = dict(data["wireTiles"][0])
    second["wireTileId"] = "wt2"
    data["wireTiles"].append(second)
    parsed = parse_layout(data)
    with pytest.raises(ValueError, match="duplicate wireTile coordinate"):
        build_tile_representation(parsed)


def test_duplicate_device_coord_never_silently_overwritten_in_representation() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"].append(
        {
            "deviceId": "dev2",
            "deviceType": "amp",
            "slotId": "slotA",
            "x": 1,
            "y": 1,
            "fromLayer": 1,
            "toLayer": 2,
            "pinGrid": {"cellsX": 2, "cellsY": 2},
            "pins": [],
        }
    )
    parsed = parse_layout(data)
    with pytest.raises(ValueError, match="duplicate device coordinate"):
        build_tile_representation(parsed)


def test_duplicate_wire_id_in_ordered_wires() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    tile = data["wireTiles"][0]
    tile["orderedWires"].append(
        {
            "wireId": "w1",
            "wireType": "sig",
            "netId": "n2",
        }
    )
    report = _validate(data)
    assert "DUPLICATE_WIRE_ID" in _codes(report)


def test_wire_tile_orientation_parsed_on_tile_level() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    parsed = parse_layout(data)
    assert parsed.wire_tiles[0].orientation == "horizontal"
    assert not hasattr(parsed.wire_tiles[0].ordered_wires[0], "orientation")


def test_missing_wire_tile_orientation_raises_parse_error() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    del data["wireTiles"][0]["orientation"]
    with pytest.raises(ParseError, match=r"wireTiles\[0\]"):
        parse_layout(data)


def test_invalid_wire_tile_orientation_is_reported_by_validation() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["wireTiles"][0]["orientation"] = "diagonal"
    report = _validate(data)
    assert "WIRE_ORIENTATION" in _codes(report)


def test_device_slot_is_validated_even_without_devices() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"] = []
    data["deviceSlots"][0]["x"] = 999
    report = _validate(data)
    assert "OUT_OF_GRID" in _codes(report)


def test_pin_grid_dimensions_must_be_positive() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["pinGrid"] = {"cellsX": 0, "cellsY": -1}
    report = _validate(data)
    assert "PIN_GRID_DIMENSION" in _codes(report)


def test_parse_error_contains_field_path() -> None:
    data = _load_json("examples/json/layout3d_valid_minimal.json")
    data["devices"][0]["pinGrid"]["cellsX"] = "2"
    with pytest.raises(ParseError, match=r"devices\[0\]\.pinGrid\.cellsX"):
        parse_layout(data)


@pytest.mark.parametrize(
    "rel_path",
    (
        "examples/json/simple_layout.json",
        "examples/json/complex_layout.json",
    ),
)
def test_demo_examples_parse_and_validate(rel_path: str) -> None:
    report = _validate(_load_json(rel_path))
    assert report.ok


def test_pipeline_raises_structured_error() -> None:
    data = _load_json("examples/json/layout3d_invalid_overlap.json")
    try:
        LayoutPipeline().parse_normalize_validate(data)
    except LayoutValidationError as error:
        assert error.issues
        first = error.issues[0]
        assert first.entity_type
        assert first.location
    else:
        raise AssertionError("expected LayoutValidationError")


def test_legacy_namespace_remains_compatible() -> None:
    from layout3d import LayoutPipeline as LegacyLayoutPipeline

    assert LegacyLayoutPipeline is LayoutPipeline


def test_legacy_and_canonical_exports_are_consistent() -> None:
    import layout3d as legacy
    import layout3d as canonical

    expected_symbols = {
        "LayoutPipeline",
        "LayoutValidator",
        "LayoutValidationError",
        "parse_layout",
        "parse_layout_json",
        "layout_to_dict",
        "layout_to_json",
        "normalize_layout",
        "build_tile_representation",
    }

    for symbol in expected_symbols:
        assert hasattr(canonical, symbol)
        assert hasattr(legacy, symbol)
        assert getattr(legacy, symbol) is getattr(canonical, symbol)


def test_legacy_submodule_objects_are_consistent() -> None:
    from layout3d.validation import LayoutValidator as LegacyValidator
    from layout3d.validation import LayoutValidator as CanonicalValidator
    from layout3d.errors import LayoutValidationError as LegacyError
    from layout3d.errors import LayoutValidationError as CanonicalError

    assert LegacyValidator is CanonicalValidator
    assert LegacyError is CanonicalError
