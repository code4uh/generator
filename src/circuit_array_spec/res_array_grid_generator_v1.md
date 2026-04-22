# ResArrayGridGenerator V1 (Device/Wire-Klassifikation)

Diese Notiz beschreibt die bewusst kleine V1-Logik des `ResArrayGridGenerator`.

## Aktiv verwendete Res-Parameter

1. `topology.res_list`
   - bestimmt die Anzahl der Widerstandsgruppen.
2. `topology.parallel_res_no`
   - multipliziert die Anzahl der Device-Tiles im Core.
3. `placement.algorithm`
   - in V1 nur `side-by-side` unterstützt (gemäß Modell).
4. `topology.boundary_resistors`
   - `left/right/top/bottom`: aktiviert Boundary-Device-Bereiche.
   - `boundary_device_size`: Boundary-Device-Größen-/Typ-Metadatum (`Unit`/`Minimum`);
     wird in V1 validiert/gelesen, beeinflusst die Geometrie aber nicht.
5. `topology.connect_dummy_res`
   - wird bewusst als No-Op für reine Tile-Kind-Klassifikation behandelt.

## Layer-Regel in V1

Die XY-Klassifikation wird identisch auf alle Layer kopiert.

Die geometrische Boundary-Ausdehnung in V1 wird ausschließlich durch
`left/right/top/bottom` bestimmt (je aktivierter Seite ein Boundary-Ring).

## Bewusst nicht implementiert in V1

- Erzeugung konkreter `layout3d.Device`-Objekte
- konkrete WireTile-Inhalte
- Pins
- Routing
- Kanalzuweisung
- Via-/Wire-Breiten-Feinparameter
