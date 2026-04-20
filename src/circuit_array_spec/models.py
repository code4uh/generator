"""Interne Datenmodelle für Circuit Array Specification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ArrayType = Literal["cap_array", "res_array"]
CapConnection = Literal["open", "shortPlusPins", "userDefined"]
CapConnectDummy = Literal[
    "open_floating",
    "open_shorted",
    "shorted_G1_p",
    "shorted_Cdmy_p",
    "Cdmy_p+Cdmy_n",
]
ResConnectDummy = Literal["open_floating", "VSS"]
CapPlacementAlgorithm = Literal[
    "common_centroid",
    "side-by-side",
    "side-by-side-row-wise",
    "user",
]
ResPlacementAlgorithm = Literal["side-by-side"]
BoundarySize = Literal["Unit", "Minimum"]


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
    boundary_caps: dict[str, Any]


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
    raw: dict[str, Any]


@dataclass(frozen=True)
class ResTopology:
    res_list: list[int]
    parallel_res_no: int
    connect_dummy_res: ResConnectDummy
    boundary_resistors: dict[str, Any]


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
    raw: dict[str, Any]


def build_model(spec: dict[str, Any]) -> CapArraySpecModel | ResArraySpecModel:
    """Baue ein internes Datenmodell aus einem bereits validierten Spec-Dict."""
    output = Output(
        libname=spec["output"]["libname"],
        cellname=spec["output"]["cellname"],
    )

    if spec["type"] == "cap_array":
        topology = spec["inputs"]["topology"]
        placement = spec["inputs"]["placement"]
        return CapArraySpecModel(
            version=spec["version"],
            type="cap_array",
            topology=CapTopology(
                cap_list=topology["cap_list"],
                connection=topology["connection"],
                plus_connected=topology.get("plusConnected"),
                connect_dummy_caps=topology["connectDummyCaps"],
                boundary_caps=topology["boundary_caps"],
            ),
            placement=CapPlacement(
                rows=placement["rows"],
                algorithm=placement["algorithm"],
                pattern=placement["pattern"],
            ),
            output=output,
            raw=spec,
        )

    topology = spec["inputs"]["topology"]
    placement = spec["inputs"]["placement"]
    return ResArraySpecModel(
        version=spec["version"],
        type="res_array",
        topology=ResTopology(
            res_list=topology["res_list"],
            parallel_res_no=topology["parallelResNo"],
            connect_dummy_res=topology["connectDummyRes"],
            boundary_resistors=topology["boundary_resistors"],
        ),
        placement=ResPlacement(
            algorithm=placement["algorithm"],
            pattern=placement["pattern"],
        ),
        output=output,
        raw=spec,
    )
