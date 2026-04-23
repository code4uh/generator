"""Semantic enrichment stage for generated minimal layouts (V1)."""

from __future__ import annotations

from ..models import CapArraySpecModel, ResArraySpecModel
from ..models.device_semantic import (
    EnrichedGeneratedLayout,
    GeneratedDeviceSemantic,
)
from ..models.enums import BoundaryDeviceSize
from ..models.grid_classification import GeneratedGridClassification
from layout3d.types import LayoutInstance


def _family_and_boundary_size(
    spec: CapArraySpecModel | ResArraySpecModel,
) -> tuple[str, BoundaryDeviceSize]:
    if isinstance(spec, CapArraySpecModel):
        return ("cap", spec.topology.boundary_caps["boundary_device_size"])
    if isinstance(spec, ResArraySpecModel):
        return ("res", spec.topology.boundary_resistors["boundary_device_size"])
    raise TypeError(f"Unsupported spec model type for semantic enrichment: {type(spec).__name__}")


def _boundary_side_for_position(*, x: int, y: int, max_x: int, max_y: int) -> str | None:
    if x == 0:
        return "left"
    if x == max_x:
        return "right"
    if y == 0:
        return "bottom"
    if y == max_y:
        return "top"
    return None


def _is_boundary_device(
    *,
    spec: CapArraySpecModel | ResArraySpecModel,
    x: int,
    y: int,
    max_x: int,
    max_y: int,
) -> bool:
    if isinstance(spec, CapArraySpecModel):
        boundary = spec.topology.boundary_caps
    else:
        boundary = spec.topology.boundary_resistors

    return (
        (bool(boundary["left"]) and x == 0)
        or (bool(boundary["right"]) and x == max_x)
        or (bool(boundary["top"]) and y == max_y)
        or (bool(boundary["bottom"]) and y == 0)
    )


def enrich_layout_semantics(
    spec: CapArraySpecModel | ResArraySpecModel,
    classification: GeneratedGridClassification,
    layout: LayoutInstance,
) -> EnrichedGeneratedLayout:
    """Enrich generated devices with minimal structural semantics."""

    family, boundary_device_size = _family_and_boundary_size(spec)
    max_x = classification.cells_x - 1
    max_y = classification.cells_y - 1

    ordered_devices = sorted(
        layout.devices,
        key=lambda device: (
            device.x,
            device.y,
            device.from_layer,
            device.to_layer,
            device.device_id,
        ),
    )

    semantics_by_id: dict[str, GeneratedDeviceSemantic] = {}
    for device in ordered_devices:
        role = (
            "boundary"
            if _is_boundary_device(
                spec=spec,
                x=device.x,
                y=device.y,
                max_x=max_x,
                max_y=max_y,
            )
            else "core"
        )
        # Group derivation from logical spec is deferred to a later stage.
        group_index = None

        boundary_side = None
        boundary_size = None
        if role == "boundary":
            boundary_side = _boundary_side_for_position(
                x=device.x,
                y=device.y,
                max_x=max_x,
                max_y=max_y,
            )
            boundary_size = boundary_device_size

        semantics_by_id[device.device_id] = GeneratedDeviceSemantic(
            family=family,
            role=role,
            group_index=group_index,
            boundary_side=boundary_side,
            boundary_device_size=boundary_size,
        )

    return EnrichedGeneratedLayout(layout=layout, device_semantics_by_id=semantics_by_id)
