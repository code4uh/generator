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


def _req(mapping: Mapping[str, Any], key: str) -> Any:
    if key not in mapping:
        raise KeyError(key)
    return mapping[key]


def _as_str(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value).__name__}")
    return value


def _as_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"expected int, got {type(value).__name__}")
    return value


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"expected mapping, got {type(value).__name__}")
    return value


def _as_sequence(value: Any) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"expected sequence, got {type(value).__name__}")
    return value


def parse_layout(data: Mapping[str, Any]) -> LayoutInstance:
    grid_raw = _as_mapping(_req(data, "grid"))
    grid = GridSize(
        cells_x=_as_int(_req(grid_raw, "cellsX")),
        cells_y=_as_int(_req(grid_raw, "cellsY")),
        layers=_as_int(_req(grid_raw, "layers")),
    )

    slots = tuple(_parse_slot(item) for item in _as_sequence(_req(data, "deviceSlots")))
    devices = tuple(_parse_device(item) for item in _as_sequence(_req(data, "devices")))
    wire_tiles = tuple(_parse_wire_tile(item) for item in _as_sequence(_req(data, "wireTiles")))

    return LayoutInstance(
        schema_version=_as_int(_req(data, "schemaVersion")),
        template_ref=_as_str(_req(data, "templateRef")),
        grid=grid,
        device_slots=slots,
        devices=devices,
        wire_tiles=wire_tiles,
    )


def _parse_slot(raw: Any) -> DeviceSlot:
    m = _as_mapping(raw)
    allowed = tuple(_as_str(item) for item in _as_sequence(_req(m, "allowedDeviceTypes")))
    return DeviceSlot(
        slot_id=_as_str(_req(m, "slotId")),
        allowed_device_types=allowed,
        x=_as_int(_req(m, "x")),
        y=_as_int(_req(m, "y")),
        from_layer=_as_int(_req(m, "fromLayer")),
        to_layer=_as_int(_req(m, "toLayer")),
    )


def _parse_device(raw: Any) -> Device:
    m = _as_mapping(raw)
    pin_grid_raw = _as_mapping(_req(m, "pinGrid"))
    pins = tuple(_parse_pin(item) for item in _as_sequence(m.get("pins", ())))
    return Device(
        device_id=_as_str(_req(m, "deviceId")),
        device_type=_as_str(_req(m, "deviceType")),
        slot_id=_as_str(_req(m, "slotId")),
        x=_as_int(_req(m, "x")),
        y=_as_int(_req(m, "y")),
        from_layer=_as_int(_req(m, "fromLayer")),
        to_layer=_as_int(_req(m, "toLayer")),
        pin_grid=PinGrid(
            cells_x=_as_int(_req(pin_grid_raw, "cellsX")),
            cells_y=_as_int(_req(pin_grid_raw, "cellsY")),
        ),
        pins=pins,
    )


def _parse_pin(raw: Any) -> DevicePin:
    m = _as_mapping(raw)
    tile_raw = _as_mapping(_req(m, "tile"))
    pos_raw = _as_mapping(_req(m, "localPos"))
    attachment_raw = _as_mapping(_req(m, "attachment"))
    ports = tuple(_parse_port(item) for item in _as_sequence(_req(attachment_raw, "ports")))
    return DevicePin(
        pin_id=_as_str(_req(m, "pinId")),
        tile=TileCoord(
            x=_as_int(_req(tile_raw, "x")),
            y=_as_int(_req(tile_raw, "y")),
            layer=_as_int(_req(tile_raw, "layer")),
        ),
        local_pos=LocalPos(
            px=_as_int(_req(pos_raw, "px")),
            py=_as_int(_req(pos_raw, "py")),
        ),
        attachment=DevicePinAttachment(ports=ports),
    )


def _parse_port(raw: Any) -> Port:
    m = _as_mapping(raw)
    return Port(side=_as_str(_req(m, "side")), pos_idx=_as_int(_req(m, "pos_idx")))


def _parse_wire_tile(raw: Any) -> WireTile:
    m = _as_mapping(raw)
    entries = tuple(_parse_wire_entry(item) for item in _as_sequence(_req(m, "orderedWires")))
    return WireTile(
        wire_tile_id=_as_str(_req(m, "wireTileId")),
        x=_as_int(_req(m, "x")),
        y=_as_int(_req(m, "y")),
        layer=_as_int(_req(m, "layer")),
        ordered_wires=entries,
    )


def _parse_wire_entry(raw: Any) -> WireEntry:
    m = _as_mapping(raw)
    return WireEntry(
        wire_id=_as_str(_req(m, "wireId")),
        wire_type=_as_str(_req(m, "wireType")),
        net_id=_as_str(_req(m, "netId")),
        orientation=_as_str(_req(m, "orientation")),
    )
