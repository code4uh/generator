"""Intermediate structure bridging grid classification to later layout generation.

This skeleton is intentionally minimal: it carries generated device stacks and
wire cells only. It does not include routing, pins, channel assignment, or any
full ``layout3d`` objects yet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedDeviceStack:
    """Generated vertical device interval at one discrete ``(x, y)`` location."""

    generated_id: str
    x: int
    y: int
    from_layer: int
    to_layer: int

    def __post_init__(self) -> None:
        if self.from_layer > self.to_layer:
            raise ValueError("device stack must satisfy from_layer <= to_layer")


@dataclass(frozen=True)
class GeneratedWireCell:
    """Generated single-cell wire tile at one discrete ``(x, y, layer)`` location."""

    generated_id: str
    x: int
    y: int
    layer: int


@dataclass(frozen=True)
class GeneratedLayoutSkeleton:
    """Minimal generated layout-like representation from tile classification."""

    cells_x: int
    cells_y: int
    layers: int
    device_stacks: tuple[GeneratedDeviceStack, ...]
    wire_cells: tuple[GeneratedWireCell, ...]

    def __post_init__(self) -> None:
        if self.cells_x < 1 or self.cells_y < 1 or self.layers < 1:
            raise ValueError("grid dimensions must be >= 1")

        expected_coords = {
            (x, y, layer)
            for layer in range(self.layers)
            for y in range(self.cells_y)
            for x in range(self.cells_x)
        }

        seen_stack_ids: set[str] = set()
        seen_wire_ids: set[str] = set()
        device_coords: set[tuple[int, int, int]] = set()
        wire_coords: set[tuple[int, int, int]] = set()

        for stack in self.device_stacks:
            if stack.generated_id in seen_stack_ids:
                raise ValueError(f"duplicate device stack id: {stack.generated_id}")
            seen_stack_ids.add(stack.generated_id)

            if not (0 <= stack.x < self.cells_x and 0 <= stack.y < self.cells_y):
                raise ValueError("device stack coordinate out of grid")
            if not (0 <= stack.from_layer <= stack.to_layer < self.layers):
                raise ValueError("device stack layer range out of grid")

            for layer in range(stack.from_layer, stack.to_layer + 1):
                coord = (stack.x, stack.y, layer)
                if coord in device_coords:
                    raise ValueError("duplicate device stack coverage")
                device_coords.add(coord)

        for wire in self.wire_cells:
            if wire.generated_id in seen_wire_ids:
                raise ValueError(f"duplicate wire cell id: {wire.generated_id}")
            seen_wire_ids.add(wire.generated_id)

            if not (0 <= wire.x < self.cells_x and 0 <= wire.y < self.cells_y):
                raise ValueError("wire cell coordinate out of grid")
            if not (0 <= wire.layer < self.layers):
                raise ValueError("wire cell layer out of grid")

            coord = (wire.x, wire.y, wire.layer)
            if coord in wire_coords:
                raise ValueError("duplicate wire cell coordinate")
            wire_coords.add(coord)

        if device_coords & wire_coords:
            raise ValueError("overlap between device stack coverage and wire cell coverage")

        covered_coords = device_coords | wire_coords
        if covered_coords != expected_coords:
            raise ValueError("layout skeleton coverage must match full grid exactly")
