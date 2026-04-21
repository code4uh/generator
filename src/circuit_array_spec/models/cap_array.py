from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import (
    Advanced,
    BoundarySize,
    PydanticOutput,
    PositiveInt,
    RoutingLevel,
    RoutingOptions,
    StrictModel,
    UnsupportedOptionPolicy,
    VersionLiteral,
)

CapPlacementAlgorithm = Literal[
    "common_centroid",
    "side-by-side",
    "side-by-side-row-wise",
    "user",
]
CapConnection = Literal["open", "shortPlusPins", "userDefined"]
CapConnectDummy = Literal[
    "open_floating",
    "open_shorted",
    "shorted_G1_p",
    "shorted_Cdmy_p",
    "Cdmy_p+Cdmy_n",
]
CapPatternElement = Annotated[
    str,
    Field(pattern=r"^(C[1-9][0-9]*_[1-9][0-9]*|C0_[1-9][0-9]*)$"),
]
CapPlacementPatternRow = list[CapPatternElement]


class CapBoundaryCaps(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool
    boundary_size: BoundarySize


class PydanticCapTopology(StrictModel):
    cap_list: Annotated[list[PositiveInt], Field(min_length=1)]
    connection: CapConnection
    plusConnected: Annotated[str | None, Field(min_length=1)] = None
    connectDummyCaps: CapConnectDummy
    boundary_caps: CapBoundaryCaps

    @model_validator(mode="after")
    def validate_plus_connected(self) -> "PydanticCapTopology":
        if self.connection == "userDefined" and self.plusConnected is None:
            raise ValueError("plusConnected is required when connection is 'userDefined'")
        return self


class PydanticCapPlacement(StrictModel):
    rows: PositiveInt
    algorithm: CapPlacementAlgorithm
    pattern: list[CapPlacementPatternRow] | None

    @model_validator(mode="after")
    def validate_pattern_by_algorithm(self) -> "PydanticCapPlacement":
        if self.algorithm == "user":
            if self.pattern is None or len(self.pattern) == 0:
                raise ValueError("pattern must be a non-empty array when algorithm is 'user'")
        elif self.pattern is not None:
            raise ValueError("pattern must be null unless algorithm is 'user'")
        return self


class DummyCaps(StrictModel):
    naming_rule: Literal["C0_<idx>"]


class CapArrayInputs(StrictModel):
    topology: PydanticCapTopology
    placement: PydanticCapPlacement
    dummy_caps: DummyCaps
    routing_options: RoutingOptions
    advanced: Advanced


class CapPlacementCapabilities(StrictModel):
    supported_algorithms: list[CapPlacementAlgorithm]
    pattern_supported: Literal[True]

    @model_validator(mode="after")
    def validate_unique_algorithms(self) -> "CapPlacementCapabilities":
        if len(self.supported_algorithms) != len(set(self.supported_algorithms)):
            raise ValueError("supported_algorithms must contain unique items")
        return self


class RoutingCapabilities(StrictModel):
    level: RoutingLevel


class AdvancedCapabilities(StrictModel):
    level: RoutingLevel


class CapArrayCapabilities(StrictModel):
    placement: CapPlacementCapabilities
    routing: RoutingCapabilities
    advanced: AdvancedCapabilities
    unsupported_option_policy: UnsupportedOptionPolicy


class CapArraySpec(StrictModel):
    version: VersionLiteral
    type: Literal["cap_array"]
    inputs: CapArrayInputs
    capabilities: CapArrayCapabilities
    output: PydanticOutput


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
class Output:
    libname: str
    cellname: str


@dataclass(frozen=True)
class CapArraySpecModel:
    version: str
    type: Literal["cap_array"]
    topology: CapTopology
    placement: CapPlacement
    output: Output
    raw: dict[str, object]
