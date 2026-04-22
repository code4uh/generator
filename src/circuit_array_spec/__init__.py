"""Circuit Array Specification helpers."""

from .derive import derive_cap_grid, derive_res_grid, expand_cap_devices, expand_res_devices
from .netlist import generate_netlist
from .grid_classification import GeneratedGridClassification, TileKind, create_uniform_classification, iter_grid_coordinates
from .models import CapArraySpecModel, ResArraySpecModel
from .parser import build_model, parse_circuit_array_spec, parse_circuit_array_spec_json
from .cap_array_grid_generator import CapArrayGridGenerator
from .res_array_grid_generator import ResArrayGridGenerator
from .generators import (
    classification_to_layout_skeleton,
    generate_grid_classification,
    generate_layout_skeleton,
)
from .validator import SpecValidationError, validate_spec
from .debug import debug_grid_classification, debug_layout, debug_layout_skeleton, debug_spec

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

from .layout3d import LayoutPipeline, LayoutValidationError, LayoutValidator

__all__.extend(["LayoutPipeline", "LayoutValidationError", "LayoutValidator"] )
