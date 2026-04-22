# CapArrayGridGenerator V1 (Device/Wire-Klassifikation)

Diese Notiz beschreibt die bewusst kleine V1-Logik des `CapArrayGridGenerator`.

## Aktiv verwendete Cap-Parameter

1. `topology.cap_list`
   - bestimmt die Anzahl der Core-Device-Tiles.
2. `placement.rows`
   - bestimmt die Core-Zeilenanzahl.
3. `placement.algorithm`
   - `side-by-side`: zeilenweise Enumeration.
   - `side-by-side-row-wise`: spaltenweise Enumeration.
   - `common_centroid`: einfache center-first Heuristik.
   - `user`: Pattern-Shape wird direkt genutzt.
4. `placement.pattern`
   - nur bei `algorithm = user`; Pattern bestimmt Device-Positionen im Core.
5. `topology.boundary_caps`
   - `left/right/top/bottom`: aktiviert Boundary-Device-Bereiche.
   - `boundary_size`: in V1 auf Dicke 1 normalisiert (`Unit` und `Minimum`).
6. `topology.connect_dummy_caps`
   - wird bewusst als No-Op für reine Tile-Kind-Klassifikation behandelt.

## Layer-Regel in V1

Die XY-Klassifikation wird identisch auf alle Layer kopiert.

## Bewusst nicht implementiert in V1

- Erzeugung konkreter `layout3d.Device`-Objekte
- konkrete WireTile-Inhalte
- Pins
- Routing
- Kanalzuweisung
- Via-/Wire-Breiten-Feinparameter
