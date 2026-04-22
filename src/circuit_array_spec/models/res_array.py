from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, TypedDict

from pydantic import Field, model_validator

from .common import (
    Advanced,
    PydanticOutput,
    PositiveInt,
    RoutingLevel,
    RoutingOptions,
    StrictModel,
    UnsupportedOptionPolicy,
    VersionLiteral,
)

from .enums import BoundaryDeviceSize

ResPlacementAlgorithm = Literal["side-by-side"]
ResConnectDummy = Literal["open_floating", "VSS"]
ResAdvancedSupportedField = Literal[
    "horDevSpacing",
    "verDevSpacing",
    "minHorDevBusSpacing",
    "minVerDevBusSpacing",
    "noRouting",
    "onlyVerticalWires",
    "omitHorizontalBus",
    "deleteFloatingWires",
    "wireSpaceHor",
    "wireSpaceVer",
]


class ResBoundaryResistors(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool
    boundary_device_size: BoundaryDeviceSize


class BoundaryResistors(TypedDict):
    left: bool
    right: bool
    top: bool
    bottom: bool
    boundary_device_size: BoundaryDeviceSize


class PydanticResTopology(StrictModel):
    res_list: Annotated[list[PositiveInt], Field(min_length=1)]
    parallelResNo: PositiveInt
    connectDummyRes: ResConnectDummy
    boundary_resistors: ResBoundaryResistors


class PydanticResPlacement(StrictModel):
    algorithm: ResPlacementAlgorithm
    pattern: None


class DummyResistors(StrictModel):
    naming_rule: Literal["R0_<idx>"]


class ResArrayInputs(StrictModel):
    topology: PydanticResTopology
    placement: PydanticResPlacement
    dummy_resistors: DummyResistors
    routing_options: RoutingOptions
    advanced: Advanced


class RoutingCapabilities(StrictModel):
    level: RoutingLevel


class ResPlacementCapabilities(StrictModel):
    supported_algorithms: Annotated[list[Literal["side-by-side"]], Field(min_length=1, max_length=1)]
    pattern_supported: Literal[False]


class ResAdvancedCapabilities(StrictModel):
    level: Literal["partial", "full", "none"]
    supported_fields: list[ResAdvancedSupportedField]

    @model_validator(mode="after")
    def validate_unique_supported_fields(self) -> "ResAdvancedCapabilities":
        if len(self.supported_fields) != len(set(self.supported_fields)):
            raise ValueError("supported_fields must contain unique items")
        return self


class ResArrayCapabilities(StrictModel):
    placement: ResPlacementCapabilities
    routing: RoutingCapabilities
    advanced: ResAdvancedCapabilities
    unsupported_option_policy: UnsupportedOptionPolicy


class ResArraySpec(StrictModel):
    version: VersionLiteral
    type: Literal["res_array"]
    inputs: ResArrayInputs
    capabilities: ResArrayCapabilities
    output: PydanticOutput


@dataclass(frozen=True)
class ResTopology:
    res_list: list[int]
    parallel_res_no: int
    connect_dummy_res: ResConnectDummy
    boundary_resistors: BoundaryResistors


@dataclass(frozen=True)
class ResPlacement:
    algorithm: ResPlacementAlgorithm
    pattern: None


@dataclass(frozen=True)
class Output:
    libname: str
    cellname: str


@dataclass(frozen=True)
class ResArraySpecModel:
    version: str
    type: Literal["res_array"]
    topology: ResTopology
    placement: ResPlacement
    output: Output
    raw: dict[str, object]
