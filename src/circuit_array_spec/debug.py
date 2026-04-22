"""Developer-focused deterministic debug text helpers for pipeline stages."""

from __future__ import annotations

from collections.abc import Mapping

from layout3d.types import LayoutInstance

from .models import CapArraySpecModel, ResArraySpecModel
from .models.grid_classification import GeneratedGridClassification
from .models.layout_skeleton import GeneratedLayoutSkeleton


def _format_bool(value: bool) -> str:
    return "true" if value else "false"


def _grid_rows(*, cells_x: int, cells_y: int, value_at: callable) -> list[str]:
    rows: list[str] = []
    for y in range(cells_y):
        row = [value_at(x, y) for x in range(cells_x)]
        rows.append(" ".join(row))
    return rows


def debug_spec(spec: CapArraySpecModel | ResArraySpecModel | Mapping[str, object]) -> str:
    """Return a compact deterministic text dump for the parsed spec model."""
    if isinstance(spec, CapArraySpecModel):
        boundary = spec.topology.boundary_caps
        lines = [
            "SpecModel",
            f"type={spec.type}",
            f"version={spec.version}",
            "topology",
            f"- cap_list={list(spec.topology.cap_list)}",
            f"- connection={spec.topology.connection}",
            f"- plus_connected={spec.topology.plus_connected}",
            f"- connect_dummy_caps={spec.topology.connect_dummy_caps}",
            "placement",
            f"- rows={spec.placement.rows}",
            f"- algorithm={spec.placement.algorithm}",
            f"- pattern={spec.placement.pattern}",
            "boundary",
            (
                "- flags: "
                f"left={_format_bool(bool(boundary['left']))} "
                f"right={_format_bool(bool(boundary['right']))} "
                f"top={_format_bool(bool(boundary['top']))} "
                f"bottom={_format_bool(bool(boundary['bottom']))}"
            ),
            f"- boundary_device_size={boundary['boundary_device_size']}",
        ]
        return "\n".join(lines)

    if isinstance(spec, ResArraySpecModel):
        boundary = spec.topology.boundary_resistors
        lines = [
            "SpecModel",
            f"type={spec.type}",
            f"version={spec.version}",
            "topology",
            f"- res_list={list(spec.topology.res_list)}",
            f"- parallel_res_no={spec.topology.parallel_res_no}",
            f"- connect_dummy_res={spec.topology.connect_dummy_res}",
            "placement",
            f"- algorithm={spec.placement.algorithm}",
            f"- pattern={spec.placement.pattern}",
            "boundary",
            (
                "- flags: "
                f"left={_format_bool(bool(boundary['left']))} "
                f"right={_format_bool(bool(boundary['right']))} "
                f"top={_format_bool(bool(boundary['top']))} "
                f"bottom={_format_bool(bool(boundary['bottom']))}"
            ),
            f"- boundary_device_size={boundary['boundary_device_size']}",
        ]
        return "\n".join(lines)

    if isinstance(spec, Mapping):
        return f"SpecMapping keys={sorted(str(k) for k in spec.keys())}"

    raise TypeError(f"Unsupported spec type for debug_spec: {type(spec).__name__}")


def debug_grid_classification(classification: GeneratedGridClassification) -> str:
    """Return deterministic layer grids and XY group index map."""
    lines = [
        "GeneratedGridClassification",
        (
            f"cells_x={classification.cells_x} "
            f"cells_y={classification.cells_y} "
            f"layers={classification.layers}"
        ),
        "",
    ]

    for layer in range(classification.layers):
        lines.append(f"Layer {layer}")
        layer_rows = _grid_rows(
            cells_x=classification.cells_x,
            cells_y=classification.cells_y,
            value_at=lambda x, y: "D"
            if classification.tile_kind_at(x, y, layer) == "device"
            else "W",
        )
        lines.extend(layer_rows)
        if layer + 1 < classification.layers:
            lines.append("")

    lines.extend(["", "group_index_by_xy"])

    def _group_value(x: int, y: int) -> str:
        group_index = classification.group_index_by_xy.get((x, y))
        has_device = any(
            classification.tile_kind_at(x, y, layer) == "device"
            for layer in range(classification.layers)
        )
        if not has_device:
            return "."
        if group_index is None:
            return "B"
        return str(group_index)

    lines.extend(
        _grid_rows(
            cells_x=classification.cells_x,
            cells_y=classification.cells_y,
            value_at=_group_value,
        )
    )

    return "\n".join(lines)


def debug_layout_skeleton(skeleton: GeneratedLayoutSkeleton) -> str:
    """Return deterministic summary for generated skeleton."""
    lines = [
        "GeneratedLayoutSkeleton",
        f"cells_x={skeleton.cells_x} cells_y={skeleton.cells_y} layers={skeleton.layers}",
        "",
        "device_stacks",
    ]

    stacks = sorted(
        skeleton.device_stacks,
        key=lambda stack: (stack.x, stack.y, stack.from_layer, stack.to_layer, stack.generated_id),
    )
    if not stacks:
        lines.append("- (none)")
    else:
        for stack in stacks:
            lines.append(
                f"- {stack.generated_id}: x={stack.x} y={stack.y} from={stack.from_layer} to={stack.to_layer}"
            )

    lines.extend(["", "wire_cells"])
    wires = sorted(
        skeleton.wire_cells,
        key=lambda wire: (wire.x, wire.y, wire.layer, wire.generated_id),
    )
    if not wires:
        lines.append("- (none)")
    else:
        for wire in wires:
            lines.append(f"- {wire.generated_id}: x={wire.x} y={wire.y} layer={wire.layer}")

    tile_map = {(wire.x, wire.y, wire.layer): "W" for wire in skeleton.wire_cells}
    for stack in skeleton.device_stacks:
        for layer in range(stack.from_layer, stack.to_layer + 1):
            tile_map[(stack.x, stack.y, layer)] = "D"

    lines.extend(["", "tile_summary"])
    for layer in range(skeleton.layers):
        lines.append(f"Layer {layer}")
        lines.extend(
            _grid_rows(
                cells_x=skeleton.cells_x,
                cells_y=skeleton.cells_y,
                value_at=lambda x, y: tile_map[(x, y, layer)],
            )
        )
        if layer + 1 < skeleton.layers:
            lines.append("")

    return "\n".join(lines)


def debug_layout(layout: LayoutInstance) -> str:
    """Return deterministic summary for minimal layout objects."""
    lines = [
        "LayoutInstance",
        f"devices={len(layout.devices)}",
        f"wire_tiles={len(layout.wire_tiles)}",
        "",
        "devices",
    ]

    devices = sorted(
        layout.devices,
        key=lambda device: (
            device.x,
            device.y,
            device.from_layer,
            device.to_layer,
            device.device_id,
        ),
    )
    if not devices:
        lines.append("- (none)")
    else:
        for device in devices:
            lines.append(
                "- "
                f"{device.device_id}: "
                f"x={device.x} y={device.y} "
                f"from={device.from_layer} to={device.to_layer} "
                f"device_type={device.device_type} slot_id={device.slot_id}"
            )

    lines.extend(["", "wire_tiles"])
    wire_tiles = sorted(
        layout.wire_tiles,
        key=lambda tile: (tile.x, tile.y, tile.layer, tile.wire_tile_id),
    )
    if not wire_tiles:
        lines.append("- (none)")
    else:
        for tile in wire_tiles:
            lines.append(
                f"- {tile.wire_tile_id}: x={tile.x} y={tile.y} layer={tile.layer} orientation={tile.orientation}"
            )

    pins_empty = all(device.pins == () for device in layout.devices)
    ordered_wires_empty = all(tile.ordered_wires == () for tile in layout.wire_tiles)

    if pins_empty:
        lines.append("")
        lines.append("note: all devices have empty pins")

    if ordered_wires_empty:
        lines.append("note: all wire_tiles have empty ordered_wires")

    return "\n".join(lines)
