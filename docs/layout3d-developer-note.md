# Layout3D – Entwicklernotiz

## Überblick
Das aktuelle `layout3d`-Modell umfasst:

- **Grid**: diskrete Ausdehnung über `cellsX`, `cellsY`, `layers`.
- **DeviceSlots**: erlauben Device-Typen auf genau einem XY-Tile mit Layer-Spannenvorgabe.
- **Devices**: Instanzen auf genau einem XY-Tile + Layer-Spanne.
- **Pins** (innerhalb Devices): lokales Pin-Grid (`pinGrid`) und Tile-/Local-Position.
- **WireTiles**: diskrete Wire-Belegung eines einzelnen Tiles auf einem einzelnen Layer.

## Abgrenzung
Dieses Modell enthält **bewusst kein Routing**:
- keine impliziten Verbindungen zwischen Tiles
- keine Nachbarschaftslogik
- keine Pfadsuche

## Wichtigste JSON-Strukturen

### Grid
```json
{
  "grid": { "cellsX": 3, "cellsY": 3, "layers": 2 }
}
```

### DeviceSlot + Device + Pin
```json
{
  "deviceSlots": [
    {
      "slotId": "slotA",
      "allowedDeviceTypes": ["amp"],
      "x": 1,
      "y": 1,
      "fromLayer": 0,
      "toLayer": 1
    }
  ],
  "devices": [
    {
      "deviceId": "dev1",
      "deviceType": "amp",
      "slotId": "slotA",
      "x": 1,
      "y": 1,
      "fromLayer": 0,
      "toLayer": 1,
      "pinGrid": { "cellsX": 2, "cellsY": 2 },
      "pins": [
        {
          "pinId": "p1",
          "tile": { "x": 1, "y": 1, "layer": 0 },
          "localPos": { "px": 0, "py": 0 },
          "attachment": {
            "ports": [
              { "side": "north", "pos_idx": 0 },
              { "side": "east", "pos_idx": 1 }
            ]
          }
        }
      ]
    }
  ]
}
```

### WireTile
```json
{
  "wireTiles": [
    {
      "wireTileId": "wt1",
      "x": 2,
      "y": 1,
      "layer": 0,
      "orderedWires": [
        {
          "wireId": "w1",
          "wireType": "sig",
          "netId": "n1",
          "orientation": "horizontal"
        }
      ]
    }
  ]
}
```

## Verwendete Pipeline
1. `parse_layout_json` / `parse_layout`
2. `normalize_layout`
3. `LayoutValidator.validate`
4. `build_tile_representation`

## Namespace-Hinweis
- Kanonischer Import: `layout3d`
- `circuit_array_spec.layout3d` ist als rückwärtskompatibler Re-Export vorhanden.
