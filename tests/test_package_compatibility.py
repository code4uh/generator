from __future__ import annotations

import importlib
import sys
import warnings


def test_import_gridlayout_works() -> None:
    gridlayout = importlib.import_module("gridlayout")
    assert hasattr(gridlayout, "__all__")


def test_import_arraylayout_emits_deprecation_warning_and_matches_public_api() -> None:
    sys.modules.pop("arraylayout", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        arraylayout = importlib.import_module("arraylayout")

    deprecations = [item for item in caught if issubclass(item.category, DeprecationWarning)]
    assert len(deprecations) == 1

    gridlayout = importlib.import_module("gridlayout")
    assert arraylayout.__all__ == gridlayout.__all__
    for name in gridlayout.__all__:
        assert getattr(arraylayout, name) is getattr(gridlayout, name)


def test_arraylayout_deprecation_warning_emitted_once_per_fresh_import() -> None:
    sys.modules.pop("arraylayout", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.import_module("arraylayout")
        importlib.import_module("arraylayout")
    deprecations = [item for item in caught if issubclass(item.category, DeprecationWarning)]
    assert len(deprecations) == 1


def test_legacy_submodule_imports_resolve_to_gridlayout_modules() -> None:
    legacy_spec = importlib.import_module("arraylayout.spec")
    new_spec = importlib.import_module("gridlayout.spec")
    assert legacy_spec is new_spec

    legacy_classification = importlib.import_module("arraylayout.classification")
    new_classification = importlib.import_module("gridlayout.classification")
    assert legacy_classification is new_classification


def test_cli_module_imports_use_gridlayout_namespace() -> None:
    debug_cli = importlib.import_module("gridlayout.debug.cli")
    render_cli = importlib.import_module("gridlayout.render.cli")
    assert callable(debug_cli.main)
    assert callable(render_cli.main)
