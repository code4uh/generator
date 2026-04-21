"""Normalisierungsschicht für deterministische Reihenfolgen und Lookups."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .types import (
    Device,
    DevicePin,
    DevicePinAttachment,
    LayoutInstance,
    NormalizedLayout,
    TileCoord,
    WireEntry,
    WireTile,
)

T = TypeVar("T")


def normalize_layout(layout: LayoutInstance) -> NormalizedLayout:
    slots = tuple(sorted(layout.device_slots, key=lambda s: s.slot_id))
    devices = tuple(sorted((_normalize_device(d) for d in layout.devices), key=lambda d: d.device_id))
    wire_tiles = tuple(sorted(layout.wire_tiles, key=lambda w: (w.layer, w.y, w.x, w.wire_tile_id)))

    normalized_layout = LayoutInstance(
        schema_version=layout.schema_version,
        template_ref=layout.template_ref,
        grid=layout.grid,
        device_slots=slots,
        devices=devices,
        wire_tiles=wire_tiles,
    )

    slot_by_id, duplicate_slot_ids = _index_by_id(slots, lambda slot: slot.slot_id)
    device_by_id, duplicate_device_ids = _index_by_id(devices, lambda device: device.device_id)

    device_tiles_by_id = {
        device.device_id: frozenset(
            TileCoord(device.x, device.y, layer) for layer in range(device.from_layer, device.to_layer + 1)
        )
        for device in devices
    }

    tile_to_device_ids: dict[TileCoord, list[str]] = {}
    for device_id, tiles in device_tiles_by_id.items():
        for tile in tiles:
            tile_to_device_ids.setdefault(tile, []).append(device_id)
    device_ids_by_tile = {tile: tuple(sorted(device_ids)) for tile, device_ids in tile_to_device_ids.items()}

    wire_tile_by_coord: dict[TileCoord, WireTile] = {}
    wire_entries_by_coord: dict[TileCoord, tuple[WireEntry, ...]] = {}
    duplicate_wire_tile_ids: list[str] = []
    seen_wire_tile_ids: set[str] = set()

    for wire_tile in wire_tiles:
        coord = TileCoord(wire_tile.x, wire_tile.y, wire_tile.layer)
        wire_tile_by_coord[coord] = wire_tile
        wire_entries_by_coord[coord] = wire_tile.ordered_wires
        if wire_tile.wire_tile_id in seen_wire_tile_ids:
            duplicate_wire_tile_ids.append(wire_tile.wire_tile_id)
        seen_wire_tile_ids.add(wire_tile.wire_tile_id)

    return NormalizedLayout(
        layout=normalized_layout,
        slot_by_id=slot_by_id,
        device_by_id=device_by_id,
        device_tiles_by_id=device_tiles_by_id,
        device_ids_by_tile=device_ids_by_tile,
        wire_tile_by_coord=wire_tile_by_coord,
        wire_entries_by_coord=wire_entries_by_coord,
        duplicate_slot_ids=tuple(sorted(set(duplicate_slot_ids))),
        duplicate_device_ids=tuple(sorted(set(duplicate_device_ids))),
        duplicate_wire_tile_ids=tuple(sorted(set(duplicate_wire_tile_ids))),
    )


def _normalize_device(device: Device) -> Device:
    pins = tuple(
        sorted(
            (_normalize_pin(pin) for pin in device.pins),
            key=lambda p: (p.tile.layer, p.tile.y, p.tile.x, p.local_pos.py, p.local_pos.px, p.pin_id),
        )
    )
    return Device(
        device_id=device.device_id,
        device_type=device.device_type,
        slot_id=device.slot_id,
        x=device.x,
        y=device.y,
        from_layer=device.from_layer,
        to_layer=device.to_layer,
        pin_grid=device.pin_grid,
        pins=pins,
    )


def _normalize_pin(pin: DevicePin) -> DevicePin:
    ports = tuple(sorted(pin.attachment.ports, key=lambda p: (p.side, p.pos_idx)))
    return DevicePin(
        pin_id=pin.pin_id,
        tile=pin.tile,
        local_pos=pin.local_pos,
        attachment=DevicePinAttachment(ports=ports),
    )


def _index_by_id(items: tuple[T, ...], id_getter: Callable[[T], str]) -> tuple[dict[str, T], list[str]]:
    indexed: dict[str, T] = {}
    duplicates: list[str] = []
    for item in items:
        item_id = id_getter(item)
        if item_id in indexed:
            duplicates.append(item_id)
            continue
        indexed[item_id] = item
    return indexed, duplicates
