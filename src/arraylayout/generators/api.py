"""Shared API for generation stages.

`generate_grid_classification(...)` is the V1 entry point that dispatches by spec
model type and returns only device-vs-wire tile classification.
"""

from __future__ import annotations

from ..cap_array_grid_generator import CapArrayGridGenerator
from ..models import CapArraySpecModel, ResArraySpecModel
from ..models.grid_classification import GeneratedGridClassification
from layout3d.types import LayoutInstance

from ..models.layout_skeleton import GeneratedLayoutSkeleton
from ..res_array_grid_generator import ResArrayGridGenerator
from .layout import skeleton_to_layout
from .layout_skeleton import classification_to_layout_skeleton


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


def generate_layout_skeleton(
    spec: CapArraySpecModel | ResArraySpecModel,
    *,
    layers: int = 1,
) -> GeneratedLayoutSkeleton:
    """Generate intermediate layout skeleton from V1 grid classification."""
    classification = generate_grid_classification(spec, layers=layers)
    return classification_to_layout_skeleton(classification)


def generate_minimal_layout(
    spec: CapArraySpecModel | ResArraySpecModel,
    *,
    layers: int = 1,
) -> LayoutInstance:
    """Generate minimal structural ``layout3d`` layout from V1 skeleton."""
    skeleton = generate_layout_skeleton(spec, layers=layers)
    return skeleton_to_layout(skeleton)
