from circuit_array_spec.debug import (
    debug_grid_classification,
    debug_layout,
    debug_layout_skeleton,
)
from circuit_array_spec.models.grid_classification import GeneratedGridClassification
from circuit_array_spec.models.layout_skeleton import (
    GeneratedDeviceStack,
    GeneratedLayoutSkeleton,
    GeneratedWireCell,
)
from layout3d.types import Device, GridSize, LayoutInstance, PinGrid, WireTile


def test_debug_grid_classification_contains_expected_markers() -> None:
    classification = GeneratedGridClassification(
        cells_x=3,
        cells_y=2,
        layers=2,
        tiles={
            (0, 0, 0): "device",
            (1, 0, 0): "wire",
            (2, 0, 0): "wire",
            (0, 1, 0): "device",
            (1, 1, 0): "wire",
            (2, 1, 0): "device",
            (0, 0, 1): "device",
            (1, 0, 1): "wire",
            (2, 0, 1): "wire",
            (0, 1, 1): "wire",
            (1, 1, 1): "wire",
            (2, 1, 1): "device",
        },
    )

    output = debug_grid_classification(classification)

    assert "Layer 0" in output
    assert "Layer 1" in output
    assert "D W W" in output


def test_debug_layout_skeleton_includes_stacks_wires_and_tile_summary() -> None:
    skeleton = GeneratedLayoutSkeleton(
        cells_x=3,
        cells_y=1,
        layers=2,
        device_stacks=(
            GeneratedDeviceStack(generated_id="dev_0_0_0_1", x=0, y=0, from_layer=0, to_layer=1),
            GeneratedDeviceStack(generated_id="dev_2_0_1_1", x=2, y=0, from_layer=1, to_layer=1),
        ),
        wire_cells=(
            GeneratedWireCell(generated_id="wire_1_0_0", x=1, y=0, layer=0),
            GeneratedWireCell(generated_id="wire_1_0_1", x=1, y=0, layer=1),
            GeneratedWireCell(generated_id="wire_2_0_0", x=2, y=0, layer=0),
        ),
    )

    output = debug_layout_skeleton(skeleton)

    assert "device_stacks" in output
    assert "dev_0_0_0_1" in output
    assert "wire_cells" in output
    assert "wire_1_0_0" in output
    assert "tile_summary" in output
    assert "D W W" in output
    assert "D W D" in output


def test_debug_layout_includes_device_wire_and_empty_semantic_notes() -> None:
    layout = LayoutInstance(
        schema_version=1,
        template_ref="generated_layout_skeleton",
        grid=GridSize(cells_x=2, cells_y=1, layers=2),
        device_slots=(),
        devices=(
            Device(
                device_id="device_a",
                device_type="generated_device",
                slot_id="slot_a",
                x=0,
                y=0,
                from_layer=0,
                to_layer=1,
                pin_grid=PinGrid(cells_x=1, cells_y=1),
                pins=(),
            ),
        ),
        wire_tiles=(
            WireTile(
                wire_tile_id="wire_b",
                x=1,
                y=0,
                layer=1,
                orientation="horizontal",
                ordered_wires=(),
            ),
            WireTile(
                wire_tile_id="wire_a",
                x=1,
                y=0,
                layer=0,
                orientation="horizontal",
                ordered_wires=(),
            ),
        ),
    )

    output = debug_layout(layout)

    assert "devices=1" in output
    assert "wire_tiles=2" in output
    assert "device_a: x=0 y=0 from=0 to=1 device_type=generated_device slot_id=slot_a" in output
    assert "wire_a: x=1 y=0 layer=0 orientation=horizontal" in output
    assert "wire_b: x=1 y=0 layer=1 orientation=horizontal" in output
    assert "note: all devices have empty pins" in output
    assert "note: all wire_tiles have empty ordered_wires" in output


def test_debug_output_ordering_is_deterministic() -> None:
    layout = LayoutInstance(
        schema_version=1,
        template_ref="generated_layout_skeleton",
        grid=GridSize(cells_x=2, cells_y=2, layers=1),
        device_slots=(),
        devices=(
            Device(
                device_id="device_z",
                device_type="generated_device",
                slot_id="slot_z",
                x=1,
                y=1,
                from_layer=0,
                to_layer=0,
                pin_grid=PinGrid(cells_x=1, cells_y=1),
                pins=(),
            ),
            Device(
                device_id="device_a",
                device_type="generated_device",
                slot_id="slot_a",
                x=0,
                y=0,
                from_layer=0,
                to_layer=0,
                pin_grid=PinGrid(cells_x=1, cells_y=1),
                pins=(),
            ),
        ),
        wire_tiles=(
            WireTile(
                wire_tile_id="wire_z",
                x=1,
                y=0,
                layer=0,
                orientation="horizontal",
                ordered_wires=(),
            ),
            WireTile(
                wire_tile_id="wire_a",
                x=0,
                y=1,
                layer=0,
                orientation="horizontal",
                ordered_wires=(),
            ),
        ),
    )

    out1 = debug_layout(layout)
    out2 = debug_layout(layout)

    assert out1 == out2
    assert out1.index("device_a") < out1.index("device_z")
    assert out1.index("wire_a") < out1.index("wire_z")
