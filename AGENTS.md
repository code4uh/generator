# AGENTS.md

## Projektziel
Dieses Repository modelliert und validiert ein **strictly discrete rasterbasiertes 3D-Layout** (Grid, Devices, Pins, WireTiles) deterministisch, testbar und ohne implizite Geometrie.

## Domäneninvarianten
- Grid ist vollständig diskret: Koordinaten sind `(x, y, layer)`.
- Device belegt **genau ein** XY-Tile und eine zusammenhängende Layer-Spanne `fromLayer..toLayer`.
- WireTile belegt **genau ein** XY-Tile auf **genau einem** Layer.
- `Port.side` ist genau einer von: `north`, `east`, `south`, `west`.
- `Port.pos_idx` ist ein diskreter Index entlang der jeweiligen Kante.
- Mehrere Ports pro Pin sind erlaubt und bedeuten OR-Semantik.

## Regeln für Änderungen
- Keine implizite Geometrie, keine Nachbarschaftsannahmen, keine versteckte Konnektivität.
- **Kein Routing** einführen, außer es wird ausdrücklich angefordert.
- Strukturierte Fehlerobjekte beibehalten (kein Fallback auf freie Fehlerstrings).
- Öffentliche API möglichst stabil halten; Breaking Changes nur mit Begründung.
- Kleine, reine Funktionen bevorzugen; Seiteneffekte vermeiden.

## Test- und Validierungsworkflow
1. Änderungen implementieren.
2. Relevante Unit-Tests ergänzen/aktualisieren.
3. `pytest -q` lokal ausführen.
4. Bei neuen Features/Regeln: immer mindestens einen positiven und einen negativen Testfall mitliefern.

## Qualitätsregeln
- Neue Features immer mit Tests liefern.
- Bestehende Invarianten dürfen nicht stillschweigend aufgeweicht werden.
- Bei Refactorings: fachliches Verhalten unverändert halten, sofern nicht explizit anders gefordert.
