"""Transformation from full grid classification to intermediate layout skeleton."""

from __future__ import annotations

from ..classification.grid import GeneratedGridClassification
from .models import (
    GeneratedDeviceStack,
    GeneratedLayoutSkeleton,
    GeneratedWireCell,
)


def classification_to_layout_skeleton(
    classification: GeneratedGridClassification,
) -> GeneratedLayoutSkeleton:
    """Convert tile classification into a minimal layout-like intermediate form.

    Device tiles are merged only along contiguous vertical layers at identical
    ``(x, y)``. Wire tiles remain one generated cell per classified wire tile.
    """

    device_stacks: list[GeneratedDeviceStack] = []
    wire_cells: list[GeneratedWireCell] = []

    for y in range(classification.cells_y):
        for x in range(classification.cells_x):
            layer = 0
            while layer < classification.layers:
                kind = classification.tile_kind_at(x, y, layer)
                if kind == "wire":
                    wire_cells.append(
                        GeneratedWireCell(
                            generated_id=f"wire_{x}_{y}_{layer}",
                            x=x,
                            y=y,
                            layer=layer,
                        )
                    )
                    layer += 1
                    continue

                run_start = layer
                run_end = layer
                while run_end + 1 < classification.layers and classification.tile_kind_at(
                    x, y, run_end + 1
                ) == "device":
                    run_end += 1

                device_stacks.append(
                    GeneratedDeviceStack(
                        generated_id=f"device_{x}_{y}_{run_start}_{run_end}",
                        x=x,
                        y=y,
                        from_layer=run_start,
                        to_layer=run_end,
                    )
                )
                layer = run_end + 1

    skeleton = GeneratedLayoutSkeleton(
        cells_x=classification.cells_x,
        cells_y=classification.cells_y,
        layers=classification.layers,
        device_stacks=tuple(device_stacks),
        wire_cells=tuple(wire_cells),
    )

    represented_device_tiles = {
        (stack.x, stack.y, layer)
        for stack in skeleton.device_stacks
        for layer in range(stack.from_layer, stack.to_layer + 1)
    }
    represented_wire_tiles = {(cell.x, cell.y, cell.layer) for cell in skeleton.wire_cells}

    input_device_tiles = {
        coord for coord, kind in classification.tiles.items() if kind == "device"
    }
    input_wire_tiles = {coord for coord, kind in classification.tiles.items() if kind == "wire"}

    if represented_device_tiles != input_device_tiles:
        raise ValueError("device tile representation mismatch in layout skeleton conversion")

    if represented_wire_tiles != input_wire_tiles:
        raise ValueError("wire tile representation mismatch in layout skeleton conversion")

    return skeleton
