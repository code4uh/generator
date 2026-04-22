"""Transformation from generated skeleton to minimal ``layout3d`` objects.

This stage is intentionally structural only:
- no routing
- no pin generation
- no channel assignment
- no net connectivity
- no device-specific electrical semantics

Placeholder policy (deterministic):
- ``device_type``: ``"generated_device"``
- ``slot_id``: ``"slot_{GeneratedDeviceStack.generated_id}"``
- ``wire orientation``: always ``"horizontal"``
- ``pin_grid``: minimal valid ``1x1``
"""

from __future__ import annotations

from layout3d.types import Device, DeviceSlot, GridSize, LayoutInstance, PinGrid, WireTile

from ..models.layout_skeleton import GeneratedLayoutSkeleton

_PLACEHOLDER_DEVICE_TYPE = "generated_device"
_PLACEHOLDER_TEMPLATE_REF = "generated_layout_skeleton"
_PLACEHOLDER_SCHEMA_VERSION = 1
_PLACEHOLDER_WIRE_ORIENTATION = "horizontal"


def skeleton_to_layout(skeleton: GeneratedLayoutSkeleton) -> LayoutInstance:
    """Convert ``GeneratedLayoutSkeleton`` into a minimal valid ``LayoutInstance``.

    The conversion is a strict structural mapping of generated stacks and cells.
    It does not infer or add electrical intent.
    """

    devices = tuple(
        Device(
            device_id=f"device_{stack.generated_id}",
            device_type=_PLACEHOLDER_DEVICE_TYPE,
            slot_id=f"slot_{stack.generated_id}",
            x=stack.x,
            y=stack.y,
            from_layer=stack.from_layer,
            to_layer=stack.to_layer,
            pin_grid=PinGrid(cells_x=1, cells_y=1),
            pins=(),
        )
        for stack in skeleton.device_stacks
    )

    device_slots = tuple(
        DeviceSlot(
            slot_id=f"slot_{stack.generated_id}",
            allowed_device_types=(_PLACEHOLDER_DEVICE_TYPE,),
            x=stack.x,
            y=stack.y,
            from_layer=stack.from_layer,
            to_layer=stack.to_layer,
        )
        for stack in skeleton.device_stacks
    )

    wire_tiles = tuple(
        WireTile(
            wire_tile_id=f"wire_tile_{wire.generated_id}",
            x=wire.x,
            y=wire.y,
            layer=wire.layer,
            orientation=_PLACEHOLDER_WIRE_ORIENTATION,
            ordered_wires=(),
        )
        for wire in skeleton.wire_cells
    )

    return LayoutInstance(
        schema_version=_PLACEHOLDER_SCHEMA_VERSION,
        template_ref=_PLACEHOLDER_TEMPLATE_REF,
        grid=GridSize(cells_x=skeleton.cells_x, cells_y=skeleton.cells_y, layers=skeleton.layers),
        device_slots=device_slots,
        devices=devices,
        wire_tiles=wire_tiles,
    )
