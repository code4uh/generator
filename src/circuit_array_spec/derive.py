"""Ableitungsfunktionen für Devices und Grids."""

from __future__ import annotations

import math
from typing import Any


def expand_cap_devices(spec: dict[str, Any]) -> dict[str, list[str]]:
    """Expandiere logische Caps zu realen Device-Namen C<i>_<j>."""
    cap_list = spec["inputs"]["topology"]["cap_list"]
    real_devices = [f"C{i}_{j}" for i, count in enumerate(cap_list, start=1) for j in range(1, count + 1)]
    return {"real": real_devices, "dummy": []}


def derive_cap_grid(spec: dict[str, Any]) -> list[list[str]]:
    """Leite ein Cap-Grid ab. Bei user-Algorithmus wird pattern direkt übernommen."""
    placement = spec["inputs"]["placement"]
    if placement["algorithm"] == "user":
        return placement["pattern"]

    rows = placement["rows"]
    real_devices = expand_cap_devices(spec)["real"]
    cols = max(1, math.ceil(len(real_devices) / rows))

    grid: list[list[str]] = []
    dummy_counter = 1
    cursor = 0
    for _ in range(rows):
        row: list[str] = []
        for _ in range(cols):
            if cursor < len(real_devices):
                row.append(real_devices[cursor])
                cursor += 1
            else:
                row.append(f"C0_{dummy_counter}")
                dummy_counter += 1
        grid.append(row)

    return grid


def expand_res_devices(spec: dict[str, Any]) -> dict[str, list[str]]:
    """Expandiere logische Resistoren zu R<divider>_<series>_<parallel>."""
    topology = spec["inputs"]["topology"]
    real_devices: list[str] = []

    for divider, series_count in enumerate(topology["res_list"], start=1):
        for series in range(1, series_count + 1):
            for parallel in range(1, topology["parallelResNo"] + 1):
                real_devices.append(f"R{divider}_{series}_{parallel}")

    return {"real": real_devices, "dummy": []}


def derive_res_grid(spec: dict[str, Any]) -> dict[str, Any]:
    """Leite rows/cols + Grid für res_array ab.

    Fachliche Regel (Markdown-Spec):
    rows = len(res_list) * parallelResNo, cols = max(res_list).
    """
    topology = spec["inputs"]["topology"]
    rows = len(topology["res_list"]) * topology["parallelResNo"]
    cols = max(topology["res_list"])

    grid: list[list[str]] = []
    dummy_counter = 1
    for divider, series_count in enumerate(topology["res_list"], start=1):
        for parallel in range(1, topology["parallelResNo"] + 1):
            row: list[str] = []
            for col in range(1, cols + 1):
                if col <= series_count:
                    row.append(f"R{divider}_{col}_{parallel}")
                else:
                    row.append(f"R0_{dummy_counter}")
                    dummy_counter += 1
            grid.append(row)

    return {"rows": rows, "cols": cols, "grid": grid}
