"""Backward-compatible re-export for grid classification output model."""

from .models.grid_classification import (
    GeneratedGridClassification,
    GridCoordinate,
    TileKind,
    create_uniform_classification,
    iter_grid_coordinates,
)

__all__ = [
    "TileKind",
    "GridCoordinate",
    "GeneratedGridClassification",
    "iter_grid_coordinates",
    "create_uniform_classification",
]
