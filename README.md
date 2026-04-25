# Grid Layout Generator

Python tooling for generating grid-based circuit layouts from structured specifications.

The project implements a transformation pipeline that converts capacitor/resistor
array specifications into multiple intermediate and final representations:
- grid classifications
- layout skeletons
- generic `layout3d` layouts
- semantic device annotations
- netlists
- renderable outputs (ASCII / PNG / HTML)

---

## Pipeline Overview

```
Spec → Validation → Derivation
     → Grid Classification
     → Layout Skeleton
     → layout3d Layout
     → Semantic Enrichment
     → Netlist / Rendering
```

The pipeline is intentionally modular, allowing inspection and testing of each stage.

---

## Installation

```bash
pip install -e .[dev]
```

Requirements:
- Python ≥ 3.10

---

## Usage

### Debug Pipeline

```bash
grid-layout-debug <input.json>
```

Runs the full pipeline and outputs intermediate stages for inspection.

---

### Render Layout

```bash
grid-layout-render <input.json>
```

Generates visual representations (ASCII / PNG / HTML).

---

## Project Structure

```
src/
  gridlayout/
    debug/
    render/
    ...
  layout3d/

docs/
  pipeline.md

tests/
examples/
```

---

## Development

Run tests:

```bash
pytest
```

Format & lint:

```bash
black .
ruff check .
```

---

## Notes

This project evolved from an earlier scope focused on
`circuit-array-spec` (parsing + validation). It now represents a full
layout generation pipeline.

---

## License

TBD
