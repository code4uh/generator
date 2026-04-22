"""Cap-array tile classification generator (V1).

V1 scope:
- only device-vs-wire classification
- no pins, no routing, no layout3d conversion

Layer rule (explicit V1):
- the same XY classification is applied on every layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .models.grid_classification import GeneratedGridClassification, TileKind, iter_grid_coordinates


@dataclass(frozen=True)
class CapArrayGridGenerator:
    """Generate a complete tile-kind classification for cap arrays."""

    layers: int = 1

    def generate(self, spec: dict[str, Any]) -> GeneratedGridClassification:
        cells_x, cells_y, device_xy = _plan_device_tiles_xy(spec)

        tiles: dict[tuple[int, int, int], TileKind] = {}
        for x, y, layer in iter_grid_coordinates(cells_x=cells_x, cells_y=cells_y, layers=self.layers):
            tiles[(x, y, layer)] = "device" if (x, y) in device_xy else "wire"

        return GeneratedGridClassification(cells_x=cells_x, cells_y=cells_y, layers=self.layers, tiles=tiles)


def _plan_device_tiles_xy(spec: dict[str, Any]) -> tuple[int, int, set[tuple[int, int]]]:
    topology = spec["inputs"]["topology"]
    placement = spec["inputs"]["placement"]

    core_cols, core_rows, core_device_xy = _plan_core_device_tiles_xy(topology=topology, placement=placement)

    boundary = topology["boundary_caps"]
    left = 1 if boundary["left"] else 0
    right = 1 if boundary["right"] else 0
    top = 1 if boundary["top"] else 0
    bottom = 1 if boundary["bottom"] else 0

    cells_x = core_cols + left + right
    cells_y = core_rows + top + bottom

    shifted_core = {(x + left, y + top) for (x, y) in core_device_xy}
    boundary_device_xy = _plan_boundary_device_tiles_xy(
        cells_x=cells_x,
        cells_y=cells_y,
        left_enabled=bool(left),
        right_enabled=bool(right),
        top_enabled=bool(top),
        bottom_enabled=bool(bottom),
    )

    return cells_x, cells_y, shifted_core | boundary_device_xy


def _plan_core_device_tiles_xy(
    topology: dict[str, Any], placement: dict[str, Any]
) -> tuple[int, int, set[tuple[int, int]]]:
    algorithm = placement["algorithm"]

    if algorithm == "user":
        pattern = placement["pattern"]
        if pattern is None or len(pattern) == 0:
            raise ValueError("placement.pattern must be non-empty when algorithm is 'user'")

        rows = len(pattern)
        cols = max((len(row) for row in pattern), default=0)
        if cols < 1:
            raise ValueError("placement.pattern rows must not be empty")

        device_xy: set[tuple[int, int]] = set()
        for y, row in enumerate(pattern):
            for x, _device_name in enumerate(row):
                device_xy.add((x, y))
        return cols, rows, device_xy

    rows = placement["rows"]
    device_count = sum(topology["cap_list"])
    cols = max(1, math.ceil(device_count / rows))

    device_xy = set()
    cursor = 0
    for y in range(rows):
        for x in range(cols):
            if cursor < device_count:
                device_xy.add((x, y))
                cursor += 1

    return cols, rows, device_xy


def _plan_boundary_device_tiles_xy(
    *,
    cells_x: int,
    cells_y: int,
    left_enabled: bool,
    right_enabled: bool,
    top_enabled: bool,
    bottom_enabled: bool,
) -> set[tuple[int, int]]:
    device_xy: set[tuple[int, int]] = set()

    if left_enabled:
        for y in range(cells_y):
            device_xy.add((0, y))
    if right_enabled:
        for y in range(cells_y):
            device_xy.add((cells_x - 1, y))
    if top_enabled:
        for x in range(cells_x):
            device_xy.add((x, 0))
    if bottom_enabled:
        for x in range(cells_x):
            device_xy.add((x, cells_y - 1))

    return device_xy
