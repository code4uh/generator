"""Renderer für tile-basiertes 3D-Layout (ASCII + PNG)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .types import LayoutInstance, Port, TileCoord, WireEntry


@dataclass(frozen=True)
class RenderPinView:
    pin_id: str
    local_px: int
    local_py: int
    pin_grid_x: int
    pin_grid_y: int
    ports: tuple[Port, ...]


@dataclass(frozen=True)
class RenderCellView:
    x: int
    y: int
    layer: int
    device_id: str | None
    device_type: str | None
    pins: tuple[RenderPinView, ...]
    wires: tuple[WireEntry, ...]

    @property
    def has_device(self) -> bool:
        return self.device_id is not None

    @property
    def has_wires(self) -> bool:
        return bool(self.wires)


@dataclass(frozen=True)
class RenderLayerView:
    layer: int
    cells: dict[tuple[int, int], RenderCellView]


@dataclass(frozen=True)
class LayoutRenderView:
    cells_x: int
    cells_y: int
    layers: tuple[int, ...]
    by_layer: dict[int, RenderLayerView]


def build_render_view(layout: LayoutInstance) -> LayoutRenderView:
    cells_x = layout.grid.cells_x
    cells_y = layout.grid.cells_y

    pins_by_coord: dict[TileCoord, list[RenderPinView]] = {}
    device_by_coord: dict[TileCoord, tuple[str, str]] = {}
    for device in layout.devices:
        for layer in range(device.from_layer, device.to_layer + 1):
            coord = TileCoord(x=device.x, y=device.y, layer=layer)
            device_by_coord[coord] = (device.device_id, device.device_type)

        for pin in device.pins:
            coord = pin.tile
            pins_by_coord.setdefault(coord, []).append(
                RenderPinView(
                    pin_id=pin.pin_id,
                    local_px=pin.local_pos.px,
                    local_py=pin.local_pos.py,
                    pin_grid_x=device.pin_grid.cells_x,
                    pin_grid_y=device.pin_grid.cells_y,
                    ports=pin.attachment.ports,
                )
            )

    for pin_views in pins_by_coord.values():
        pin_views.sort(key=lambda p: p.pin_id)

    wires_by_coord: dict[TileCoord, tuple[WireEntry, ...]] = {}
    for wire_tile in layout.wire_tiles:
        coord = TileCoord(x=wire_tile.x, y=wire_tile.y, layer=wire_tile.layer)
        wires_by_coord[coord] = wire_tile.ordered_wires

    by_layer: dict[int, RenderLayerView] = {}
    layer_numbers = tuple(range(layout.grid.layers))
    for layer in layer_numbers:
        cells: dict[tuple[int, int], RenderCellView] = {}
        for y in range(cells_y):
            for x in range(cells_x):
                coord = TileCoord(x=x, y=y, layer=layer)
                device = device_by_coord.get(coord)
                cell = RenderCellView(
                    x=x,
                    y=y,
                    layer=layer,
                    device_id=None if device is None else device[0],
                    device_type=None if device is None else device[1],
                    pins=tuple(pins_by_coord.get(coord, [])),
                    wires=wires_by_coord.get(coord, ()),
                )
                cells[(x, y)] = cell
        by_layer[layer] = RenderLayerView(layer=layer, cells=cells)

    return LayoutRenderView(cells_x=cells_x, cells_y=cells_y, layers=layer_numbers, by_layer=by_layer)


def render_ascii(view: LayoutRenderView, mode: str = "compact") -> str:
    if mode not in {"compact", "detailed"}:
        raise ValueError("mode must be one of: compact, detailed")

    blocks: list[str] = []
    for layer in view.layers:
        layer_view = view.by_layer[layer]
        lines = [f"Layer {layer}"]
        for y in range(view.cells_y):
            row_tokens: list[str] = []
            for x in range(view.cells_x):
                cell = layer_view.cells[(x, y)]
                if mode == "compact":
                    row_tokens.append(_compact_token(cell))
                else:
                    row_tokens.append(_detailed_token(cell))
            lines.append(" ".join(row_tokens))

        if mode == "detailed":
            lines.append("details:")
            for y in range(view.cells_y):
                for x in range(view.cells_x):
                    cell = layer_view.cells[(x, y)]
                    if not (cell.has_device or cell.has_wires):
                        continue
                    details = [f"({x},{y})"]
                    if cell.has_device:
                        details.append(f"device={cell.device_id}:{cell.device_type}")
                        details.append(f"pins={_pins_repr(cell)}")
                    if cell.has_wires:
                        details.append(f"wires={_wires_repr(cell)}")
                    lines.append("  - " + " | ".join(details))

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _compact_token(cell: RenderCellView) -> str:
    if cell.has_device and cell.has_wires:
        return "B"
    if cell.has_device:
        return "D"
    if cell.has_wires:
        return "W"
    return "."


def _detailed_token(cell: RenderCellView) -> str:
    if cell.has_device and cell.has_wires:
        return "[DW]"
    if cell.has_device:
        return "[D ]"
    if cell.has_wires:
        return "[ W]"
    return "[  ]"


def _pins_repr(cell: RenderCellView) -> str:
    chunks: list[str] = []
    for pin in cell.pins:
        port_values = ",".join(f"{port.side}:{port.pos_idx}" for port in pin.ports)
        chunks.append(f"{pin.pin_id}@({pin.local_px},{pin.local_py})<{port_values}>")
    return "[" + "; ".join(chunks) + "]"


def _wires_repr(cell: RenderCellView) -> str:
    return "[" + "; ".join(
        f"{wire.wire_id}:{wire.net_id}:{wire.orientation}" for wire in cell.wires
    ) + "]"


def render_png_layers(
    view: LayoutRenderView,
    output_dir: Path,
    prefix: str = "layout",
    tile_size: int = 72,
    draw_ports: bool = False,
) -> list[Path]:
    try:
        from PIL import Image, ImageDraw
    except ModuleNotFoundError as exc:  # pragma: no cover - env dependent
        raise RuntimeError("Pillow is required for PNG rendering") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    grid_pad = 20
    width = grid_pad * 2 + view.cells_x * tile_size
    height = grid_pad * 2 + view.cells_y * tile_size

    paths: list[Path] = []
    for layer in view.layers:
        image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        _draw_grid(draw, view, tile_size, grid_pad)
        _draw_layer_cells(draw, view.by_layer[layer], tile_size, grid_pad, draw_ports)

        out_path = output_dir / f"{prefix}_layer{layer}.png"
        image.save(out_path)
        paths.append(out_path)

    return paths


def _draw_grid(draw, view: LayoutRenderView, tile_size: int, pad: int) -> None:
    x0 = pad
    y0 = pad
    x1 = pad + view.cells_x * tile_size
    y1 = pad + view.cells_y * tile_size
    draw.rectangle((x0, y0, x1, y1), outline=(70, 70, 70), width=2)

    for ix in range(view.cells_x + 1):
        x = pad + ix * tile_size
        draw.line((x, y0, x, y1), fill=(180, 180, 180), width=1)
    for iy in range(view.cells_y + 1):
        y = pad + iy * tile_size
        draw.line((x0, y, x1, y), fill=(180, 180, 180), width=1)


def _draw_layer_cells(draw, layer: RenderLayerView, tile_size: int, pad: int, draw_ports: bool) -> None:
    for (x, y), cell in layer.cells.items():
        left = pad + x * tile_size
        top = pad + y * tile_size
        right = left + tile_size
        bottom = top + tile_size

        if cell.has_device:
            draw.rectangle((left + 2, top + 2, right - 2, bottom - 2), fill=(188, 224, 255))
        if cell.has_wires:
            draw.rectangle((left + 8, top + 8, right - 8, bottom - 8), outline=(227, 126, 55), width=3)

        for pin in cell.pins:
            px = left + int(((pin.local_px + 0.5) / pin.pin_grid_x) * tile_size)
            py = top + int(((pin.local_py + 0.5) / pin.pin_grid_y) * tile_size)
            r = max(2, tile_size // 14)
            draw.ellipse((px - r, py - r, px + r, py + r), fill=(39, 97, 171), outline=(255, 255, 255))
            if draw_ports:
                _draw_ports(draw, left, top, tile_size, pin)


def _draw_ports(draw, left: int, top: int, tile_size: int, pin: RenderPinView) -> None:
    for port in pin.ports:
        if port.side == "north":
            x = left + int(((port.pos_idx + 0.5) / pin.pin_grid_x) * tile_size)
            y = top + 2
        elif port.side == "south":
            x = left + int(((port.pos_idx + 0.5) / pin.pin_grid_x) * tile_size)
            y = top + tile_size - 2
        elif port.side == "west":
            x = left + 2
            y = top + int(((port.pos_idx + 0.5) / pin.pin_grid_y) * tile_size)
        else:  # east
            x = left + tile_size - 2
            y = top + int(((port.pos_idx + 0.5) / pin.pin_grid_y) * tile_size)

        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(100, 100, 100))


def render_layout_ascii(layout: LayoutInstance, mode: str = "compact") -> str:
    return render_ascii(build_render_view(layout), mode=mode)


def render_layout_png_layers(
    layout: LayoutInstance,
    output_dir: Path,
    prefix: str = "layout",
    tile_size: int = 72,
    draw_ports: bool = False,
) -> list[Path]:
    return render_png_layers(
        build_render_view(layout),
        output_dir=output_dir,
        prefix=prefix,
        tile_size=tile_size,
        draw_ports=draw_ports,
    )
