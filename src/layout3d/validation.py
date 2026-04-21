"""Basis-Validatoren für das 3D-Layout."""

from __future__ import annotations

from .errors import ValidationIssue, ValidationReport
from .types import LayoutInstance, NormalizedLayout, Port, TileCoord

_VALID_PORT_SIDES = {"north", "east", "south", "west"}
_VALID_WIRE_ORIENTATION = {"horizontal", "vertical"}


class LayoutValidator:
    def validate(self, normalized: NormalizedLayout) -> ValidationReport:
        layout = normalized.layout
        issues: list[ValidationIssue] = []
        issues.extend(_validate_grid_dimensions(layout))
        issues.extend(_validate_id_integrity(normalized))
        issues.extend(_validate_device_slots(normalized))
        issues.extend(_validate_devices(normalized))
        issues.extend(_validate_device_overlap(normalized))
        issues.extend(_validate_pins(layout))
        issues.extend(_validate_wire_tiles(normalized))
        return ValidationReport(issues=tuple(issues))


def _validate_grid_dimensions(layout: LayoutInstance) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if layout.grid.cells_x <= 0:
        issues.append(_issue("GRID_DIMENSION", "grid", None, ("grid", "cellsX"), "cellsX must be > 0"))
    if layout.grid.cells_y <= 0:
        issues.append(_issue("GRID_DIMENSION", "grid", None, ("grid", "cellsY"), "cellsY must be > 0"))
    if layout.grid.layers <= 0:
        issues.append(_issue("GRID_DIMENSION", "grid", None, ("grid", "layers"), "layers must be > 0"))
    return issues


def _validate_id_integrity(normalized: NormalizedLayout) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for slot_id in normalized.duplicate_slot_ids:
        issues.append(_issue("DUPLICATE_SLOT_ID", "deviceSlot", slot_id, ("deviceSlots",), "slotId must be unique"))
    for device_id in normalized.duplicate_device_ids:
        issues.append(_issue("DUPLICATE_DEVICE_ID", "device", device_id, ("devices",), "deviceId must be unique"))
    for wire_tile_id in normalized.duplicate_wire_tile_ids:
        issues.append(
            _issue("DUPLICATE_WIRE_TILE_ID", "wireTile", wire_tile_id, ("wireTiles",), "wireTileId must be unique")
        )
    for coord in normalized.duplicate_wire_tile_coords:
        issues.append(
            _issue(
                "DUPLICATE_WIRE_TILE_COORD",
                "wireTile",
                None,
                ("wireTiles",),
                "max one wireTile per (x,y,layer)",
                tile={"x": coord.x, "y": coord.y, "layer": coord.layer},
            )
        )

    return issues


def _validate_device_slots(normalized: NormalizedLayout) -> list[ValidationIssue]:
    layout = normalized.layout
    issues: list[ValidationIssue] = []
    for slot in layout.device_slots:
        issues.extend(
            _validate_xy_layer_bounds(
                x=slot.x,
                y=slot.y,
                from_layer=slot.from_layer,
                to_layer=slot.to_layer,
                layout=layout,
                entity_type="deviceSlot",
                entity_id=slot.slot_id,
                location=("deviceSlots", slot.slot_id),
            )
        )
    return issues


def _validate_devices(normalized: NormalizedLayout) -> list[ValidationIssue]:
    layout = normalized.layout
    issues: list[ValidationIssue] = []

    for device in layout.devices:
        if device.pin_grid.cells_x <= 0:
            issues.append(
                _issue(
                    "PIN_GRID_DIMENSION",
                    "device",
                    device.device_id,
                    ("devices", device.device_id, "pinGrid", "cellsX"),
                    "pinGrid.cellsX must be > 0",
                )
            )
        if device.pin_grid.cells_y <= 0:
            issues.append(
                _issue(
                    "PIN_GRID_DIMENSION",
                    "device",
                    device.device_id,
                    ("devices", device.device_id, "pinGrid", "cellsY"),
                    "pinGrid.cellsY must be > 0",
                )
            )

        issues.extend(
            _validate_xy_layer_bounds(
                x=device.x,
                y=device.y,
                from_layer=device.from_layer,
                to_layer=device.to_layer,
                layout=layout,
                entity_type="device",
                entity_id=device.device_id,
                location=("devices", device.device_id),
            )
        )

        slot = normalized.slot_by_id.get(device.slot_id)
        if slot is None:
            issues.append(
                _issue("UNKNOWN_SLOT", "device", device.device_id, ("devices", device.device_id, "slotId"), "slotId not found")
            )
            continue

        if device.device_type not in slot.allowed_device_types:
            issues.append(
                _issue(
                    "DEVICE_TYPE_NOT_ALLOWED",
                    "device",
                    device.device_id,
                    ("devices", device.device_id, "deviceType"),
                    "deviceType not allowed by slot",
                    slot_id=slot.slot_id,
                )
            )

        if not _span_inside(device.x, device.y, device.from_layer, device.to_layer, slot.x, slot.y, slot.from_layer, slot.to_layer):
            issues.append(
                _issue(
                    "DEVICE_OUTSIDE_SLOT",
                    "device",
                    device.device_id,
                    ("devices", device.device_id),
                    "device must be fully contained in slot",
                    slot_id=slot.slot_id,
                )
            )

    return issues


def _validate_device_overlap(normalized: NormalizedLayout) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for tile, device_ids in normalized.device_ids_by_tile.items():
        if len(device_ids) > 1:
            for device_id in device_ids:
                others = tuple(other_id for other_id in device_ids if other_id != device_id)
                issues.append(
                    _issue(
                        "DEVICE_OVERLAP",
                        "device",
                        device_id,
                        ("devices", device_id),
                        "device overlaps another device",
                        tile={"x": tile.x, "y": tile.y, "layer": tile.layer},
                        other_device_ids=others,
                    )
                )
    return issues


def _validate_pins(layout: LayoutInstance) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for device in layout.devices:
        used_positions: set[tuple[TileCoord, int, int]] = set()
        for pin in device.pins:
            if pin.tile.x != device.x or pin.tile.y != device.y or not (device.from_layer <= pin.tile.layer <= device.to_layer):
                issues.append(
                    _issue(
                        "PIN_OUTSIDE_DEVICE",
                        "pin",
                        pin.pin_id,
                        ("devices", device.device_id, "pins", pin.pin_id, "tile"),
                        "pin tile must be inside device tile occupancy",
                        device_id=device.device_id,
                    )
                )

            if not (0 <= pin.local_pos.px < device.pin_grid.cells_x):
                issues.append(
                    _issue(
                        "PIN_LOCAL_POS",
                        "pin",
                        pin.pin_id,
                        ("devices", device.device_id, "pins", pin.pin_id, "localPos", "px"),
                        "px out of pin grid bounds",
                    )
                )
            if not (0 <= pin.local_pos.py < device.pin_grid.cells_y):
                issues.append(
                    _issue(
                        "PIN_LOCAL_POS",
                        "pin",
                        pin.pin_id,
                        ("devices", device.device_id, "pins", pin.pin_id, "localPos", "py"),
                        "py out of pin grid bounds",
                    )
                )

            pos_key = (pin.tile, pin.local_pos.px, pin.local_pos.py)
            if pos_key in used_positions:
                issues.append(
                    _issue(
                        "PIN_POSITION_DUPLICATE",
                        "pin",
                        pin.pin_id,
                        ("devices", device.device_id, "pins", pin.pin_id),
                        "(tile, px, py) must be unique per device",
                        device_id=device.device_id,
                    )
                )
            used_positions.add(pos_key)

            seen_ports: set[tuple[str, int]] = set()
            for port_idx, port in enumerate(pin.attachment.ports):
                issues.extend(
                    _validate_port(
                        port,
                        device.pin_grid.cells_x,
                        device.pin_grid.cells_y,
                        pin.pin_id,
                        device.device_id,
                        port_idx,
                    )
                )
                port_key = (port.side, port.pos_idx)
                if port_key in seen_ports:
                    issues.append(
                        _issue(
                            "DUPLICATE_PORT",
                            "pin",
                            pin.pin_id,
                            ("devices", device.device_id, "pins", pin.pin_id, "attachment", "ports"),
                            "duplicate port in pin",
                        )
                    )
                seen_ports.add(port_key)

    return issues


def _validate_wire_tiles(normalized: NormalizedLayout) -> list[ValidationIssue]:
    layout = normalized.layout
    issues: list[ValidationIssue] = []

    for tile in layout.wire_tiles:
        if not _xy_layer_in_grid(tile.x, tile.y, tile.layer, tile.layer, layout):
            issues.append(
                _issue(
                    "WIRE_TILE_OUT_OF_GRID",
                    "wireTile",
                    tile.wire_tile_id,
                    ("wireTiles", tile.wire_tile_id),
                    "wireTile coordinate out of grid",
                )
            )

        seen_wire_ids: set[str] = set()
        for entry in tile.ordered_wires:
            if entry.orientation not in _VALID_WIRE_ORIENTATION:
                issues.append(
                    _issue(
                        "WIRE_ORIENTATION",
                        "wire",
                        entry.wire_id,
                        ("wireTiles", tile.wire_tile_id, "orderedWires", entry.wire_id, "orientation"),
                        "invalid orientation",
                    )
                )
            if entry.wire_id in seen_wire_ids:
                issues.append(
                    _issue(
                        "DUPLICATE_WIRE_ID",
                        "wire",
                        entry.wire_id,
                        ("wireTiles", tile.wire_tile_id, "orderedWires"),
                        "wireId duplicated in same wireTile",
                        wire_tile_id=tile.wire_tile_id,
                    )
                )
            seen_wire_ids.add(entry.wire_id)

    return issues


def _validate_port(
    port: Port,
    cells_x: int,
    cells_y: int,
    pin_id: str,
    device_id: str,
    port_idx: int,
) -> list[ValidationIssue]:
    location = ("devices", device_id, "pins", pin_id, "attachment", "ports", str(port_idx))
    issues: list[ValidationIssue] = []
    if port.side not in _VALID_PORT_SIDES:
        issues.append(_issue("PORT_SIDE", "pin", pin_id, location + ("side",), "invalid port side"))
        return issues

    if port.side in {"north", "south"}:
        if not (0 <= port.pos_idx < cells_x):
            issues.append(
                _issue("PORT_POS_IDX", "pin", pin_id, location + ("pos_idx",), "pos_idx out of range for north/south")
            )
    else:
        if not (0 <= port.pos_idx < cells_y):
            issues.append(
                _issue("PORT_POS_IDX", "pin", pin_id, location + ("pos_idx",), "pos_idx out of range for east/west")
            )
    return issues


def _validate_xy_layer_bounds(
    x: int,
    y: int,
    from_layer: int,
    to_layer: int,
    layout: LayoutInstance,
    entity_type: str,
    entity_id: str | None,
    location: tuple[str, ...],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if from_layer > to_layer:
        issues.append(_issue("LAYER_SPAN", entity_type, entity_id, location, "fromLayer must be <= toLayer"))
    if not _xy_layer_in_grid(x, y, from_layer, to_layer, layout):
        issues.append(_issue("OUT_OF_GRID", entity_type, entity_id, location, "x/y/layer span outside grid bounds"))
    return issues


def _xy_layer_in_grid(x: int, y: int, from_layer: int, to_layer: int, layout: LayoutInstance) -> bool:
    return (
        0 <= x < layout.grid.cells_x
        and 0 <= y < layout.grid.cells_y
        and 0 <= from_layer < layout.grid.layers
        and 0 <= to_layer < layout.grid.layers
    )


def _span_inside(
    x: int,
    y: int,
    from_layer: int,
    to_layer: int,
    slot_x: int,
    slot_y: int,
    slot_from_layer: int,
    slot_to_layer: int,
) -> bool:
    return x == slot_x and y == slot_y and slot_from_layer <= from_layer <= to_layer <= slot_to_layer


def _issue(
    code: str,
    entity_type: str,
    entity_id: str | None,
    location: tuple[str, ...],
    message: str,
    **context: object,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        location=location,
        context=context,
    )
