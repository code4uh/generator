"""Shared API for first-stage grid classification generation.

`generate_grid_classification(...)` is the V1 entry point that dispatches by spec
model type and returns only device-vs-wire tile classification.
"""

from __future__ import annotations

from ..cap_array_grid_generator import CapArrayGridGenerator
from ..models import CapArraySpecModel, ResArraySpecModel
from ..models.grid_classification import GeneratedGridClassification
from ..res_array_grid_generator import ResArrayGridGenerator


def generate_grid_classification(
    spec: CapArraySpecModel | ResArraySpecModel,
    *,
    layers: int = 1,
) -> GeneratedGridClassification:
    """Generate V1 grid classification by dispatching on spec model type."""
    if isinstance(spec, CapArraySpecModel):
        return CapArrayGridGenerator().generate(spec, layers=layers)

    if isinstance(spec, ResArraySpecModel):
        return ResArrayGridGenerator().generate(spec, layers=layers)

    raise TypeError(
        "Unsupported spec model type for generate_grid_classification: "
        f"{type(spec).__name__}"
    )
