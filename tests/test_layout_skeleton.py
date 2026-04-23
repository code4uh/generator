import pytest

from arraylayout.skeleton.transform import classification_to_layout_skeleton
from arraylayout.classification.grid import GeneratedGridClassification, iter_grid_coordinates
from arraylayout.skeleton.models import (
    GeneratedDeviceStack,
    GeneratedLayoutSkeleton,
    GeneratedWireCell,
)


def make_classification(
    *,
    cells_x: int,
    cells_y: int,
    layers: int,
    devices: set[tuple[int, int, int]],
) -> GeneratedGridClassification:
    tiles = {
        coord: ("device" if coord in devices else "wire")
        for coord in iter_grid_coordinates(cells_x, cells_y, layers)
    }
    return GeneratedGridClassification(
        cells_x=cells_x,
        cells_y=cells_y,
        layers=layers,
        tiles=tiles,
    )


def test_vertical_device_merging_contiguous_layers() -> None:
    classification = make_classification(
        cells_x=4,
        cells_y=3,
        layers=4,
        devices={(3, 2, 0), (3, 2, 1), (3, 2, 2)},
    )

    skeleton = classification_to_layout_skeleton(classification)

    stacks_at_xy = [s for s in skeleton.device_stacks if (s.x, s.y) == (3, 2)]
    assert len(stacks_at_xy) == 1
    assert stacks_at_xy[0].from_layer == 0
    assert stacks_at_xy[0].to_layer == 2


def test_no_merge_across_different_xy() -> None:
    classification = make_classification(
        cells_x=2,
        cells_y=2,
        layers=2,
        devices={(0, 0, 0), (1, 1, 1)},
    )

    skeleton = classification_to_layout_skeleton(classification)

    assert len(skeleton.device_stacks) == 2
    assert {(s.x, s.y) for s in skeleton.device_stacks} == {(0, 0), (1, 1)}


def test_no_merge_across_layer_gap() -> None:
    classification = make_classification(
        cells_x=1,
        cells_y=1,
        layers=3,
        devices={(0, 0, 0), (0, 0, 2)},
    )

    skeleton = classification_to_layout_skeleton(classification)

    assert len(skeleton.device_stacks) == 2
    spans = {(s.from_layer, s.to_layer) for s in skeleton.device_stacks}
    assert spans == {(0, 0), (2, 2)}


def test_wire_tiles_stay_separate_per_cell() -> None:
    classification = make_classification(
        cells_x=2,
        cells_y=1,
        layers=3,
        devices={(0, 0, 1)},
    )

    skeleton = classification_to_layout_skeleton(classification)

    expected_wire_cells = {
        (0, 0, 0),
        (0, 0, 2),
        (1, 0, 0),
        (1, 0, 1),
        (1, 0, 2),
    }
    assert {(w.x, w.y, w.layer) for w in skeleton.wire_cells} == expected_wire_cells


def test_full_representation_accounting() -> None:
    devices = {(0, 0, 0), (0, 0, 1), (1, 0, 2)}
    classification = make_classification(cells_x=2, cells_y=1, layers=3, devices=devices)

    skeleton = classification_to_layout_skeleton(classification)

    represented_device_tiles = {
        (stack.x, stack.y, layer)
        for stack in skeleton.device_stacks
        for layer in range(stack.from_layer, stack.to_layer + 1)
    }
    represented_wire_tiles = {(cell.x, cell.y, cell.layer) for cell in skeleton.wire_cells}

    expected_device_tiles = {coord for coord, kind in classification.tiles.items() if kind == "device"}
    expected_wire_tiles = {coord for coord, kind in classification.tiles.items() if kind == "wire"}

    assert represented_device_tiles == expected_device_tiles
    assert represented_wire_tiles == expected_wire_tiles
    assert represented_device_tiles.isdisjoint(represented_wire_tiles)


def test_skeleton_rejects_missing_coverage() -> None:
    with pytest.raises(ValueError, match="coverage"):
        GeneratedLayoutSkeleton(
            cells_x=1,
            cells_y=1,
            layers=2,
            device_stacks=(
                GeneratedDeviceStack(
                    generated_id="d0",
                    x=0,
                    y=0,
                    from_layer=0,
                    to_layer=0,
                ),
            ),
            wire_cells=(),
        )


def test_skeleton_rejects_overlap_between_device_and_wire() -> None:
    with pytest.raises(ValueError, match="overlap"):
        GeneratedLayoutSkeleton(
            cells_x=1,
            cells_y=1,
            layers=1,
            device_stacks=(
                GeneratedDeviceStack(
                    generated_id="d0",
                    x=0,
                    y=0,
                    from_layer=0,
                    to_layer=0,
                ),
            ),
            wire_cells=(
                GeneratedWireCell(
                    generated_id="w0",
                    x=0,
                    y=0,
                    layer=0,
                ),
            ),
        )


def test_skeleton_rejects_duplicate_wire_cell_coverage() -> None:
    with pytest.raises(ValueError, match="duplicate wire cell coordinate"):
        GeneratedLayoutSkeleton(
            cells_x=1,
            cells_y=1,
            layers=1,
            device_stacks=(),
            wire_cells=(
                GeneratedWireCell(
                    generated_id="w0",
                    x=0,
                    y=0,
                    layer=0,
                ),
                GeneratedWireCell(
                    generated_id="w1",
                    x=0,
                    y=0,
                    layer=0,
                ),
            ),
        )


def test_skeleton_accepts_valid_tuple_backed_representation() -> None:
    skeleton = GeneratedLayoutSkeleton(
        cells_x=1,
        cells_y=1,
        layers=2,
        device_stacks=(
            GeneratedDeviceStack(
                generated_id="d0",
                x=0,
                y=0,
                from_layer=0,
                to_layer=0,
            ),
        ),
        wire_cells=(
            GeneratedWireCell(
                generated_id="w0",
                x=0,
                y=0,
                layer=1,
            ),
        ),
    )

    assert isinstance(skeleton.device_stacks, tuple)
    assert isinstance(skeleton.wire_cells, tuple)
