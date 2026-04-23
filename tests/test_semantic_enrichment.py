import json
from pathlib import Path

from arraylayout.debug import debug_semantics
from arraylayout.semantics.groups import enrich_layout_semantics
from arraylayout.classification.grid import GeneratedGridClassification
from arraylayout.spec.parser import build_model
from layout3d.types import Device, GridSize, LayoutInstance, PinGrid

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _layout_with_devices(*devices: Device, cells_x: int, cells_y: int, layers: int = 1) -> LayoutInstance:
    return LayoutInstance(
        schema_version=1,
        template_ref="generated_layout_skeleton",
        grid=GridSize(cells_x=cells_x, cells_y=cells_y, layers=layers),
        device_slots=(),
        devices=devices,
        wire_tiles=(),
    )


def _device(device_id: str, x: int, y: int) -> Device:
    return Device(
        device_id=device_id,
        device_type="generated_device",
        slot_id=f"slot_{device_id}",
        x=x,
        y=y,
        from_layer=0,
        to_layer=0,
        pin_grid=PinGrid(cells_x=1, cells_y=1),
        pins=(),
    )


def test_semantic_enrichment_core_devices_have_group_and_no_boundary_fields() -> None:
    spec = build_model(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))

    classification = GeneratedGridClassification(
        cells_x=2,
        cells_y=1,
        layers=1,
        tiles={(0, 0, 0): "device", (1, 0, 0): "device"},
    )
    layout = _layout_with_devices(_device("d0", 0, 0), _device("d1", 1, 0), cells_x=2, cells_y=1)

    enriched = enrich_layout_semantics(spec, classification, layout)

    assert enriched.device_semantics_by_id["d0"].role == "core"
    assert enriched.device_semantics_by_id["d0"].group_index == 1
    assert enriched.device_semantics_by_id["d1"].group_index == 1
    assert enriched.device_semantics_by_id["d0"].boundary_side is None
    assert enriched.device_semantics_by_id["d0"].boundary_device_size is None


def test_semantic_enrichment_boundary_devices_include_side_and_size() -> None:
    spec_dict = load_fixture("spec/fixtures/valid/cap_array_minimal.json")
    spec_dict["inputs"]["topology"]["boundary_caps"].update(
        {"left": True, "right": True, "top": True, "bottom": True}
    )
    spec = build_model(spec_dict)

    classification = GeneratedGridClassification(
        cells_x=3,
        cells_y=2,
        layers=1,
        tiles={
            (0, 0, 0): "device",
            (1, 0, 0): "device",
            (2, 0, 0): "device",
            (0, 1, 0): "device",
            (1, 1, 0): "device",
            (2, 1, 0): "device",
        },
    )
    layout = _layout_with_devices(
        _device("left", 0, 1),
        _device("right", 2, 1),
        _device("bottom", 1, 0),
        _device("top", 1, 1),
        cells_x=3,
        cells_y=2,
    )

    enriched = enrich_layout_semantics(spec, classification, layout)

    assert enriched.device_semantics_by_id["left"].role == "boundary"
    assert enriched.device_semantics_by_id["left"].group_index == 0
    assert enriched.device_semantics_by_id["left"].boundary_side == "left"
    assert enriched.device_semantics_by_id["left"].boundary_device_size == spec.topology.boundary_caps["boundary_device_size"]

    assert enriched.device_semantics_by_id["right"].group_index == 0
    assert enriched.device_semantics_by_id["right"].boundary_side == "right"
    assert enriched.device_semantics_by_id["bottom"].group_index == 0
    assert enriched.device_semantics_by_id["bottom"].boundary_side == "bottom"
    assert enriched.device_semantics_by_id["top"].role == "boundary"
    assert enriched.device_semantics_by_id["top"].group_index == 0
    assert enriched.device_semantics_by_id["top"].boundary_side == "top"


def test_semantic_enrichment_mixed_layout_is_deterministic() -> None:
    spec = build_model(load_fixture("spec/fixtures/valid/cap_array_minimal.json"))

    classification = GeneratedGridClassification(
        cells_x=2,
        cells_y=2,
        layers=1,
        tiles={(x, y, 0): "device" for y in range(2) for x in range(2)},
    )
    layout = _layout_with_devices(
        _device("d", 1, 1),
        _device("a", 0, 0),
        _device("c", 0, 1),
        _device("b", 1, 0),
        cells_x=2,
        cells_y=2,
    )

    enriched = enrich_layout_semantics(spec, classification, layout)

    assert list(enriched.device_semantics_by_id) == ["a", "c", "b", "d"]
    assert all(isinstance(s.group_index, int) for s in enriched.device_semantics_by_id.values())
    out1 = debug_semantics(enriched)
    out2 = debug_semantics(enriched)
    assert out1 == out2


def test_semantic_enrichment_res_spec_sets_res_family() -> None:
    spec_dict = load_fixture("spec/fixtures/valid/res_array_minimal.json")
    spec_dict["inputs"]["topology"]["res_list"] = [2]
    spec_dict["inputs"]["topology"]["boundary_resistors"].update(
        {"left": True, "right": False, "top": False, "bottom": False}
    )
    spec = build_model(spec_dict)

    classification = GeneratedGridClassification(
        cells_x=2,
        cells_y=1,
        layers=1,
        tiles={(0, 0, 0): "device", (1, 0, 0): "device"},
    )
    layout = _layout_with_devices(_device("res_boundary", 0, 0), _device("res_core", 1, 0), cells_x=2, cells_y=1)

    enriched = enrich_layout_semantics(spec, classification, layout)

    assert enriched.device_semantics_by_id["res_boundary"].family == "res"
    assert enriched.device_semantics_by_id["res_boundary"].role == "boundary"
    assert enriched.device_semantics_by_id["res_boundary"].group_index == 0
    assert enriched.device_semantics_by_id["res_boundary"].boundary_device_size == spec.topology.boundary_resistors["boundary_device_size"]
    assert enriched.device_semantics_by_id["res_core"].family == "res"
    assert enriched.device_semantics_by_id["res_core"].role == "core"
    assert enriched.device_semantics_by_id["res_core"].group_index == 1


def test_semantic_enrichment_user_pattern_dummy_devices_are_group_zero() -> None:
    spec_dict = load_fixture("spec/fixtures/valid/cap_array_user_pattern.json")
    spec_dict["inputs"]["placement"]["pattern"] = [["C1_1", "C0_1"]]
    spec_dict["inputs"]["topology"]["boundary_caps"].update(
        {"left": False, "right": False, "top": False, "bottom": False}
    )
    spec = build_model(spec_dict)

    classification = GeneratedGridClassification(
        cells_x=2,
        cells_y=1,
        layers=1,
        tiles={(0, 0, 0): "device", (1, 0, 0): "device"},
    )
    layout = _layout_with_devices(_device("core", 0, 0), _device("dummy", 1, 0), cells_x=2, cells_y=1)

    enriched = enrich_layout_semantics(spec, classification, layout)

    assert enriched.device_semantics_by_id["core"].group_index == 1
    assert enriched.device_semantics_by_id["dummy"].group_index == 0
