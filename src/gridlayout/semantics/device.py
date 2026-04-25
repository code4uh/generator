"""Semantic enrichment output models for generated layouts (V1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from layout3d.types import LayoutInstance

from ..spec.models.enums import BoundaryDeviceSize

BoundarySide = Literal["left", "right", "top", "bottom"]
DeviceFamily = Literal["cap", "res"]
DeviceRole = Literal["core", "boundary", "dummy"]


@dataclass(frozen=True)
class GeneratedDeviceSemantic:
    """Minimal semantic information for a generated layout device.

    Every semantic device belongs to exactly one logical group. Group ``0`` is
    reserved for boundary and dummy devices.
    """

    family: DeviceFamily
    role: DeviceRole
    group_index: int
    boundary_side: BoundarySide | None
    boundary_device_size: BoundaryDeviceSize | None


@dataclass(frozen=True)
class EnrichedGeneratedLayout:
    """Minimal layout plus semantic metadata keyed by ``device_id``."""

    layout: LayoutInstance
    device_semantics_by_id: dict[str, GeneratedDeviceSemantic]
