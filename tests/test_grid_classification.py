import pytest

from arraylayout.classification.grid import (
    GeneratedGridClassification,
    create_uniform_classification,
    iter_grid_coordinates,
)


def test_iter_grid_coordinates_covers_complete_shape() -> None:
    coords = list(iter_grid_coordinates(cells_x=2, cells_y=2, layers=2))
    assert len(coords) == 8
    assert (0, 0, 0) in coords
    assert (1, 1, 1) in coords


def test_generated_grid_classification_accepts_complete_grid() -> None:
    classification = create_uniform_classification(cells_x=3, cells_y=2, layers=1, kind="wire")

    assert classification.tile_kind_at(0, 0, 0) == "wire"
    assert classification.tile_kind_at(2, 1, 0) == "wire"


def test_generated_grid_classification_rejects_missing_coordinate() -> None:
    tiles = {(0, 0, 0): "device"}

    with pytest.raises(ValueError, match="incomplete"):
        GeneratedGridClassification(cells_x=2, cells_y=1, layers=1, tiles=tiles)


def test_generated_grid_classification_rejects_out_of_grid_coordinate() -> None:
    tiles = {(0, 0, 0): "device", (2, 0, 0): "wire"}

    with pytest.raises(ValueError, match="out-of-grid"):
        GeneratedGridClassification(cells_x=2, cells_y=1, layers=1, tiles=tiles)


def test_generated_grid_classification_rejects_invalid_kind() -> None:
    tiles = {(0, 0, 0): "unknown"}

    with pytest.raises(ValueError, match="invalid tile kinds"):
        GeneratedGridClassification(cells_x=1, cells_y=1, layers=1, tiles=tiles)


def test_generated_grid_classification_accepts_mixed_device_wire_geometry() -> None:
    classification = GeneratedGridClassification(
        cells_x=2,
        cells_y=1,
        layers=2,
        tiles={
            (0, 0, 0): "device",
            (1, 0, 0): "wire",
            (0, 0, 1): "wire",
            (1, 0, 1): "wire",
        },
    )

    assert classification.tile_kind_at(0, 0, 0) == "device"
    assert classification.tile_kind_at(1, 0, 1) == "wire"
