"""Shared API for generation stages.

`generate_grid_classification(...)` is the V1 entry point that dispatches by spec
model type and returns only device-vs-wire tile classification.
"""

from __future__ import annotations

from ..classification.cap_array import CapArrayGridGenerator
from ..spec.models import CapArraySpecModel, ResArraySpecModel
from ..classification.grid import GeneratedGridClassification
from layout3d.types import LayoutInstance

from ..skeleton.models import GeneratedLayoutSkeleton
from ..classification.res_array import ResArrayGridGenerator
from ..layout.build import skeleton_to_layout
from ..skeleton.transform import classification_to_layout_skeleton


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
