"""Domänentypen für ein strikt diskretes rasterbasiertes 3D-Layout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PortSide = Literal["north", "east", "south", "west"]
WireOrientation = Literal["horizontal", "vertical"]


@dataclass(frozen=True)
class GridSize:
    cells_x: int
    cells_y: int
    layers: int


@dataclass(frozen=True)
class TileCoord:
    x: int
    y: int
    layer: int


@dataclass(frozen=True)
class Port:
    side: PortSide
    pos_idx: int


@dataclass(frozen=True)
class DevicePinAttachment:
    ports: tuple[Port, ...]


@dataclass(frozen=True)
class LocalPos:
    px: int
    py: int


@dataclass(frozen=True)
class PinGrid:
    cells_x: int
    cells_y: int


@dataclass(frozen=True)
class DevicePin:
    pin_id: str
    tile: TileCoord
    local_pos: LocalPos
    attachment: DevicePinAttachment


@dataclass(frozen=True)
class Device:
    device_id: str
    device_type: str
    slot_id: str
    x: int
    y: int
    from_layer: int
    to_layer: int
    pin_grid: PinGrid
    pins: tuple[DevicePin, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DeviceSlot:
    slot_id: str
    allowed_device_types: tuple[str, ...]
    x: int
    y: int
    from_layer: int
    to_layer: int


@dataclass(frozen=True)
class WireEntry:
    wire_id: str
    wire_type: str
    net_id: str
    orientation: WireOrientation


@dataclass(frozen=True)
class WireTile:
    wire_tile_id: str
    x: int
    y: int
    layer: int
    ordered_wires: tuple[WireEntry, ...]


@dataclass(frozen=True)
class LayoutInstance:
    schema_version: int
    template_ref: str
    grid: GridSize
    device_slots: tuple[DeviceSlot, ...]
    devices: tuple[Device, ...]
    wire_tiles: tuple[WireTile, ...]


@dataclass(frozen=True)
class NormalizedLayout:
    """Deterministische Instanz inklusive vorberechneter Lookups."""

    layout: LayoutInstance
    slot_by_id: dict[str, DeviceSlot]
    device_by_id: dict[str, Device]
    device_tiles_by_id: dict[str, frozenset[TileCoord]]
    device_ids_by_tile: dict[TileCoord, tuple[str, ...]]
    wire_tile_by_coord: dict[TileCoord, WireTile]
    wire_entries_by_coord: dict[TileCoord, tuple[WireEntry, ...]]
    duplicate_slot_ids: tuple[str, ...] = ()
    duplicate_device_ids: tuple[str, ...] = ()
    duplicate_wire_tile_ids: tuple[str, ...] = ()
