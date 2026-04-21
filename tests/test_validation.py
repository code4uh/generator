import json
from pathlib import Path

import pytest

from circuit_array_spec.validator import SpecValidationError, validate_spec

ROOT = Path(__file__).resolve().parents[1]


def load_fixture(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_valid_cap_user_pattern() -> None:
    spec = load_fixture("spec/fixtures/valid/cap_array_user_pattern.json")
    validate_spec(spec)


def test_invalid_cap_missing_plus_connected() -> None:
    spec = load_fixture("spec/fixtures/invalid/cap_array_missing_plus_connected.json")
    with pytest.raises(SpecValidationError, match="plusConnected"):
        validate_spec(spec)


def test_invalid_res_connect_dummy() -> None:
    spec = load_fixture("spec/fixtures/invalid/res_array_invalid_connect_dummy.json")
    with pytest.raises(SpecValidationError):
        validate_spec(spec)
