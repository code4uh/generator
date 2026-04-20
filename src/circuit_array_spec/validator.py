"""Schema- und semantische Validierung für Circuit Array Specs."""

from __future__ import annotations

import re
from typing import Any

from .models import build_model


class SpecValidationError(ValueError):
    """Fehler bei Schema- oder semantischer Validierung."""


def _require_keys(obj: dict[str, Any], required: set[str], *, path: str) -> None:
    missing = required - set(obj.keys())
    if missing:
        raise SpecValidationError(f"{path}: fehlende Felder {sorted(missing)}")


def _forbid_additional(obj: dict[str, Any], allowed: set[str], *, path: str) -> None:
    extra = set(obj.keys()) - allowed
    if extra:
        raise SpecValidationError(f"{path}: zusätzliche Felder nicht erlaubt {sorted(extra)}")


def _expect_type(value: Any, expected: type | tuple[type, ...], *, path: str) -> None:
    if not isinstance(value, expected):
        raise SpecValidationError(f"{path}: erwarteter Typ {expected}, erhalten {type(value)}")


def _validate_common_schema(spec: dict[str, Any]) -> None:
    allowed = {"version", "type", "inputs", "capabilities", "output"}
    _require_keys(spec, allowed, path="<root>")
    _forbid_additional(spec, allowed, path="<root>")

    if spec["version"] != "0.1":
        raise SpecValidationError("version muss '0.1' sein")
    if spec["type"] not in {"cap_array", "res_array"}:
        raise SpecValidationError("type muss 'cap_array' oder 'res_array' sein")

    _expect_type(spec["inputs"], dict, path="inputs")
    _expect_type(spec["capabilities"], dict, path="capabilities")
    _expect_type(spec["output"], dict, path="output")

    output = spec["output"]
    _require_keys(output, {"libname", "cellname"}, path="output")
    _forbid_additional(output, {"libname", "cellname"}, path="output")
    if not output["libname"] or not output["cellname"]:
        raise SpecValidationError("output.libname und output.cellname dürfen nicht leer sein")


def _validate_common_input_blocks(inputs: dict[str, Any], *, device: str) -> None:
    routing = inputs["routing_options"]
    _require_keys(
        routing,
        {
            "nVias",
            "wireWidthHor",
            "wireWidthVer",
            "wireWidthPlus",
            "wireWidthMinus",
            "truncVerWires",
            "truncHorWires",
            "verWireAssignment",
            "horWireAssignment",
            "verShielding",
            "horShielding",
            "guardRingOptions",
            "addGuardRingSpacing",
        },
        path=f"inputs.{device}.routing_options",
    )

    advanced = inputs["advanced"]
    _require_keys(
        advanced,
        {
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
        },
        path=f"inputs.{device}.advanced",
    )


def _validate_cap_schema(spec: dict[str, Any]) -> None:
    inputs = spec["inputs"]
    _require_keys(
        inputs,
        {"topology", "placement", "dummy_caps", "routing_options", "advanced"},
        path="inputs",
    )
    _forbid_additional(
        inputs,
        {"topology", "placement", "dummy_caps", "routing_options", "advanced"},
        path="inputs",
    )

    topology = inputs["topology"]
    _require_keys(topology, {"cap_list", "connection", "connectDummyCaps", "boundary_caps"}, path="inputs.topology")
    _forbid_additional(
        topology,
        {"cap_list", "connection", "plusConnected", "connectDummyCaps", "boundary_caps"},
        path="inputs.topology",
    )
    if not topology["cap_list"] or not all(isinstance(x, int) and x >= 1 for x in topology["cap_list"]):
        raise SpecValidationError("inputs.topology.cap_list muss Integer >= 1 enthalten")
    if topology["connection"] not in {"open", "shortPlusPins", "userDefined"}:
        raise SpecValidationError("inputs.topology.connection ungültig")
    if topology["connectDummyCaps"] not in {
        "open_floating",
        "open_shorted",
        "shorted_G1_p",
        "shorted_Cdmy_p",
        "Cdmy_p+Cdmy_n",
    }:
        raise SpecValidationError("inputs.topology.connectDummyCaps ungültig")
    if topology["connection"] == "userDefined" and "plusConnected" not in topology:
        raise SpecValidationError("inputs.topology.plusConnected ist erforderlich bei userDefined")

    placement = inputs["placement"]
    _require_keys(placement, {"rows", "algorithm", "pattern"}, path="inputs.placement")
    if not isinstance(placement["rows"], int) or placement["rows"] < 1:
        raise SpecValidationError("inputs.placement.rows muss Integer >= 1 sein")
    if placement["algorithm"] not in {"common_centroid", "side-by-side", "side-by-side-row-wise", "user"}:
        raise SpecValidationError("inputs.placement.algorithm ungültig")

    _validate_common_input_blocks(inputs, device="cap")


def _validate_res_schema(spec: dict[str, Any]) -> None:
    inputs = spec["inputs"]
    _require_keys(
        inputs,
        {"topology", "placement", "dummy_resistors", "routing_options", "advanced"},
        path="inputs",
    )
    _forbid_additional(
        inputs,
        {"topology", "placement", "dummy_resistors", "routing_options", "advanced"},
        path="inputs",
    )

    topology = inputs["topology"]
    _require_keys(
        topology,
        {"res_list", "parallelResNo", "connectDummyRes", "boundary_resistors"},
        path="inputs.topology",
    )
    if not topology["res_list"] or not all(isinstance(x, int) and x >= 1 for x in topology["res_list"]):
        raise SpecValidationError("inputs.topology.res_list muss Integer >= 1 enthalten")
    if not isinstance(topology["parallelResNo"], int) or topology["parallelResNo"] < 1:
        raise SpecValidationError("inputs.topology.parallelResNo muss Integer >= 1 sein")
    if topology["connectDummyRes"] not in {"open_floating", "VSS"}:
        raise SpecValidationError("inputs.topology.connectDummyRes ungültig")

    placement = inputs["placement"]
    _require_keys(placement, {"algorithm", "pattern"}, path="inputs.placement")

    _validate_common_input_blocks(inputs, device="res")


def _validate_schema(spec: dict[str, Any]) -> None:
    _validate_common_schema(spec)
    if spec["type"] == "cap_array":
        _validate_cap_schema(spec)
    else:
        _validate_res_schema(spec)


def _parse_plus_connected(value: str) -> list[list[int]]:
    groups: list[list[int]] = []
    for match in re.finditer(r"\(([^)]*)\)", value):
        inside = match.group(1)
        indices = [int(item.strip()) for item in inside.split(",") if item.strip()]
        if not indices:
            raise SpecValidationError("plusConnected enthält eine leere Gruppe")
        groups.append(indices)
    if not groups:
        raise SpecValidationError("plusConnected hat kein gültiges Gruppenformat '(1, 2) (3, 4)'")
    return groups


def _validate_cap_semantics(spec: dict[str, Any]) -> None:
    topology = spec["inputs"]["topology"]
    placement = spec["inputs"]["placement"]

    if placement["algorithm"] == "user" and placement["pattern"] is None:
        raise SpecValidationError("placement.pattern ist erforderlich bei placement.algorithm='user'")
    if placement["algorithm"] != "user" and placement["pattern"] is not None:
        raise SpecValidationError("placement.pattern muss null sein wenn placement.algorithm != 'user'")

    plus_connected = topology.get("plusConnected")
    if topology["connection"] != "userDefined" and plus_connected is not None:
        raise SpecValidationError("topology.plusConnected ist nur bei topology.connection='userDefined' erlaubt")

    if topology["connection"] == "userDefined":
        if plus_connected is None:
            raise SpecValidationError("topology.plusConnected fehlt für userDefined connection")

        groups = _parse_plus_connected(plus_connected)
        cap_count = len(topology["cap_list"])
        seen: set[int] = set()
        for group in groups:
            for idx in group:
                if idx < 1 or idx > cap_count:
                    raise SpecValidationError(
                        f"plusConnected Index {idx} außerhalb gültiger Kapazitätsindizes 1..{cap_count}"
                    )
                if idx in seen:
                    raise SpecValidationError(
                        f"plusConnected enthält doppelten Kapazitätsindex: {idx}"
                    )
                seen.add(idx)


def _validate_res_semantics(spec: dict[str, Any]) -> None:
    placement = spec["inputs"]["placement"]
    if placement["algorithm"] != "side-by-side":
        raise SpecValidationError("res_array placement.algorithm muss 'side-by-side' sein")
    if placement["pattern"] is not None:
        raise SpecValidationError("res_array placement.pattern muss null sein")


def validate_spec(spec: dict[str, Any]):
    """Validiert Spec (Schema + Semantik) und gibt internes Datenmodell zurück."""
    _validate_schema(spec)

    if spec["type"] == "cap_array":
        _validate_cap_semantics(spec)
    elif spec["type"] == "res_array":
        _validate_res_semantics(spec)
    else:
        raise SpecValidationError(f"Unbekannter type: {spec['type']}")

    return build_model(spec)
