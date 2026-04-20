# circuit-array-spec

Referenz-Repo für die Circuit Array Specification v0.1.

## Inhalt

- `spec/`
  - `circuit-array-spec.md` – fachliche Spezifikation
  - `circuit-array.schema.json` – JSON Schema
  - `examples/`
    - `cap_array.example.json`
    - `res_array.example.json`
- `tasks/`
  - `codex-task.md` – konkrete Implementierungsaufgabe für Codex
- `src/circuit_array_spec/`
  - Platz für Parser, Validator und Ableitungslogik
- `tests/`
  - Unit-Tests
- `docs/`
  - zusätzliche Doku
- `examples/`
  - optionale Laufzeitbeispiele / Demo-Inputs

## Empfohlener Entwicklungsplan

1. JSON-Schema-Validierung implementieren
2. Semantische Validierung ergänzen
3. Device-Expansion implementieren
4. Grid-Ableitung implementieren
5. Netlist-/Layout-Ableitung ergänzen
6. Tests vervollständigen

## Wichtige Dateien

### Fachliche Quelle
`spec/circuit-array-spec.md`

### Formale Struktur
`spec/circuit-array.schema.json`

### Referenzbeispiele
- `spec/examples/cap_array.example.json`
- `spec/examples/res_array.example.json`

## Erwartete Kernfunktionen

### cap_array
- `expand_cap_devices(spec)`
- `derive_cap_grid(spec)`

### res_array
- `expand_res_devices(spec)`
- `derive_res_grid(spec)`

## Semantische Regeln, die zusätzlich zum Schema geprüft werden sollten

### cap_array
- `placement.algorithm = "user"` → `placement.pattern` erforderlich
- sonst → `placement.pattern = null`
- `topology.plusConnected` nur bei `topology.connection = "userDefined"`
- `plusConnected` muss gültige 1-basierte Kapazitätsindizes enthalten
- keine doppelten Kapazitätsindizes in `plusConnected`

### res_array
- `placement.algorithm` muss `"side-by-side"` sein
- `placement.pattern` muss `null` sein
- abgeleitet:
  - `rows = len(res_list) * parallelResNo`
  - `cols = max(res_list)`

## Beispiel: Python-Startpunkt

```python
from pathlib import Path
import json

spec = json.loads(Path("spec/examples/cap_array.example.json").read_text())

# 1. schema validate
# 2. semantic validate
# 3. derive devices / grid
```

## Git-Nutzung

```bash
git init
git add .
git commit -m "Initial circuit array spec bundle"
```

## Hinweis

Wenn Markdown-Spec und JSON-Schema voneinander abweichen, sollte die Markdown-Spec als fachliche Quelle behandelt werden.
