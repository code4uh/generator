"""Interne tile-basierte Repräsentation."""

from __future__ import annotations

from dataclasses import dataclass

from .types import LayoutInstance, TileCoord, WireEntry


@dataclass(frozen=True)
class TileRepresentation:
    occupied_device_tiles: dict[TileCoord, str]
    wire_entries_by_tile: dict[TileCoord, tuple[WireEntry, ...]]
    pin_keys_by_device: dict[str, set[tuple[TileCoord, int, int]]]


def build_tile_representation(layout: LayoutInstance) -> TileRepresentation:
    occupied: dict[TileCoord, str] = {}
    pin_keys: dict[str, set[tuple[TileCoord, int, int]]] = {}

    for device in layout.devices:
        for layer in range(device.from_layer, device.to_layer + 1):
            coord = TileCoord(x=device.x, y=device.y, layer=layer)
            if coord in occupied:
                raise ValueError(
                    f"duplicate device coordinate ({coord.x}, {coord.y}, {coord.layer}) for "
                    f"{occupied[coord]!r} and {device.device_id!r}"
                )
            occupied[coord] = device.device_id
        pin_keys[device.device_id] = {
            (pin.tile, pin.local_pos.px, pin.local_pos.py)
            for pin in device.pins
        }

    wire_entries: dict[TileCoord, tuple[WireEntry, ...]] = {}
    for tile in layout.wire_tiles:
        coord = TileCoord(x=tile.x, y=tile.y, layer=tile.layer)
        if coord in wire_entries:
            raise ValueError(f"duplicate wireTile coordinate ({coord.x}, {coord.y}, {coord.layer})")
        wire_entries[coord] = tile.ordered_wires

    return TileRepresentation(
        occupied_device_tiles=occupied,
        wire_entries_by_tile=wire_entries,
        pin_keys_by_device=pin_keys,
    )
