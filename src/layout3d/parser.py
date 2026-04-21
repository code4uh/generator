"""Parsing-Schicht: raw dict -> Domänenmodell."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from .types import (
    Device,
    DevicePin,
    DevicePinAttachment,
    DeviceSlot,
    GridSize,
    LayoutInstance,
    LocalPos,
    PinGrid,
    Port,
    TileCoord,
    WireEntry,
    WireTile,
)


def parse_layout_json(payload: str) -> Mapping[str, Any]:
    return json.loads(payload)


def layout_to_dict(layout: LayoutInstance) -> dict[str, Any]:
    return {
        "schemaVersion": layout.schema_version,
        "templateRef": layout.template_ref,
        "grid": {
            "cellsX": layout.grid.cells_x,
            "cellsY": layout.grid.cells_y,
            "layers": layout.grid.layers,
        },
        "deviceSlots": [
            {
                "slotId": slot.slot_id,
                "allowedDeviceTypes": list(slot.allowed_device_types),
                "x": slot.x,
                "y": slot.y,
                "fromLayer": slot.from_layer,
                "toLayer": slot.to_layer,
            }
            for slot in layout.device_slots
        ],
        "devices": [
            {
                "deviceId": device.device_id,
                "deviceType": device.device_type,
                "slotId": device.slot_id,
                "x": device.x,
                "y": device.y,
                "fromLayer": device.from_layer,
                "toLayer": device.to_layer,
                "pinGrid": {
                    "cellsX": device.pin_grid.cells_x,
                    "cellsY": device.pin_grid.cells_y,
                },
                "pins": [
                    {
                        "pinId": pin.pin_id,
                        "tile": {"x": pin.tile.x, "y": pin.tile.y, "layer": pin.tile.layer},
                        "localPos": {"px": pin.local_pos.px, "py": pin.local_pos.py},
                        "attachment": {
                            "ports": [{"side": p.side, "pos_idx": p.pos_idx} for p in pin.attachment.ports]
                        },
                    }
                    for pin in device.pins
                ],
            }
            for device in layout.devices
        ],
        "wireTiles": [
            {
                "wireTileId": tile.wire_tile_id,
                "x": tile.x,
                "y": tile.y,
                "layer": tile.layer,
                "orderedWires": [
                    {
                        "wireId": entry.wire_id,
                        "wireType": entry.wire_type,
                        "netId": entry.net_id,
                        "orientation": entry.orientation,
                    }
                    for entry in tile.ordered_wires
                ],
            }
            for tile in layout.wire_tiles
        ],
    }


def layout_to_json(layout: LayoutInstance, *, indent: int = 2) -> str:
    return json.dumps(layout_to_dict(layout), indent=indent, sort_keys=True)


def _req(mapping: Mapping[str, Any], key: str, *, path: str | None = None) -> Any:
    if key not in mapping:
        if path is None:
            raise KeyError(key)
        raise KeyError(f"missing key '{key}' at {path}")
    return mapping[key]


def _as_str(value: Any, *, path: str | None = None) -> str:
    if not isinstance(value, str):
        suffix = f" at {path}" if path is not None else ""
        raise TypeError(f"expected str, got {type(value).__name__}{suffix}")
    return value


def _as_int(value: Any, *, path: str | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        suffix = f" at {path}" if path is not None else ""
        raise TypeError(f"expected int, got {type(value).__name__}{suffix}")
    return value


def _as_mapping(value: Any, *, path: str | None = None) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        suffix = f" at {path}" if path is not None else ""
        raise TypeError(f"expected mapping, got {type(value).__name__}{suffix}")
    return value


def _as_sequence(value: Any, *, path: str | None = None) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        suffix = f" at {path}" if path is not None else ""
        raise TypeError(f"expected sequence, got {type(value).__name__}{suffix}")
    return value


def parse_layout(data: Mapping[str, Any]) -> LayoutInstance:
    grid_raw = _as_mapping(_req(data, "grid", path="root"), path="grid")
    grid = GridSize(
        cells_x=_as_int(_req(grid_raw, "cellsX", path="grid"), path="grid.cellsX"),
        cells_y=_as_int(_req(grid_raw, "cellsY", path="grid"), path="grid.cellsY"),
        layers=_as_int(_req(grid_raw, "layers", path="grid"), path="grid.layers"),
    )

    slots = tuple(
        _parse_slot(item, idx) for idx, item in enumerate(_as_sequence(_req(data, "deviceSlots", path="root"), path="deviceSlots"))
    )
    devices = tuple(
        _parse_device(item, idx) for idx, item in enumerate(_as_sequence(_req(data, "devices", path="root"), path="devices"))
    )
    wire_tiles = tuple(
        _parse_wire_tile(item, idx)
        for idx, item in enumerate(_as_sequence(_req(data, "wireTiles", path="root"), path="wireTiles"))
    )

    return LayoutInstance(
        schema_version=_as_int(_req(data, "schemaVersion", path="root"), path="schemaVersion"),
        template_ref=_as_str(_req(data, "templateRef", path="root"), path="templateRef"),
        grid=grid,
        device_slots=slots,
        devices=devices,
        wire_tiles=wire_tiles,
    )


def _parse_slot(raw: Any, idx: int) -> DeviceSlot:
    base = f"deviceSlots[{idx}]"
    m = _as_mapping(raw, path=base)
    allowed = tuple(
        _as_str(item, path=f"{base}.allowedDeviceTypes[{allowed_idx}]")
        for allowed_idx, item in enumerate(_as_sequence(_req(m, "allowedDeviceTypes", path=base), path=f"{base}.allowedDeviceTypes"))
    )
    return DeviceSlot(
        slot_id=_as_str(_req(m, "slotId", path=base), path=f"{base}.slotId"),
        allowed_device_types=allowed,
        x=_as_int(_req(m, "x", path=base), path=f"{base}.x"),
        y=_as_int(_req(m, "y", path=base), path=f"{base}.y"),
        from_layer=_as_int(_req(m, "fromLayer", path=base), path=f"{base}.fromLayer"),
        to_layer=_as_int(_req(m, "toLayer", path=base), path=f"{base}.toLayer"),
    )


def _parse_device(raw: Any, idx: int) -> Device:
    base = f"devices[{idx}]"
    m = _as_mapping(raw, path=base)
    pin_grid_raw = _as_mapping(_req(m, "pinGrid", path=base), path=f"{base}.pinGrid")
    pins = tuple(
        _parse_pin(item, base=base, idx=pin_idx)
        for pin_idx, item in enumerate(_as_sequence(m.get("pins", ()), path=f"{base}.pins"))
    )
    return Device(
        device_id=_as_str(_req(m, "deviceId", path=base), path=f"{base}.deviceId"),
        device_type=_as_str(_req(m, "deviceType", path=base), path=f"{base}.deviceType"),
        slot_id=_as_str(_req(m, "slotId", path=base), path=f"{base}.slotId"),
        x=_as_int(_req(m, "x", path=base), path=f"{base}.x"),
        y=_as_int(_req(m, "y", path=base), path=f"{base}.y"),
        from_layer=_as_int(_req(m, "fromLayer", path=base), path=f"{base}.fromLayer"),
        to_layer=_as_int(_req(m, "toLayer", path=base), path=f"{base}.toLayer"),
        pin_grid=PinGrid(
            cells_x=_as_int(_req(pin_grid_raw, "cellsX", path=f"{base}.pinGrid"), path=f"{base}.pinGrid.cellsX"),
            cells_y=_as_int(_req(pin_grid_raw, "cellsY", path=f"{base}.pinGrid"), path=f"{base}.pinGrid.cellsY"),
        ),
        pins=pins,
    )


def _parse_pin(raw: Any, *, base: str, idx: int) -> DevicePin:
    pin_base = f"{base}.pins[{idx}]"
    m = _as_mapping(raw, path=pin_base)
    tile_raw = _as_mapping(_req(m, "tile", path=pin_base), path=f"{pin_base}.tile")
    pos_raw = _as_mapping(_req(m, "localPos", path=pin_base), path=f"{pin_base}.localPos")
    attachment_raw = _as_mapping(_req(m, "attachment", path=pin_base), path=f"{pin_base}.attachment")
    ports = tuple(
        _parse_port(item, base=pin_base, idx=port_idx)
        for port_idx, item in enumerate(_as_sequence(_req(attachment_raw, "ports", path=f"{pin_base}.attachment"), path=f"{pin_base}.attachment.ports"))
    )
    return DevicePin(
        pin_id=_as_str(_req(m, "pinId", path=pin_base), path=f"{pin_base}.pinId"),
        tile=TileCoord(
            x=_as_int(_req(tile_raw, "x", path=f"{pin_base}.tile"), path=f"{pin_base}.tile.x"),
            y=_as_int(_req(tile_raw, "y", path=f"{pin_base}.tile"), path=f"{pin_base}.tile.y"),
            layer=_as_int(_req(tile_raw, "layer", path=f"{pin_base}.tile"), path=f"{pin_base}.tile.layer"),
        ),
        local_pos=LocalPos(
            px=_as_int(_req(pos_raw, "px", path=f"{pin_base}.localPos"), path=f"{pin_base}.localPos.px"),
            py=_as_int(_req(pos_raw, "py", path=f"{pin_base}.localPos"), path=f"{pin_base}.localPos.py"),
        ),
        attachment=DevicePinAttachment(ports=ports),
    )


def _parse_port(raw: Any, *, base: str, idx: int) -> Port:
    port_base = f"{base}.attachment.ports[{idx}]"
    m = _as_mapping(raw, path=port_base)
    return Port(
        side=_as_str(_req(m, "side", path=port_base), path=f"{port_base}.side"),
        pos_idx=_as_int(_req(m, "pos_idx", path=port_base), path=f"{port_base}.pos_idx"),
    )


def _parse_wire_tile(raw: Any, idx: int) -> WireTile:
    base = f"wireTiles[{idx}]"
    m = _as_mapping(raw, path=base)
    entries = tuple(
        _parse_wire_entry(item, base=base, idx=entry_idx)
        for entry_idx, item in enumerate(_as_sequence(_req(m, "orderedWires", path=base), path=f"{base}.orderedWires"))
    )
    return WireTile(
        wire_tile_id=_as_str(_req(m, "wireTileId", path=base), path=f"{base}.wireTileId"),
        x=_as_int(_req(m, "x", path=base), path=f"{base}.x"),
        y=_as_int(_req(m, "y", path=base), path=f"{base}.y"),
        layer=_as_int(_req(m, "layer", path=base), path=f"{base}.layer"),
        ordered_wires=entries,
    )


def _parse_wire_entry(raw: Any, *, base: str, idx: int) -> WireEntry:
    entry_base = f"{base}.orderedWires[{idx}]"
    m = _as_mapping(raw, path=entry_base)
    return WireEntry(
        wire_id=_as_str(_req(m, "wireId", path=entry_base), path=f"{entry_base}.wireId"),
        wire_type=_as_str(_req(m, "wireType", path=entry_base), path=f"{entry_base}.wireType"),
        net_id=_as_str(_req(m, "netId", path=entry_base), path=f"{entry_base}.netId"),
        orientation=_as_str(_req(m, "orientation", path=entry_base), path=f"{entry_base}.orientation"),
    )
