"""Res-array tile classification generator (V1).

V1 scope:
- only device-vs-wire classification
- no pins, no routing, no layout3d conversion

V1 layer rule:
- layer count is an explicit `generate(..., layers=...)` input (default: 1)
- the same XY classification is copied to every layer

V1 notes:
- `placement.algorithm` is currently expected to be `side-by-side` for res arrays.
- `boundary_resistors.boundary_size` is validated/acknowledged as boundary-device
  metadata (`Unit`, `Minimum`), but does not change V1 tile geometry.
- `connect_dummy_res` does not change tile kinds in V1; it is treated as a
  deliberate no-op for this first classification stage.
"""

from __future__ import annotations

from .models import ResArraySpecModel
from .models.grid_classification import GeneratedGridClassification, TileKind, iter_grid_coordinates

GridXY = tuple[int, int]


class ResArrayGridGenerator:
    """Generate a complete tile-kind classification for resistor arrays."""

    def generate(self, spec: ResArraySpecModel, *, layers: int = 1) -> GeneratedGridClassification:
        if layers < 1:
            raise ValueError("layers must be >= 1")

        cells_x, cells_y, device_xy = _plan_device_tiles_xy(spec)

        tiles: dict[tuple[int, int, int], TileKind] = {}
        for x, y, layer in iter_grid_coordinates(cells_x=cells_x, cells_y=cells_y, layers=layers):
            tiles[(x, y, layer)] = "device" if (x, y) in device_xy else "wire"

        return GeneratedGridClassification(cells_x=cells_x, cells_y=cells_y, layers=layers, tiles=tiles)

    def generate_tile_classification(
        self, spec: ResArraySpecModel, *, layers: int = 1
    ) -> GeneratedGridClassification:
        """Explicit alias for first-stage output generation."""
        return self.generate(spec, layers=layers)


def _plan_device_tiles_xy(spec: ResArraySpecModel) -> tuple[int, int, set[GridXY]]:
    core_cols, core_rows, core_device_xy = _plan_core_device_tiles_xy(spec)

    boundary = spec.topology.boundary_resistors
    _validate_boundary_size_semantic(boundary["boundary_size"])

    # V1 geometry is side-flag driven only: each enabled side contributes one
    # boundary device ring. `boundary_size` is intentionally deferred metadata.
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

    _ = spec.topology.connect_dummy_res

    return cells_x, cells_y, shifted_core | boundary_device_xy


def _plan_core_device_tiles_xy(spec: ResArraySpecModel) -> tuple[int, int, set[GridXY]]:
    if spec.placement.algorithm != "side-by-side":
        raise ValueError(f"unsupported placement algorithm for res V1: {spec.placement.algorithm!r}")

    resistor_instances = sum(spec.topology.res_list) * spec.topology.parallel_res_no
    cols = max(1, resistor_instances)
    rows = 1

    return cols, rows, {(x, 0) for x in range(cols)}


def _validate_boundary_size_semantic(boundary_size: object) -> None:
    if boundary_size in ("Unit", "Minimum"):
        return
    raise ValueError(f"unsupported boundary_size for V1 classification: {boundary_size!r}")


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
