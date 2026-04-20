# circuit-array-spec

Parser-, Validierungs- und Ableitungs-Helfer für die Circuit Array Specification v0.1.

## Installation

```bash
pip install -e .
```

## Validierung

Die Validierung erfolgt in zwei Schritten:

1. **JSON-Schema-Validierung** mit `jsonschema` gegen `spec/circuit-array.schema.json`
2. **Semantische Validierung** für zusätzliche Fachregeln (z. B. `plusConnected`, `placement`-Regeln)

```python
import json
from pathlib import Path

from circuit_array_spec.validator import validate_spec

spec = json.loads(Path("spec/examples/cap_array.example.json").read_text())
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
