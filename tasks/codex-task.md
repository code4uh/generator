# Codex Task

## Ziel

Implementiere einen Parser, Validator und erste Ableitungslogik für die Circuit Array Specification v0.1.

## Zuerst lesen

Bitte lies zuerst vollständig:

- `spec/circuit-array-spec.md`
- `spec/circuit-array.schema.json`
- `spec/examples/cap_array.example.json`
- `spec/examples/res_array.example.json`

## Scope

Implementiere Unterstützung für:

- `cap_array`
- `res_array`

## Aufgaben

### 1. Datenmodelle
Implementiere interne Datenmodelle für beide Typen.

### 2. JSON-Schema-Validierung
Validiere Input-Dateien gegen `spec/circuit-array.schema.json`.

### 3. Semantische Validierung
Implementiere zusätzliche semantische Regeln, die nicht vollständig im Schema ausdrückbar sind.

#### cap_array
- `placement.algorithm = "user"` → `placement.pattern` erforderlich
- sonst → `placement.pattern = null`
- `topology.plusConnected` nur bei `topology.connection = "userDefined"`
- `plusConnected` muss gültige 1-basierte Kapazitätsindizes enthalten
- keine doppelten Kapazitätsindizes in `plusConnected`

#### res_array
- `placement.algorithm` muss `"side-by-side"` sein
- `placement.pattern` muss `null` sein
- abgeleitet:
  - `rows = len(res_list) * parallelResNo`
  - `cols = max(res_list)`

### 4. Ableitungsfunktionen
Implementiere mindestens diese Funktionen:

- `expand_cap_devices(spec)`
- `expand_res_devices(spec)`
- `derive_cap_grid(spec)`
- `derive_res_grid(spec)`

#### Erwartung für cap_array
- reale Caps expandieren zu `C<i>_<j>`
- Dummy-Caps mit `C0_<idx>`

#### Erwartung für res_array
- reale Resistoren expandieren zu `R<divider>_<series>_<parallel>`
- Dummy-Resistoren mit `R0_<idx>`

### 5. Tests
Erzeuge Unit-Tests für:

- gültiges `cap_array` Beispiel
- gültiges `res_array` Beispiel
- mindestens je 2 ungültige Beispiele

### 6. README
Erzeuge eine kurze `README.md` mit:
- wie validiert wird
- wie die Ableitung aufgerufen wird
- wie Tests gestartet werden

## Konfliktbehandlung

Wenn Markdown-Spec und JSON-Schema voneinander abweichen:

- behandle die Markdown-Spec als fachliche Quelle
- dokumentiere die Abweichung im Code oder in der README

## Erwartetes Ergebnis

- sauber strukturierter Code
- Tests
- README
- klare Trennung zwischen Schema-Validierung und semantischer Validierung
