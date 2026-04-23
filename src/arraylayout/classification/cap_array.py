"""Cap-array tile classification generator (V1).

V1 scope:
- only device-vs-wire classification
- no pins, no routing, no layout3d conversion

V1 layer rule:
- layer count is an explicit `generate(..., layers=...)` input (default: 1)
- the same XY classification is copied to every layer

V1 notes:
- `boundary_caps.boundary_device_size` is validated/acknowledged as boundary-device metadata
  (`unit`, `minimum`), but does not change V1 tile geometry.
- `connect_dummy_caps` does not change tile kinds in V1; it is validated/read and
  documented as a no-op for classification (electrical connectivity is out of scope).
- `common_centroid` uses a simple center-first placement heuristic (not an analog-
  quality placer), but it is intentionally different from side-by-side modes.
"""

from __future__ import annotations

import math

from ..spec.models import BoundaryDeviceSize, CapArraySpecModel
from .grid import GeneratedGridClassification, TileKind, iter_grid_coordinates

GridXY = tuple[int, int]


class CapArrayGridGenerator:
    """Generate a complete tile-kind classification for cap arrays."""

    def generate(self, spec: CapArraySpecModel, *, layers: int = 1) -> GeneratedGridClassification:
        if layers < 1:
            raise ValueError("layers must be >= 1")

        cells_x, cells_y, device_xy = _plan_device_tiles_xy(spec)

        tiles: dict[tuple[int, int, int], TileKind] = {}
        for x, y, layer in iter_grid_coordinates(cells_x=cells_x, cells_y=cells_y, layers=layers):
            tiles[(x, y, layer)] = "device" if (x, y) in device_xy else "wire"

        return GeneratedGridClassification(
            cells_x=cells_x,
            cells_y=cells_y,
            layers=layers,
            tiles=tiles,
        )

    def generate_tile_classification(
        self, spec: CapArraySpecModel, *, layers: int = 1
    ) -> GeneratedGridClassification:
        """Explicit alias for first-stage output generation."""
        return self.generate(spec, layers=layers)


def _plan_device_tiles_xy(spec: CapArraySpecModel) -> tuple[int, int, set[GridXY]]:
    core_cols, core_rows, core_device_xy = _plan_core_device_tiles_xy(spec)

    boundary = spec.topology.boundary_caps
    _validate_boundary_device_size_semantic(boundary["boundary_device_size"])

    # V1 geometry is side-flag driven only: each enabled side contributes one
    # boundary device ring. `boundary_device_size` is intentionally deferred metadata.
    left = 1 if bool(boundary["left"]) else 0
    right = 1 if bool(boundary["right"]) else 0
    top = 1 if bool(boundary["top"]) else 0
    bottom = 1 if bool(boundary["bottom"]) else 0

    cells_x = core_cols + left + right
    cells_y = core_rows + top + bottom

    shifted_core = {(x + left, y + top) for (x, y) in core_device_xy}
    boundary_device_xy = _plan_boundary_device_tiles_xy(
        cells_x=cells_x,
        cells_y=cells_y,
        left_thickness=left,
        right_thickness=right,
        top_thickness=top,
        bottom_thickness=bottom,
    )

    _ = spec.topology.connect_dummy_caps

    return cells_x, cells_y, shifted_core | boundary_device_xy


def _validate_boundary_device_size_semantic(boundary_device_size: BoundaryDeviceSize) -> None:
    if boundary_device_size in (BoundaryDeviceSize.UNIT, BoundaryDeviceSize.MINIMUM):
        return
    raise ValueError(f"unsupported boundary_device_size for V1 classification: {boundary_device_size!r}")


def _plan_core_device_tiles_xy(spec: CapArraySpecModel) -> tuple[int, int, set[GridXY]]:
    algorithm = spec.placement.algorithm

    if algorithm == "user":
        return _plan_user_pattern_xy(spec.placement.pattern)

    rows = spec.placement.rows
    cap_list = spec.topology.cap_list
    device_count = sum(cap_list)
    cols = max(1, math.ceil(device_count / rows))

    positions = _enumerate_positions(cols=cols, rows=rows, algorithm=algorithm)
    placed_positions = positions[:device_count]

    device_xy: set[GridXY] = set()
    cursor = 0
    for _group_index, count in enumerate(cap_list):
        for _ in range(count):
            device_xy.add(placed_positions[cursor])
            cursor += 1
    return cols, rows, device_xy


def _plan_user_pattern_xy(pattern: list[list[str]] | None) -> tuple[int, int, set[GridXY]]:
    if pattern is None or len(pattern) == 0:
        raise ValueError("placement.pattern must be non-empty when algorithm is 'user'")

    rows = len(pattern)
    cols = max((len(row) for row in pattern), default=0)
    if cols < 1:
        raise ValueError("placement.pattern rows must not be empty")

    device_xy: set[GridXY] = set()
    for y, row in enumerate(pattern):
        for x, device_name in enumerate(row):
            _validate_cap_device_name(device_name)
            device_xy.add((x, y))

    return cols, rows, device_xy


def _validate_cap_device_name(device_name: str) -> None:
    if "_" not in device_name:
        raise ValueError(f"invalid cap device name in pattern: {device_name!r}")
    prefix, _suffix = device_name.split("_", maxsplit=1)
    if len(prefix) < 2 or not prefix.startswith("C"):
        raise ValueError(f"invalid cap device name in pattern: {device_name!r}")

    numeric_part = prefix[1:]
    if not numeric_part.isdigit():
        raise ValueError(f"invalid cap device name in pattern: {device_name!r}")

    _ = int(numeric_part)


def _enumerate_positions(*, cols: int, rows: int, algorithm: str) -> list[GridXY]:
    if algorithm == "side-by-side":
        return [(x, y) for y in range(rows) for x in range(cols)]

    if algorithm == "side-by-side-row-wise":
        return [(x, y) for x in range(cols) for y in range(rows)]

    if algorithm == "common_centroid":
        return _center_first_positions(cols=cols, rows=rows)

    raise ValueError(f"unsupported placement algorithm: {algorithm!r}")


def _center_first_positions(*, cols: int, rows: int) -> list[GridXY]:
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
    return positions


def _plan_boundary_device_tiles_xy(
    *,
    cells_x: int,
    cells_y: int,
    left_thickness: int,
    right_thickness: int,
    top_thickness: int,
    bottom_thickness: int,
) -> set[GridXY]:
    device_xy: set[GridXY] = set()

    if left_thickness:
        for x in range(left_thickness):
            for y in range(cells_y):
                device_xy.add((x, y))
    if right_thickness:
        for x in range(cells_x - right_thickness, cells_x):
            for y in range(cells_y):
                device_xy.add((x, y))
    if top_thickness:
        for y in range(top_thickness):
            for x in range(cells_x):
                device_xy.add((x, y))
    if bottom_thickness:
        for y in range(cells_y - bottom_thickness, cells_y):
            for x in range(cells_x):
                device_xy.add((x, y))

    return device_xy
