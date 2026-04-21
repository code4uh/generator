"""Tile classification output model for generator pre-layout stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

TileKind = Literal["device", "wire"]
GridCoordinate = tuple[int, int, int]


def iter_grid_coordinates(width: int, height: int, layers: int) -> Iterable[GridCoordinate]:
    """Yield all valid (x, y, layer) coordinates for the discrete grid shape."""
    for layer in range(layers):
        for y in range(height):
            for x in range(width):
                yield (x, y, layer)


@dataclass(frozen=True)
class GeneratedGridClassification:
    """Complete, unambiguous tile classification for a discrete 3D grid."""

    width: int
    height: int
    layers: int
    tiles: dict[GridCoordinate, TileKind]

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1 or self.layers < 1:
            raise ValueError("grid dimensions must be >= 1")

        expected = set(iter_grid_coordinates(self.width, self.height, self.layers))
        actual = set(self.tiles)

        extra = actual - expected
        if extra:
            raise ValueError(f"tile classification contains {len(extra)} out-of-grid coordinate(s)")

        missing = expected - actual
        if missing:
            raise ValueError(f"tile classification incomplete, missing {len(missing)} coordinate(s)")

        invalid_kinds = {kind for kind in self.tiles.values() if kind not in ("device", "wire")}
        if invalid_kinds:
            raise ValueError(f"invalid tile kinds: {sorted(invalid_kinds)}")

    def tile_kind_at(self, x: int, y: int, layer: int) -> TileKind:
        """Return tile kind for a valid grid coordinate."""
        return self.tiles[(x, y, layer)]


def create_uniform_classification(width: int, height: int, layers: int, kind: TileKind) -> GeneratedGridClassification:
    """Build a complete classification with the same tile kind for all coordinates."""
    tiles = {coord: kind for coord in iter_grid_coordinates(width, height, layers)}
    return GeneratedGridClassification(width=width, height=height, layers=layers, tiles=tiles)
