from arraylayout.layout.build import skeleton_to_layout
from arraylayout.skeleton.models import (
    GeneratedDeviceStack,
    GeneratedLayoutSkeleton,
    GeneratedWireCell,
)
from layout3d.normalize import normalize_layout
from layout3d.validation import LayoutValidator


def _sample_skeleton() -> GeneratedLayoutSkeleton:
    return GeneratedLayoutSkeleton(
        cells_x=2,
        cells_y=1,
        layers=2,
        device_stacks=(
            GeneratedDeviceStack(
                generated_id="device_0_0_0_1",
                x=0,
                y=0,
                from_layer=0,
                to_layer=1,
            ),
        ),
        wire_cells=(
            GeneratedWireCell(generated_id="wire_1_0_0", x=1, y=0, layer=0),
            GeneratedWireCell(generated_id="wire_1_0_1", x=1, y=0, layer=1),
        ),
    )


def test_device_stack_maps_to_single_device_with_preserved_span() -> None:
    layout = skeleton_to_layout(_sample_skeleton())

    assert len(layout.devices) == 1
    device = layout.devices[0]
    assert (device.x, device.y) == (0, 0)
    assert (device.from_layer, device.to_layer) == (0, 1)
    assert device.pins == ()


def test_wire_cell_maps_to_wire_tile_with_preserved_coordinate() -> None:
    layout = skeleton_to_layout(_sample_skeleton())

    assert len(layout.wire_tiles) == 2
    coords = {(tile.x, tile.y, tile.layer) for tile in layout.wire_tiles}
    assert coords == {(1, 0, 0), (1, 0, 1)}


def test_multiple_stacks_and_wire_cells_map_1_to_1() -> None:
    skeleton = GeneratedLayoutSkeleton(
        cells_x=2,
        cells_y=2,
        layers=1,
        device_stacks=(
            GeneratedDeviceStack(generated_id="d_0_0_0_0", x=0, y=0, from_layer=0, to_layer=0),
            GeneratedDeviceStack(generated_id="d_1_0_0_0", x=1, y=0, from_layer=0, to_layer=0),
        ),
        wire_cells=(
            GeneratedWireCell(generated_id="w_0_1_0", x=0, y=1, layer=0),
            GeneratedWireCell(generated_id="w_1_1_0", x=1, y=1, layer=0),
        ),
    )

    layout = skeleton_to_layout(skeleton)

    assert len(layout.devices) == 2
    assert len(layout.wire_tiles) == 2


def test_output_is_valid_minimal_layout_and_ids_are_deterministic() -> None:
    skeleton = _sample_skeleton()

    layout_first = skeleton_to_layout(skeleton)
    layout_second = skeleton_to_layout(skeleton)

    assert layout_first == layout_second
    assert {d.device_id for d in layout_first.devices} == {"device_device_0_0_0_1"}
    assert {d.slot_id for d in layout_first.devices} == {"slot_device_0_0_0_1"}
    assert {w.wire_tile_id for w in layout_first.wire_tiles} == {
        "wire_tile_wire_1_0_0",
        "wire_tile_wire_1_0_1",
    }

    report = LayoutValidator().validate(normalize_layout(layout_first))
    assert report.ok


def test_no_accidental_routing_or_pin_semantics_are_introduced() -> None:
    layout = skeleton_to_layout(_sample_skeleton())

    assert all(device.pins == () for device in layout.devices)
    assert all(tile.ordered_wires == () for tile in layout.wire_tiles)
    assert all(tile.orientation == "horizontal" for tile in layout.wire_tiles)
