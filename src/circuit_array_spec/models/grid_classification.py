"""Output model for first-stage grid tile classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

TileKind = Literal["device", "wire"]
GridCoordinate = tuple[int, int, int]
GridXYCoordinate = tuple[int, int]
GroupIndex = int | None


def iter_grid_coordinates(cells_x: int, cells_y: int, layers: int) -> Iterable[GridCoordinate]:
    """Yield all valid discrete coordinates for a grid shape."""
    for layer in range(layers):
        for y in range(cells_y):
            for x in range(cells_x):
                yield (x, y, layer)


@dataclass(frozen=True)
class GeneratedGridClassification:
    """Complete grid classification including per-XY device grouping.

    ``group_index_by_xy`` maps each device tile at coordinate ``(x, y)`` to a
    deterministic logical group index from the input spec.

    The mapping is XY-only (not layer-specific), because grouping is a 2D device
    placement property while tile kinds are still represented per ``(x, y, layer)``.

    Boundary devices are represented with ``None`` to keep them separate from
    normal numbered groups from ``cap_list`` / ``res_list``.
    """

    cells_x: int
    cells_y: int
    layers: int
    tiles: dict[GridCoordinate, TileKind]
    group_index_by_xy: dict[GridXYCoordinate, GroupIndex] | None = None

    def __post_init__(self) -> None:
        if self.cells_x < 1 or self.cells_y < 1 or self.layers < 1:
            raise ValueError("grid dimensions must be >= 1")

        expected = set(iter_grid_coordinates(self.cells_x, self.cells_y, self.layers))
        actual = set(self.tiles)

        out_of_grid = actual - expected
        if out_of_grid:
            raise ValueError(
                f"tile classification contains {len(out_of_grid)} out-of-grid coordinate(s)"
            )

        missing = expected - actual
        if missing:
            raise ValueError(
                f"tile classification incomplete, missing {len(missing)} coordinate(s)"
            )

        invalid_kinds = {kind for kind in self.tiles.values() if kind not in ("device", "wire")}
        if invalid_kinds:
            raise ValueError(f"invalid tile kinds: {sorted(invalid_kinds)}")

        if self.group_index_by_xy is None:
            object.__setattr__(self, "group_index_by_xy", {})

        group_index_by_xy = self.group_index_by_xy
        xy_coords = {(x, y) for (x, y, _layer) in expected}

        out_of_grid_xy = set(group_index_by_xy) - xy_coords
        if out_of_grid_xy:
            raise ValueError(
                f"group_index_by_xy contains {len(out_of_grid_xy)} out-of-grid coordinate(s)"
            )

        invalid_group_values = {
            value for value in group_index_by_xy.values() if value is not None and not isinstance(value, int)
        }
        if invalid_group_values:
            invalid_repr = sorted(repr(value) for value in invalid_group_values)
            raise ValueError(f"invalid group index values: {invalid_repr}")

        device_xy = {(x, y) for (x, y, _layer), kind in self.tiles.items() if kind == "device"}
        wire_xy = xy_coords - device_xy

        for x, y in sorted(device_xy):
            if (x, y) not in group_index_by_xy:
                raise ValueError(f"Missing group_index for device position ({x}, {y})")

        for x, y in sorted(wire_xy):
            if (x, y) in group_index_by_xy:
                raise ValueError(f"Wire position ({x}, {y}) must not have group_index")

    def tile_kind_at(self, x: int, y: int, layer: int) -> TileKind:
        return self.tiles[(x, y, layer)]


def create_uniform_classification(
    cells_x: int,
    cells_y: int,
    layers: int,
    kind: TileKind,
) -> GeneratedGridClassification:
    """Build a complete grid classification with one tile kind everywhere."""
    tiles = {coord: kind for coord in iter_grid_coordinates(cells_x, cells_y, layers)}
    return GeneratedGridClassification(cells_x=cells_x, cells_y=cells_y, layers=layers, tiles=tiles)
