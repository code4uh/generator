"""Schema- und semantische Validierung für Circuit Array Specs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .parser import build_model


class SpecValidationError(ValueError):
    """Fehler bei Schema- oder semantischer Validierung."""


_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "spec" / "schema" / "circuit-array.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _format_jsonschema_path(path: Any) -> str:
    if not path:
        return "<root>"
    return ".".join(str(item) for item in path)


def _stable_jsonschema_summary(error: Any) -> str:
    validator = getattr(error, "validator", "")

    if validator == "additionalProperties":
        return "additional properties not allowed"

    if validator == "required":
        missing_key = next(
            (key for key in error.validator_value if key not in getattr(error, "instance", {})),
            None,
        )
        if missing_key is None:
            return "missing required property"
        return f"missing required property '{missing_key}'"

    if validator == "type":
        expected_type = error.validator_value
        if isinstance(expected_type, list):
            expected = ", ".join(str(item) for item in expected_type)
        else:
            expected = str(expected_type)
        return f"expected type {expected}"

    if validator == "enum":
        allowed = ", ".join(repr(item) for item in error.validator_value)
        return f"must be one of: {allowed}"

    if validator == "oneOf":
        context = getattr(error, "context", ()) or ()
        sub_summaries: list[str] = []
        for sub_error in context:
            sub_path = _format_jsonschema_path(getattr(sub_error, "absolute_path", ()))
            sub_summary = _stable_jsonschema_summary(sub_error)
            detail = f"{sub_path}: {sub_summary}" if sub_path != "<root>" else sub_summary
            if detail not in sub_summaries:
                sub_summaries.append(detail)
            if len(sub_summaries) >= 3:
                break
        if sub_summaries:
            return "must match exactly one schema; candidates failed: " + " | ".join(sub_summaries)
        return "must match exactly one schema"

    if validator:
        return f"{validator} constraint violated"

    return "schema constraint violated"


def _raise_schema_error(path: str, summary: str) -> None:
    raise SpecValidationError(f"Schema validation failed at {path}: {summary}")


def _validate_schema_without_jsonschema(spec: dict[str, Any]) -> None:
    required_top_level = ("version", "type", "inputs", "capabilities", "output")
    for key in required_top_level:
        if key not in spec:
            _raise_schema_error("<root>", f"missing required property '{key}'")

    if spec.get("type") == "cap_array":
        topology = spec.get("inputs", {}).get("topology", {})
        boundary_caps = topology.get("boundary_caps", {})
        connection = topology.get("connection")
        plus_connected = topology.get("plusConnected")

        if "boundary_device_size" not in boundary_caps:
            _raise_schema_error(
                "inputs.topology.boundary_caps",
                "missing required property 'boundary_device_size'",
            )
        if "boundary_size" in boundary_caps:
            _raise_schema_error(
                "inputs.topology.boundary_caps",
                "additional properties not allowed",
            )

        if connection == "userDefined" and "plusConnected" not in topology:
            _raise_schema_error("inputs.topology", "missing required property 'plusConnected'")

        if plus_connected is not None and not isinstance(plus_connected, str):
            _raise_schema_error("inputs.topology.plusConnected", "expected type string")

    if spec.get("type") == "res_array":
        topology = spec.get("inputs", {}).get("topology", {})
        boundary_resistors = topology.get("boundary_resistors", {})
        connect_dummy_res = topology.get("connectDummyRes")
        allowed = ("open_floating", "VSS")
        if connect_dummy_res not in allowed:
            allowed_text = ", ".join(repr(item) for item in allowed)
            _raise_schema_error(
                "inputs.topology.connectDummyRes",
                f"must be one of: {allowed_text}",
            )
        if "boundary_device_size" not in boundary_resistors:
            _raise_schema_error(
                "inputs.topology.boundary_resistors",
                "missing required property 'boundary_device_size'",
            )
        if "boundary_size" in boundary_resistors:
            _raise_schema_error(
                "inputs.topology.boundary_resistors",
                "additional properties not allowed",
            )


def _validate_schema(spec: dict[str, Any]) -> None:
    """Validiere strikt per jsonschema Draft 2020-12 gegen die kanonische Schema-Datei."""
    try:
        from jsonschema import Draft202012Validator
    except ModuleNotFoundError as error:
        _validate_schema_without_jsonschema(spec)
        return

    errors = sorted(Draft202012Validator(_SCHEMA).iter_errors(spec), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        path = _format_jsonschema_path(error.absolute_path)
        summary = _stable_jsonschema_summary(error)
        raise SpecValidationError(
            f"Schema validation failed at {path}: {summary}"
        )


def _parse_plus_connected(value: str) -> list[list[int]]:
    if not re.fullmatch(r"\s*(\(\s*\d+(?:\s*,\s*\d+)*\s*\)\s*)+", value):
        raise SpecValidationError(
            "plusConnected has invalid format; expected only whitespace and groups like '(1, 2) (3, 4)'"
        )

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


def validate_spec(spec: dict[str, Any]):
    """Validiert Spec (Schema + Semantik) und gibt internes Datenmodell zurück."""
    _validate_schema(spec)

    if spec["type"] == "cap_array":
        _validate_cap_semantics(spec)
    elif spec["type"] != "res_array":
        raise SpecValidationError(f"Unbekannter type: {spec['type']}")

    return build_model(spec)
