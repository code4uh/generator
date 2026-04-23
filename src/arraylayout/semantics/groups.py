"""Semantic enrichment stage for generated minimal layouts (V1)."""

from __future__ import annotations

import math

from ..spec.models import CapArraySpecModel, ResArraySpecModel
from .device import (
    EnrichedGeneratedLayout,
    GeneratedDeviceSemantic,
)
from ..spec.models.enums import BoundaryDeviceSize
from ..classification.grid import GeneratedGridClassification
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


def _core_offsets(spec: CapArraySpecModel | ResArraySpecModel) -> tuple[int, int]:
    if isinstance(spec, CapArraySpecModel):
        boundary = spec.topology.boundary_caps
    else:
        boundary = spec.topology.boundary_resistors
    return (1 if bool(boundary["left"]) else 0, 1 if bool(boundary["top"]) else 0)


def _cap_group_from_name(device_name: str) -> int:
    prefix, _ = device_name.split("_", maxsplit=1)
    numeric_part = prefix[1:]
    return int(numeric_part)


def _cap_core_group_map(spec: CapArraySpecModel) -> dict[tuple[int, int], int]:
    left_offset, top_offset = _core_offsets(spec)
    mapping: dict[tuple[int, int], int] = {}

    if spec.placement.algorithm == "user":
        pattern = spec.placement.pattern
        if pattern is None:
            return mapping
        for y, row in enumerate(pattern):
            for x, device_name in enumerate(row):
                mapping[(x + left_offset, y + top_offset)] = _cap_group_from_name(device_name)
        return mapping

    rows = spec.placement.rows
    cap_list = spec.topology.cap_list
    device_count = sum(cap_list)
    cols = max(1, math.ceil(device_count / rows))

    if spec.placement.algorithm == "side-by-side":
        positions = [(x, y) for y in range(rows) for x in range(cols)]
    elif spec.placement.algorithm == "side-by-side-row-wise":
        positions = [(x, y) for x in range(cols) for y in range(rows)]
    elif spec.placement.algorithm == "common_centroid":
        center_x = (cols - 1) / 2.0
        center_y = (rows - 1) / 2.0
        positions = [(x, y) for y in range(rows) for x in range(cols)]
        positions.sort(
            key=lambda p: (
                abs(p[0] - center_x) + abs(p[1] - center_y),
                (p[0] + p[1]) % 2,
                abs(p[1] - center_y),
                abs(p[0] - center_x),
                p[1],
                p[0],
            )
        )
    else:
        return mapping

    cursor = 0
    for group_idx, count in enumerate(cap_list):
        group_index = group_idx + 1
        for _ in range(count):
            x, y = positions[cursor]
            mapping[(x + left_offset, y + top_offset)] = group_index
            cursor += 1
    return mapping


def _res_core_group_map(spec: ResArraySpecModel) -> dict[tuple[int, int], int]:
    left_offset, top_offset = _core_offsets(spec)
    mapping: dict[tuple[int, int], int] = {}
    cursor = 0
    for group_idx, count in enumerate(spec.topology.res_list):
        group_index = group_idx + 1
        for _series in range(count):
            for _parallel in range(spec.topology.parallel_res_no):
                mapping[(cursor + left_offset, top_offset)] = group_index
                cursor += 1
    return mapping


def enrich_layout_semantics(
    spec: CapArraySpecModel | ResArraySpecModel,
    classification: GeneratedGridClassification,
    layout: LayoutInstance,
) -> EnrichedGeneratedLayout:
    """Enrich generated devices with minimal structural semantics."""

    family, boundary_device_size = _family_and_boundary_size(spec)
    max_x = classification.cells_x - 1
    max_y = classification.cells_y - 1
    core_group_map = _cap_core_group_map(spec) if isinstance(spec, CapArraySpecModel) else _res_core_group_map(spec)

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
        group_index = 0 if role == "boundary" else core_group_map.get((device.x, device.y), 1)

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
