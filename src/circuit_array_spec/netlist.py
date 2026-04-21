"""SPICE-ähnliche Netlist-Generierung für Circuit-Array-Specs."""

from __future__ import annotations

import re
from typing import Any

from .derive import derive_cap_grid, derive_res_grid


def _parse_plus_connected(value: str) -> list[list[int]]:
    groups: list[list[int]] = []
    for match in re.finditer(r"\(([^)]*)\)", value):
        indices = [int(item.strip()) for item in match.group(1).split(",") if item.strip()]
        if indices:
            groups.append(indices)
    return groups


def _cap_plus_nets(spec: dict[str, Any]) -> dict[int, str]:
    topology = spec["inputs"]["topology"]
    cap_count = len(topology["cap_list"])

    if topology["connection"] == "shortPlusPins":
        return {cap_idx: "G1_p" for cap_idx in range(1, cap_count + 1)}

    if topology["connection"] == "userDefined":
        plus_connected: str = topology["plusConnected"]
        groups = _parse_plus_connected(plus_connected)

        nets = {cap_idx: f"G{cap_idx}_p" for cap_idx in range(1, cap_count + 1)}
        for group_idx, group in enumerate(groups, start=1):
            net = f"G{group_idx}_p"
            for cap_idx in group:
                nets[cap_idx] = net
        return nets

    return {cap_idx: f"G{cap_idx}_p" for cap_idx in range(1, cap_count + 1)}


def _cap_dummy_nets(connect_dummy_caps: str, dummy_name: str) -> tuple[str, str]:
    if connect_dummy_caps == "open_shorted":
        net = f"{dummy_name}_s"
        return net, net
    if connect_dummy_caps == "shorted_G1_p":
        return "G1_p", "Cdmy_n"
    if connect_dummy_caps == "shorted_Cdmy_p":
        return "Cdmy_p", "Cdmy_n"
    if connect_dummy_caps == "Cdmy_p+Cdmy_n":
        return "Cdmy", "Cdmy"
    return f"{dummy_name}_p", f"{dummy_name}_n"


def _generate_cap_netlist(spec: dict[str, Any]) -> str:
    topology = spec["inputs"]["topology"]
    plus_nets = _cap_plus_nets(spec)

    lines: list[str] = ["* cap_array", ".SUBCKT cap_array"]

    for cap_idx, count in enumerate(topology["cap_list"], start=1):
        for instance_idx in range(1, count + 1):
            name = f"C{cap_idx}_{instance_idx}"
            lines.append(f"{name} {plus_nets[cap_idx]} GND CUNIT")

    grid = derive_cap_grid(spec)
    dummies = sorted({cell for row in grid["grid"] for cell in row if cell.startswith("C0_")})
    for dummy in dummies:
        plus_net, minus_net = _cap_dummy_nets(topology["connectDummyCaps"], dummy)
        lines.append(f"{dummy} {plus_net} {minus_net} CUNIT_DMY")

    lines.append(".ENDS cap_array")
    return "\n".join(lines)


def _res_dummy_nets(connect_dummy_res: str, dummy_name: str) -> tuple[str, str]:
    if connect_dummy_res == "VSS":
        return "VSS", "VSS"
    return f"{dummy_name}_p", f"{dummy_name}_n"


def _generate_res_netlist(spec: dict[str, Any]) -> str:
    topology = spec["inputs"]["topology"]
    lines: list[str] = ["* res_array", ".SUBCKT res_array"]

    for divider_idx, series_count in enumerate(topology["res_list"], start=1):
        for series_idx in range(1, series_count + 1):
            plus_net = f"G{divider_idx}_p" if series_idx == 1 else f"N{divider_idx}_{series_idx - 1}"
            minus_net = f"D{divider_idx}_n" if series_idx == series_count else f"N{divider_idx}_{series_idx}"
            for parallel_idx in range(1, topology["parallelResNo"] + 1):
                name = f"R{divider_idx}_{series_idx}_{parallel_idx}"
                lines.append(f"{name} {plus_net} {minus_net} RUNIT")

    grid = derive_res_grid(spec)
    dummies = sorted({cell for row in grid["grid"] for cell in row if cell.startswith("R0_")})
    for dummy in dummies:
        plus_net, minus_net = _res_dummy_nets(topology["connectDummyRes"], dummy)
        lines.append(f"{dummy} {plus_net} {minus_net} RUNIT_DMY")

    lines.append(".ENDS res_array")
    return "\n".join(lines)


def generate_netlist(spec: dict[str, Any]) -> str:
    """Erzeuge eine SPICE-ähnliche Netlist aus einer validierten Spec."""
    spec_type = spec.get("type")
    if spec_type == "cap_array":
        return _generate_cap_netlist(spec)
    if spec_type == "res_array":
        return _generate_res_netlist(spec)
    raise ValueError(f"Unsupported spec type: {spec_type!r}")
