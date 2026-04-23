"""Circuit Array Specification helpers."""

from .spec.derive import derive_cap_grid, derive_res_grid, expand_cap_devices, expand_res_devices
from .spec.netlist import generate_netlist
from .classification import GeneratedGridClassification, TileKind, create_uniform_classification, iter_grid_coordinates
from .spec.models import CapArraySpecModel, ResArraySpecModel
from .spec.parser import build_model, parse_circuit_array_spec, parse_circuit_array_spec_json
from .classification.cap_array import CapArrayGridGenerator
from .classification.res_array import ResArrayGridGenerator
from .generators import (
    classification_to_layout_skeleton,
    generate_grid_classification,
    generate_layout_skeleton,
)
from .spec.validator import SpecValidationError, validate_spec
from .debug.helpers import debug_grid_classification, debug_layout, debug_layout_skeleton, debug_spec

__all__ = [
    "CapArraySpecModel",
    "ResArraySpecModel",
    "SpecValidationError",
    "build_model",
    "parse_circuit_array_spec",
    "parse_circuit_array_spec_json",
    "validate_spec",
    "expand_cap_devices",
    "expand_res_devices",
    "derive_cap_grid",
    "derive_res_grid",
    "generate_netlist",
    "TileKind",
    "GeneratedGridClassification",
    "iter_grid_coordinates",
    "create_uniform_classification",
    "CapArrayGridGenerator",
    "ResArrayGridGenerator",
    "generate_grid_classification",
    "classification_to_layout_skeleton",
    "generate_layout_skeleton",
    "debug_spec",
    "debug_grid_classification",
    "debug_layout_skeleton",
    "debug_layout",
]

from layout3d import LayoutPipeline, LayoutValidationError, LayoutValidator

__all__.extend(["LayoutPipeline", "LayoutValidationError", "LayoutValidator"])
