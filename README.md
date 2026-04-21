# circuit-array-spec

Parser-, Validierungs- und Ableitungs-Helfer für die Circuit Array Specification v0.1.

## Installation

```bash
pip install -e .
```

## Validierung

Die Validierung erfolgt in zwei Schritten:

1. **JSON-Schema-Validierung** mit `jsonschema` (Draft 2020-12) gegen `spec/schema/circuit-array.schema.json`
2. **Semantische Validierung** für zusätzliche Fachregeln (z. B. `plusConnected`, `placement`-Regeln)

```python
import json
from pathlib import Path

from circuit_array_spec.validator import validate_spec

spec = json.loads(Path("examples/json/cap_array_v0_1.json").read_text())
model = validate_spec(spec)
print(type(model).__name__)
```

## Ableitungsfunktionen

```python
from circuit_array_spec.derive import (
    expand_cap_devices,
    derive_cap_grid,
    expand_res_devices,
    derive_res_grid,
)

cap_devices = expand_cap_devices(cap_spec)
cap_grid = derive_cap_grid(cap_spec)  # enthält rows, cols, grid

res_devices = expand_res_devices(res_spec)
res_grid = derive_res_grid(res_spec)  # enthält rows, cols, grid
```


## Aktueller Stand der Cap-Placement-Ableitung

`derive_cap_grid()` unterscheidet aktuell nur zwischen:

- `algorithm == "user"`: `placement.pattern` wird direkt übernommen
- alle anderen Algorithmen (`common_centroid`, `side-by-side`, `side-by-side-row-wise`):
  es wird eine generische zeilenweise Default-Platzierung erzeugt

Das bedeutet: **die algorithmischen Unterschiede der drei Nicht-`user`-Algorithmen sind derzeit noch nicht separat implementiert**.

## Tests starten

```bash
pytest -q
```

## Hinweis zu Konflikten zwischen Markdown-Spec und JSON-Schema

Wenn Markdown-Spec und JSON-Schema abweichen, behandelt diese Implementierung die
Markdown-Spec als fachliche Quelle und ergänzt dafür semantische Prüfungen
zusätzlich zum Schema.


## Netlist-Generierung

Die Netlist-Ausgabe ist SPICE-ähnlich und nutzt Defaultwerte:

- `cap_array`: `1f`, `W=1u`, `L=1u`
- `res_array`: `1k`, `W=1u`, `L=1u`

Für `cap_array` mit `connectDummyCaps = "open_floating"` werden keine Dummy-/Boundary-Cap-Zeilen erzeugt.

## Developer Note: Rasterbasiertes 3D-Layout

Kanonischer Namespace ist `layout3d` (die alten Pfade unter `circuit_array_spec.layout3d` bleiben als Kompatibilitäts-Wrapper erhalten).

Module unter `layout3d` trennen strikt:

1. `parser.py`: Mapping/JSON -> typsichere Domänenobjekte
2. `normalize.py`: deterministische Sortierung ohne implizite Geometrie
3. `validation.py`: regelbasierte Basisvalidierung mit strukturierten `ValidationIssue`s
4. `representation.py`: interne tile-basierte Repräsentation (`TileRepresentation`)
5. `pipeline.py`: explizite Orchestrierung der Schritte

Semantik:
- ausschließlich diskrete Tiles `(x, y, layer)`
- Devices belegen zusammenhängende Layer-Spannen auf genau einem XY-Tile
- keine impliziten Nachbarschaften oder Routing-Logik
- WireTiles gelten immer nur für genau einen Layer

Zusätzlich unterstützt `layout3d` jetzt JSON-Ein-/Ausgabe (`parse_layout_json`, `layout_to_dict`, `layout_to_json`)
sowie Normalisierungs-Lookups (ID-Maps, Device-Tile-Expansion, WireTile-Map pro `(x,y,layer)`).

Eine kompakte Entwicklerdokumentation liegt unter `docs/layout3d-developer-note.md`.

## Rendering (ASCII + PNG)

Das Layout kann auf Basis der bestehenden Tile-Repräsentation gerendert werden:

```python
from pathlib import Path
import json

from layout3d import parse_layout
from layout3d.render import build_render_view, render_ascii, render_png_layers

data = json.loads(Path("examples/json/simple_layout.json").read_text())
layout = parse_layout(data)
view = build_render_view(layout)

print(render_ascii(view, mode="compact"))
print(render_ascii(view, mode="detailed"))

render_png_layers(view, output_dir=Path("out/render"), prefix="simple")
```

Kleiner CLI-Demo-Einstiegspunkt:

```bash
PYTHONPATH=src python -m layout3d.render_demo examples/json/simple_layout.json --ascii-mode detailed --png-out out/render
```
