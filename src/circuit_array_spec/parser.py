"""Parsing helpers and backward-compatible model builder."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Annotated

from pydantic import Field, TypeAdapter

from .models.cap_array import CapArraySpec, CapArraySpecModel, CapPlacement, CapTopology, Output
from .models.res_array import ResArraySpec, ResArraySpecModel, ResPlacement, ResTopology

CircuitArraySpec = Annotated[CapArraySpec | ResArraySpec, Field(discriminator="type")]
_CIRCUIT_ARRAY_SPEC_ADAPTER = TypeAdapter(CircuitArraySpec)


def parse_circuit_array_spec(data: Mapping[str, object]) -> CircuitArraySpec:
    return _CIRCUIT_ARRAY_SPEC_ADAPTER.validate_python(data)


def parse_circuit_array_spec_json(data: str) -> CircuitArraySpec:
    return _CIRCUIT_ARRAY_SPEC_ADAPTER.validate_json(data)


def _to_plain_obj(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): _to_plain_obj(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain_obj(v) for v in value]
    return deepcopy(value)


def _to_plain_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return deepcopy(value)
    if isinstance(value, Mapping):
        return {str(k): _to_plain_obj(v) for k, v in value.items()}
    raise TypeError("spec must be a mapping")


def build_model(spec: Mapping[str, object]) -> CapArraySpecModel | ResArraySpecModel:
    validated = parse_circuit_array_spec(spec)
    raw = _to_plain_dict(spec)

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
            output=Output(libname=validated.output.libname, cellname=validated.output.cellname),
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
        output=Output(libname=validated.output.libname, cellname=validated.output.cellname),
        raw=raw,
    )
