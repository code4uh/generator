"""Parsing helpers and backward-compatible model builder."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy

from .models import (
    CapArraySpecModel,
    CapPlacement,
    CapTopology,
    Output,
    ResArraySpecModel,
    ResPlacement,
    ResTopology,
)


def parse_circuit_array_spec(data: Mapping[str, object]) -> Mapping[str, object]:
    return data


def parse_circuit_array_spec_json(data: str) -> Mapping[str, object]:
    return json.loads(data)


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
    raw = _to_plain_dict(spec)
    spec_type = raw["type"]

    if spec_type == "cap_array":
        inputs = raw["inputs"]
        topology = inputs["topology"]
        placement = inputs["placement"]
        output = raw["output"]
        return CapArraySpecModel(
            version=str(raw["version"]),
            type="cap_array",
            topology=CapTopology(
                cap_list=list(topology["cap_list"]),
                connection=topology["connection"],
                plus_connected=topology.get("plusConnected"),
                connect_dummy_caps=topology["connectDummyCaps"],
                boundary_caps=deepcopy(topology["boundary_caps"]),
            ),
            placement=CapPlacement(
                rows=int(placement["rows"]),
                algorithm=placement["algorithm"],
                pattern=placement["pattern"],
            ),
            output=Output(libname=str(output["libname"]), cellname=str(output["cellname"])),
            raw=raw,
        )

    inputs = raw["inputs"]
    topology = inputs["topology"]
    placement = inputs["placement"]
    output = raw["output"]
    return ResArraySpecModel(
        version=str(raw["version"]),
        type="res_array",
        topology=ResTopology(
            res_list=list(topology["res_list"]),
            parallel_res_no=int(topology["parallelResNo"]),
            connect_dummy_res=topology["connectDummyRes"],
            boundary_resistors=deepcopy(topology["boundary_resistors"]),
        ),
        placement=ResPlacement(
            algorithm=placement["algorithm"],
            pattern=placement["pattern"],
        ),
        output=Output(libname=str(output["libname"]), cellname=str(output["cellname"])),
        raw=raw,
    )
