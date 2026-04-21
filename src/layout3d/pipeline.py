"""Orchestrierung von Parsing, Normalisierung, Validierung und Repräsentation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import LayoutValidationError
from .normalize import normalize_layout
from .parser import parse_layout
from .representation import TileRepresentation, build_tile_representation
from .validation import LayoutValidator


class LayoutPipeline:
    def __init__(self, validator: LayoutValidator | None = None) -> None:
        self._validator = validator or LayoutValidator()

    def parse_normalize_validate(self, data: Mapping[str, Any]) -> TileRepresentation:
        parsed = parse_layout(data)
        normalized = normalize_layout(parsed)
        report = self._validator.validate(normalized)
        if not report.ok:
            raise LayoutValidationError(list(report.issues))
        return build_tile_representation(normalized.layout)
