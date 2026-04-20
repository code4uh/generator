"""Pydantic v2 models for Circuit Array Specification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from copy import deepcopy
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


# -----------------------------------------------------------------------------
# Shared scalar aliases
# -----------------------------------------------------------------------------

NonEmptyStr = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeFloat = Annotated[float, Field(ge=0)]
PositiveFloat = Annotated[float, Field(gt=0)]
VersionLiteral = Literal["0.1"]
ArrayType = Literal["cap_array", "res_array"]

UnsupportedOptionPolicy = Literal["ignore", "ignore_with_warning", "error"]
RoutingLevel = Literal["full", "partial", "none"]
BoundarySize = Literal["Unit", "Minimum"]

CapPlacementAlgorithm = Literal[
    "common_centroid",
    "side-by-side",
    "side-by-side-row-wise",
    "user",
]
ResPlacementAlgorithm = Literal["side-by-side"]

CapConnection = Literal["open", "shortPlusPins", "userDefined"]
CapConnectDummy = Literal[
    "open_floating",
    "open_shorted",
    "shorted_G1_p",
    "shorted_Cdmy_p",
    "Cdmy_p+Cdmy_n",
]
ResConnectDummy = Literal["open_floating", "VSS"]

CapPatternElement = Annotated[
    str,
    Field(pattern=r"^(C[1-9][0-9]*_[1-9][0-9]*|C0_[1-9][0-9]*)$"),
]
CapPlacementPatternRow = list[CapPatternElement]

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


# -----------------------------------------------------------------------------
# Base utility models
# -----------------------------------------------------------------------------


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PydanticOutput(StrictModel):
    libname: NonEmptyStr
    cellname: NonEmptyStr


class GuardRingOptions(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool


class RoutingOptions(StrictModel):
    nVias: PositiveInt
    wireWidthHor: PositiveFloat
    wireWidthVer: PositiveFloat
    wireWidthPlus: PositiveFloat
    wireWidthMinus: PositiveFloat
    truncVerWires: bool
    truncHorWires: bool
    verWireAssignment: Literal["minus-plus", "separate-plus-minus"]
    horWireAssignment: Literal["all-bottom", "all-top", "symmetric", "separate-plus-minus"]
    verShielding: Literal["shield-pin", "Cdmy_n"]
    horShielding: Literal["device-bus", "plus-minus", "outer-edge"]
    guardRingOptions: GuardRingOptions
    addGuardRingSpacing: NonNegativeFloat


class Advanced(StrictModel):
    horDevSpacing: float
    verDevSpacing: float
    minHorDevBusSpacing: NonNegativeFloat
    minVerDevBusSpacing: NonNegativeFloat
    noRouting: bool
    onlyVerticalWires: bool
    omitHorizontalBus: bool
    deleteFloatingWires: bool
    wireSpaceHor: NonNegativeFloat
    wireSpaceVer: NonNegativeFloat


class CapBoundaryCaps(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool
    boundary_size: BoundarySize


class ResBoundaryResistors(StrictModel):
    left: bool
    right: bool
    top: bool
    bottom: bool
    boundary_size: BoundarySize


# -----------------------------------------------------------------------------
# Capacitor spec models
# -----------------------------------------------------------------------------


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
        else:
            if self.pattern is not None:
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


# -----------------------------------------------------------------------------
# Resistor spec models
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Top-level union + parsing helpers
# -----------------------------------------------------------------------------


CircuitArraySpec = Annotated[CapArraySpec | ResArraySpec, Field(discriminator="type")]
_CIRCUIT_ARRAY_SPEC_ADAPTER = TypeAdapter(CircuitArraySpec)


def parse_circuit_array_spec(data: Mapping[str, object]) -> CircuitArraySpec:
    return _CIRCUIT_ARRAY_SPEC_ADAPTER.validate_python(data)


def parse_circuit_array_spec_json(data: str) -> CircuitArraySpec:
    return _CIRCUIT_ARRAY_SPEC_ADAPTER.validate_json(data)


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


def _to_plain_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, Mapping):
        return {str(k): _to_plain_obj(v) for k, v in value.items()}
    raise TypeError("spec must be a mapping")


def _to_plain_obj(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _to_plain_obj(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain_obj(v) for v in value]
    return deepcopy(value)


def build_model(spec: Mapping[str, object]) -> CapArraySpecModel | ResArraySpecModel:
    """Backward-compatible conversion wrapper around the top-level parser."""
    validated = parse_circuit_array_spec(spec)
    raw = _to_plain_dict(spec)

    legacy_output = Output(
        libname=validated.output.libname,
        cellname=validated.output.cellname,
    )

    if isinstance(validated, CapArraySpec):
        return CapArraySpecModel(
            version=validated.version,
            type="cap_array",
            topology=CapTopology(
                cap_list=list(validated.inputs.topology.cap_list),
                connection=validated.inputs.topology.connection,
                plus_connected=validated.inputs.topology.plusConnected,
                connect_dummy_caps=validated.inputs.topology.connectDummyCaps,
                boundary_caps=validated.inputs.topology.boundary_caps.model_dump(),
            ),
            placement=CapPlacement(
                rows=validated.inputs.placement.rows,
                algorithm=validated.inputs.placement.algorithm,
                pattern=validated.inputs.placement.pattern,
            ),
            output=legacy_output,
            raw=raw,
        )

    return ResArraySpecModel(
        version=validated.version,
        type="res_array",
        topology=ResTopology(
            res_list=list(validated.inputs.topology.res_list),
            parallel_res_no=validated.inputs.topology.parallelResNo,
            connect_dummy_res=validated.inputs.topology.connectDummyRes,
            boundary_resistors=validated.inputs.topology.boundary_resistors.model_dump(),
        ),
        placement=ResPlacement(
            algorithm=validated.inputs.placement.algorithm,
            pattern=validated.inputs.placement.pattern,
        ),
        output=legacy_output,
        raw=raw,
    )


# -----------------------------------------------------------------------------
# Minimal runnable example + self-checks
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    cap_example = {
        "version": "0.1",
        "type": "cap_array",
        "inputs": {
            "topology": {
                "cap_list": [3, 4, 3, 2],
                "connection": "userDefined",
                "plusConnected": "(1, 2) (3, 4)",
                "connectDummyCaps": "shorted_G1_p",
                "boundary_caps": {
                    "left": True,
                    "right": True,
                    "top": False,
                    "bottom": True,
                    "boundary_size": "Unit",
                },
            },
            "placement": {
                "rows": 3,
                "algorithm": "common_centroid",
                "pattern": None,
            },
            "dummy_caps": {"naming_rule": "C0_<idx>"},
            "routing_options": {
                "nVias": 2,
                "wireWidthHor": 0.4,
                "wireWidthVer": 0.4,
                "wireWidthPlus": 0.6,
                "wireWidthMinus": 0.6,
                "truncVerWires": True,
                "truncHorWires": False,
                "verWireAssignment": "minus-plus",
                "horWireAssignment": "symmetric",
                "verShielding": "shield-pin",
                "horShielding": "plus-minus",
                "guardRingOptions": {
                    "left": True,
                    "right": True,
                    "top": True,
                    "bottom": False,
                },
                "addGuardRingSpacing": 0.8,
            },
            "advanced": {
                "horDevSpacing": 0.2,
                "verDevSpacing": 0.2,
                "minHorDevBusSpacing": 0.15,
                "minVerDevBusSpacing": 0.15,
                "noRouting": False,
                "onlyVerticalWires": False,
                "omitHorizontalBus": False,
                "deleteFloatingWires": True,
                "wireSpaceHor": 0.1,
                "wireSpaceVer": 0.1,
            },
        },
        "capabilities": {
            "placement": {
                "supported_algorithms": [
                    "common_centroid",
                    "side-by-side",
                    "side-by-side-row-wise",
                    "user",
                ],
                "pattern_supported": True,
            },
            "routing": {"level": "full"},
            "advanced": {"level": "full"},
            "unsupported_option_policy": "ignore_with_warning",
        },
        "output": {"libname": "my_library", "cellname": "cap_array_cell"},
    }

    res_example = {
        "version": "0.1",
        "type": "res_array",
        "inputs": {
            "topology": {
                "res_list": [3, 4, 2],
                "parallelResNo": 2,
                "connectDummyRes": "VSS",
                "boundary_resistors": {
                    "left": True,
                    "right": True,
                    "top": False,
                    "bottom": True,
                    "boundary_size": "Unit",
                },
            },
            "placement": {
                "algorithm": "side-by-side",
                "pattern": None,
            },
            "dummy_resistors": {"naming_rule": "R0_<idx>"},
            "routing_options": {
                "nVias": 2,
                "wireWidthHor": 0.4,
                "wireWidthVer": 0.4,
                "wireWidthPlus": 0.6,
                "wireWidthMinus": 0.6,
                "truncVerWires": True,
                "truncHorWires": False,
                "verWireAssignment": "minus-plus",
                "horWireAssignment": "symmetric",
                "verShielding": "shield-pin",
                "horShielding": "plus-minus",
                "guardRingOptions": {
                    "left": True,
                    "right": True,
                    "top": True,
                    "bottom": False,
                },
                "addGuardRingSpacing": 0.8,
            },
            "advanced": {
                "horDevSpacing": 0.2,
                "verDevSpacing": 0.2,
                "minHorDevBusSpacing": 0.15,
                "minVerDevBusSpacing": 0.15,
                "noRouting": False,
                "onlyVerticalWires": False,
                "omitHorizontalBus": False,
                "deleteFloatingWires": True,
                "wireSpaceHor": 0.1,
                "wireSpaceVer": 0.1,
            },
        },
        "capabilities": {
            "placement": {
                "supported_algorithms": ["side-by-side"],
                "pattern_supported": False,
            },
            "routing": {"level": "partial"},
            "advanced": {
                "level": "partial",
                "supported_fields": ["horDevSpacing", "verDevSpacing"],
            },
            "unsupported_option_policy": "ignore_with_warning",
        },
        "output": {"libname": "my_library", "cellname": "res_array_cell"},
    }

    parsed_cap = parse_circuit_array_spec(cap_example)
    parsed_res = parse_circuit_array_spec(res_example)

    assert isinstance(parsed_cap, CapArraySpec)
    assert parsed_cap.type == "cap_array"
    assert isinstance(parsed_res, ResArraySpec)
    assert parsed_res.type == "res_array"

    legacy_cap = build_model(cap_example)
    legacy_res = build_model(res_example)

    assert isinstance(legacy_cap, CapArraySpecModel)
    assert legacy_cap.topology.plus_connected == "(1, 2) (3, 4)"
    assert legacy_cap.topology.connect_dummy_caps == "shorted_G1_p"
    assert legacy_cap.output.libname == "my_library"

    assert isinstance(legacy_res, ResArraySpecModel)
    assert legacy_res.topology.parallel_res_no == 2
    assert legacy_res.topology.connect_dummy_res == "VSS"
    assert legacy_res.output.cellname == "res_array_cell"

    print("CircuitArraySpec self-checks passed.")
