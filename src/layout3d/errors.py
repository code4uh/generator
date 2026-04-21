"""Strukturierte Fehlerobjekte für Parsing und Validierung."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    entity_type: str
    entity_id: str | None
    location: tuple[str, ...]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


class LayoutValidationError(ValueError):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = tuple(issues)
        msg = "\n".join(
            f"{issue.code} ({issue.entity_type}:{issue.entity_id or '-'}) at {'/'.join(issue.location) or '<root>'}: {issue.message}"
            for issue in issues
        )
        super().__init__(msg)


class ParseError(ValueError):
    """Konsistenter Fehler für Parser-Probleme mit optionalem Pfadkontext."""

    def __init__(self, message: str, *, path: str | None = None):
        self.message = message
        self.path = path
        suffix = f" at {path}" if path else ""
        super().__init__(f"{message}{suffix}")
