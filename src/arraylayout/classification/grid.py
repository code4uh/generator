"""Output model for first-stage grid tile classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

TileKind = Literal["device", "wire"]
GridCoordinate = tuple[int, int, int]


def iter_grid_coordinates(cells_x: int, cells_y: int, layers: int) -> Iterable[GridCoordinate]:
    """Yield all valid discrete coordinates for a grid shape."""
    for layer in range(layers):
        for y in range(cells_y):
            for x in range(cells_x):
                yield (x, y, layer)


@dataclass(frozen=True)
class GeneratedGridClassification:
    """Complete stage-2 grid classification (geometry only).

    Stage 2 intentionally carries only per-tile DEVICE/WIRE information on the
    discrete 3D grid. Logical grouping is handled in later semantic stages.
    """

    cells_x: int
    cells_y: int
    layers: int
    tiles: dict[GridCoordinate, TileKind]

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
