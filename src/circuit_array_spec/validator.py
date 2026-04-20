"""Schema- und semantische Validierung für Circuit Array Specs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import build_model


class SpecValidationError(ValueError):
    """Fehler bei Schema- oder semantischer Validierung."""


_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "spec" / "circuit-array.schema.json"
_SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _format_jsonschema_path(path: Any) -> str:
    if not path:
        return "<root>"
    return ".".join(str(item) for item in path)


def _validate_schema(spec: dict[str, Any]) -> None:
    """Valdiere strikt per jsonschema Draft7 gegen die kanonische Schema-Datei."""
    try:
        from jsonschema import Draft7Validator
    except ModuleNotFoundError as error:
        raise SpecValidationError(
            "Die Abhängigkeit 'jsonschema' fehlt. Bitte installiere Projektabhängigkeiten (z. B. `pip install -e .`)."
        ) from error

    errors = sorted(Draft7Validator(_SCHEMA).iter_errors(spec), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        raise SpecValidationError(
            f"Schemafehler bei {_format_jsonschema_path(error.absolute_path)}: {error.message}"
        )


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
