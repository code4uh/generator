# Circuit Array Specification v0.1

## 1. Überblick

Diese Spezifikation definiert ein JSON-Format zur Beschreibung von:

- `cap_array`
- `res_array`

Ziel ist die deterministische Generierung von:

- Devices
- Grid
- Routing
- Netlist/Layout

Top-Level-Struktur:

```json
{
  "version": "0.1",
  "type": "cap_array | res_array",
  "inputs": { ... },
  "capabilities": { ... },
  "output": { ... }
}
```

---

## 2. Gemeinsame Sections

### 2.1 output

```json
"output": {
  "libname": "string",
  "cellname": "string"
}
```

- `libname`: Zielbibliothek
- `cellname`: Zielzelle

### 2.2 capabilities

Die `capabilities`-Section beschreibt, welche Teile der Spec von der aktuellen Implementierung tatsächlich unterstützt werden.

Typische Felder:

- `placement.supported_algorithms`
- `placement.pattern_supported`
- `routing.level`
- `advanced.level`
- optional `advanced.supported_fields`
- `unsupported_option_policy`

Zulässige Policies:

- `ignore`
- `ignore_with_warning`
- `error`

---

## 3. cap_array

Ein `cap_array` ist eine Sammlung logischer Kapazitäten, wobei jede Kapazität aus mehreren parallelen physischen Kondensatoren besteht.

### 3.1 topology

```json
"topology": {
  "cap_list": [3, 4, 3, 2],
  "connection": "userDefined",
  "plusConnected": "(1, 2) (3, 4)",
  "connectDummyCaps": "shorted_G1_p",
  "boundary_caps": {
    "left": true,
    "right": true,
    "top": false,
    "bottom": true,
    "boundary_device_size": "unit"
  }
}
```

#### cap_list

Jeder Eintrag beschreibt eine logische Kapazität.
Der Wert gibt die Anzahl paralleler physischer Caps an.

Naming-Regel:

```text
C<i>_<j>
```

Beispiel für `cap_list = [3, 4]`:

- `C1_1`, `C1_2`, `C1_3`
- `C2_1`, `C2_2`, `C2_3`, `C2_4`

#### connection

Zulässige Werte:

- `open`
- `shortPlusPins`
- `userDefined`

Bedeutung:

- `open`: keine zusätzliche Verbindung der Plus-Pins
- `shortPlusPins`: alle realen Plus-Pins werden verbunden, Netzname später `G1_p`
- `userDefined`: Gruppen werden über `plusConnected` definiert

#### plusConnected

Beispiel:

```text
"(1, 2) (3, 4)"
```

Bedeutung:

- Kapazitäten 1 und 2 bilden Gruppe 1 → `G1_p`
- Kapazitäten 3 und 4 bilden Gruppe 2 → `G2_p`

Regeln:

- nur gültig bei `connection = "userDefined"`
- Indizes sind 1-basiert und referenzieren `cap_list`
- jede Kapazität darf höchstens einmal vorkommen
- nicht genannte Kapazitäten bleiben unverbunden

#### connectDummyCaps

Gilt für:

- Dummy-Caps
- Boundary-Caps

Zulässige Werte:

- `open_floating`
- `open_shorted`
- `shorted_G1_p`
- `shorted_Cdmy_p`
- `Cdmy_p+Cdmy_n`

#### boundary_caps

```json
{
  "left": true,
  "right": true,
  "top": false,
  "bottom": true,
  "boundary_device_size": "unit"
}
```

- `left/right/top/bottom`: Boundary-Caps auf jeweiliger Seite aktiv/inaktiv
- `boundary_device_size`: `unit` oder `minimum`

### 3.2 placement

```json
"placement": {
  "rows": 3,
  "algorithm": "common_centroid",
  "pattern": null
}
```

Parameter:

- `rows`: Anzahl Grid-Zeilen
- `algorithm`:
  - `common_centroid`
  - `side-by-side`
  - `side-by-side-row-wise`
  - `user`
- `pattern`: explizites Grid, nur wenn `algorithm = "user"`

Regeln:

- `algorithm = "user"` → `pattern` muss gesetzt sein
- sonst → `pattern = null`

Pattern-Einträge bestehen aus:

- realen Caps: `C<i>_<j>`
- Dummy-Caps: `C0_<idx>`

### 3.3 dummy_caps

```json
"dummy_caps": {
  "naming_rule": "C0_<idx>"
}
```

Dummy-Caps füllen leere Grid-Zellen.

### 3.4 routing_options

```json
"routing_options": {
  "nVias": 2,
  "wireWidthHor": 0.4,
  "wireWidthVer": 0.4,
  "wireWidthPlus": 0.6,
  "wireWidthMinus": 0.6,
  "truncVerWires": true,
  "truncHorWires": false,
  "verWireAssignment": "minus-plus",
  "horWireAssignment": "symmetric",
  "verShielding": "shield-pin",
  "horShielding": "plus-minus",
  "guardRingOptions": {
    "left": true,
    "right": true,
    "top": true,
    "bottom": false
  },
  "addGuardRingSpacing": 0.8
}
```

Wichtige Enums:

- `verWireAssignment`:
  - `minus-plus`
  - `separate-plus-minus`

- `horWireAssignment`:
  - `all-bottom`
  - `all-top`
  - `symmetric`
  - `separate-plus-minus`

- `verShielding`:
  - `shield-pin`
  - `Cdmy_n`

- `horShielding`:
  - `device-bus`
  - `plus-minus`
  - `outer-edge`

### 3.5 advanced

```json
"advanced": {
  "horDevSpacing": 0.2,
  "verDevSpacing": 0.2,
  "minHorDevBusSpacing": 0.15,
  "minVerDevBusSpacing": 0.15,
  "noRouting": false,
  "onlyVerticalWires": false,
  "omitHorizontalBus": false,
  "deleteFloatingWires": true,
  "wireSpaceHor": 0.1,
  "wireSpaceVer": 0.1
}
```

Bedeutung:

- `horDevSpacing`, `verDevSpacing`: Device-Abstände, dürfen negativ sein
- `minHorDevBusSpacing`, `minVerDevBusSpacing`: Mindestabstände Device ↔ Bus
- `noRouting`: Routing komplett deaktivieren
- `onlyVerticalWires`: nur vertikale Leitungen erzeugen
- `omitHorizontalBus`: keine horizontalen Busse erzeugen
- `deleteFloatingWires`: unverbundene Leitungen löschen
- `wireSpaceHor`, `wireSpaceVer`: Abstand zwischen Leitungen

### 3.6 capabilities

```json
"capabilities": {
  "placement": {
    "supported_algorithms": [
      "common_centroid",
      "side-by-side",
      "side-by-side-row-wise",
      "user"
    ],
    "pattern_supported": true
  },
  "routing": {
    "level": "full"
  },
  "advanced": {
    "level": "full"
  },
  "unsupported_option_policy": "ignore_with_warning"
}
```

---

## 4. res_array

Ein `res_array` ist ein Array von Spannungsteilern.

Jeder Eintrag in `res_list` beschreibt genau einen Spannungsteiler.
Der Wert gibt die Anzahl serieller Widerstände in diesem Spannungsteiler an.
Jeder serielle Widerstand wird durch `parallelResNo` parallele primitive Widerstände realisiert.

### 4.1 topology

```json
"topology": {
  "res_list": [3, 4, 2],
  "parallelResNo": 2,
  "connectDummyRes": "VSS",
  "boundary_resistors": {
    "left": true,
    "right": true,
    "top": false,
    "bottom": true,
    "boundary_device_size": "unit"
  }
}
```

#### res_list

Beispiel:

```text
[3, 4, 2]
```

bedeutet:

- Divider 1: 3 serielle Widerstände
- Divider 2: 4 serielle Widerstände
- Divider 3: 2 serielle Widerstände

#### parallelResNo

Anzahl paralleler primitiver Widerstände pro Serien-Stufe.

#### connectDummyRes

Zulässige Werte:

- `open_floating`
- `VSS`

Bedeutung:

- `open_floating`: keine Verbindung
- `VSS`: Dummy- und Boundary-Resistoren an `VSS`

#### boundary_resistors

```json
{
  "left": true,
  "right": true,
  "top": false,
  "bottom": true,
  "boundary_device_size": "unit"
}
```

### 4.2 placement

```json
"placement": {
  "algorithm": "side-by-side",
  "pattern": null
}
```

Regeln:

- `algorithm` muss `"side-by-side"` sein
- `pattern` muss `null` sein

### 4.3 Grid-Ableitung

Für `res_array` wird das Grid nicht gespeichert, sondern abgeleitet:

```text
rows = len(res_list) * parallelResNo
cols = max(res_list)
```

Interpretation:

- jede Zeile = ein paralleler Zweig eines Dividers
- jede Spalte = eine Serienposition

### 4.4 dummy_resistors

```json
"dummy_resistors": {
  "naming_rule": "R0_<idx>"
}
```

### 4.5 Naming

Primitive reale Widerstände:

```text
R<divider>_<series>_<parallel>
```

Beispiel:

```text
R2_3_1
```

bedeutet:

- Divider 2
- Serien-Stufe 3
- paralleles Element 1

Dummy-Widerstände:

```text
R0_<idx>
```

Boundary-Widerstände:

```text
RB_<side>_<idx>
```

mit `side ∈ {L, R, T, B}`.

### 4.6 Netlist-Modell

Primitive Zeile:

```text
R<divider>_<series>_<parallel> <plus_net> <minus_net> <value_or_model>
```

Netze:

- `G<i>_p` → Eingang des Dividers
- `N<i>_<j>` → interner Knoten
- `D<i>_n` → Ausgang des Dividers

### 4.7 routing_options / advanced

Die Struktur ist identisch zu `cap_array`.
Aktuell werden bei `res_array` aber nur folgende `advanced`-Felder aktiv genutzt:

- `horDevSpacing`
- `verDevSpacing`

Andere Felder sind reserviert und dürfen ignoriert werden.

### 4.8 capabilities

```json
"capabilities": {
  "placement": {
    "supported_algorithms": ["side-by-side"],
    "pattern_supported": false
  },
  "routing": {
    "level": "partial"
  },
  "advanced": {
    "level": "partial",
    "supported_fields": [
      "horDevSpacing",
      "verDevSpacing"
    ]
  },
  "unsupported_option_policy": "ignore_with_warning"
}
```

---

## 5. Common Conflict Rules

### 5.1 cap_array

- `algorithm = "user"` → `pattern` erforderlich
- sonst → `pattern = null`

### 5.2 noRouting

Wenn `advanced.noRouting = true`:

- Routing-, Shielding-, Guard-Ring- und Cleanup-Optionen werden ignoriert

### 5.3 onlyVerticalWires

Wenn `advanced.onlyVerticalWires = true`:

- horizontale Routing-Optionen werden ignoriert

### 5.4 omitHorizontalBus

Wenn `advanced.omitHorizontalBus = true`:

- horizontale Busse werden nicht erzeugt

### 5.5 Priorität

```text
onlyVerticalWires > omitHorizontalBus
```

### 5.6 Ignorierte Optionen

Nicht unterstützte oder übersteuerte Optionen:

- erzeugen keinen Fehler
- dürfen eine Warnung erzeugen

### 5.7 Negative Device-Spacings

- `horDevSpacing`, `verDevSpacing` dürfen negativ sein
- geometrische Unzulässigkeit ist kein Spec-Fehler, sondern ein Layout-/Generatorfehler
