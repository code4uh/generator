from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CapConnection = Literal["open", "shortPlusPins", "userDefined"]
CapConnectDummy = Literal[
    "open_floating",
    "open_shorted",
    "shorted_G1_p",
    "shorted_Cdmy_p",
    "Cdmy_p+Cdmy_n",
]
CapPlacementAlgorithm = Literal["common_centroid", "side-by-side", "side-by-side-row-wise", "user"]

ResPlacementAlgorithm = Literal["side-by-side"]
ResConnectDummy = Literal["open_floating", "VSS"]


@dataclass(frozen=True)
class Output:
    libname: str
    cellname: str


@dataclass(frozen=True)
class CapTopology:
    cap_list: list[int]
    connection: CapConnection
    plus_connected: str | None
    connect_dummy_caps: CapConnectDummy
    boundary_caps: dict[str, object]


@dataclass(frozen=True)
class CapPlacement:
    rows: int
    algorithm: CapPlacementAlgorithm
    pattern: list[list[str]] | None


@dataclass(frozen=True)
class CapArraySpecModel:
    version: str
    type: Literal["cap_array"]
    topology: CapTopology
    placement: CapPlacement
    output: Output
    raw: dict[str, object]


@dataclass(frozen=True)
class ResTopology:
    res_list: list[int]
    parallel_res_no: int
    connect_dummy_res: ResConnectDummy
    boundary_resistors: dict[str, object]


@dataclass(frozen=True)
class ResPlacement:
    algorithm: ResPlacementAlgorithm
    pattern: None


@dataclass(frozen=True)
class ResArraySpecModel:
    version: str
    type: Literal["res_array"]
    topology: ResTopology
    placement: ResPlacement
    output: Output
    raw: dict[str, object]
