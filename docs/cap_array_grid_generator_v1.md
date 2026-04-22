# CapArrayGridGenerator V1 (Tile-Klassifikation)

## Aktiv verwendete Cap-Parameter

- `topology.cap_list`
- `topology.boundary_caps.left/right/top/bottom`
- `topology.boundary_caps.boundary_size`
- `topology.connect_dummy_caps` (in V1 explizit gelesen, aber ohne Einfluss auf TileKind)
- `placement.rows`
- `placement.algorithm`
- `placement.pattern` (nur für `algorithm = user`)

## V1-Layer-Regel

- Layer sind ein expliziter Parameter von `generate(..., layers=...)`.
- Dieselbe XY-Klassifikation wird auf allen Layern repliziert.

## V1-Algorithmusverhalten

- `side-by-side`: einfache zeilenweise Blockverteilung.
- `side-by-side-row-wise`: einfache spaltenweise Verteilung (sichtbar anders als `side-by-side`).
- `common_centroid`: center-first Heuristik (bewusst nur grobe V1-Näherung, keine Analog-Qualität).
- `user`: `placement.pattern` bestimmt die Device-Positionen direkt.

## Bewusst eingeschränkt in V1

- `boundary_caps.boundary_size`: aktuell diskret auf Randdicke `1` normalisiert (für `Unit` und `Minimum`).
- `connect_dummy_caps`: hat in V1 keinen Einfluss auf Device/Wire-TileKind (Routing/Netzlogik ist out of scope).
