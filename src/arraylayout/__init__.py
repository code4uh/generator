"""Backward-compatible shim for the renamed ``gridlayout`` package."""

from __future__ import annotations

import importlib
import sys
import warnings

from gridlayout import *  # noqa: F401,F403
from gridlayout import __all__ as __all__

warnings.warn(
    "'arraylayout' is deprecated and will be removed in a future release; use 'gridlayout' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Provide legacy subpackage import compatibility, e.g. ``import arraylayout.spec``.
for _name in (
    "classification",
    "debug",
    "generators",
    "layout",
    "models",
    "render",
    "semantics",
    "skeleton",
    "spec",
):
    sys.modules[f"arraylayout.{_name}"] = importlib.import_module(f"gridlayout.{_name}")
