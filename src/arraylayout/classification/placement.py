"""Shared non-semantic placement helpers for XY coordinate ordering."""

from __future__ import annotations

GridXY = tuple[int, int]


def enumerate_positions(*, cols: int, rows: int, algorithm: str) -> list[GridXY]:
    """Return deterministic XY traversal order for supported placement algorithms."""
    if algorithm == "side-by-side":
        return [(x, y) for y in range(rows) for x in range(cols)]

    if algorithm == "side-by-side-row-wise":
        return [(x, y) for x in range(cols) for y in range(rows)]

    if algorithm == "common_centroid":
        return center_first_positions(cols=cols, rows=rows)

    raise ValueError(f"unsupported placement algorithm: {algorithm!r}")


def center_first_positions(*, cols: int, rows: int) -> list[GridXY]:
    """Deterministic center-first ordering used by ``common_centroid`` in V1."""
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
