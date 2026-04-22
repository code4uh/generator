# --- Config ---
PYTHON := python
MODULE := circuit_array_spec.debug_cli
SRC := src

# Default files (kannst du überschreiben)
CAP_EXAMPLE := examples/json/cap_array_v0_1.json
RES_EXAMPLE := examples/json/res_array_v0_1.json

LAYERS ?= 2
STAGE ?= all

# --- Helper ---
export PYTHONPATH := $(SRC)

# --- Targets ---

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make cap            # cap example (all stages)"
	@echo "  make res            # res example (all stages)"
	@echo "  make grid           # only grid stage"
	@echo "  make skeleton       # only skeleton stage"
	@echo "  make layout         # only layout stage"
	@echo "  make run FILE=...   # custom file"
	@echo "  make diff           # diff two runs"
	@echo ""
	@echo "Optional vars:"
	@echo "  LAYERS=2"
	@echo "  STAGE=all"

# --- Standard runs ---

.PHONY: cap
cap:
	$(PYTHON) -m $(MODULE) $(CAP_EXAMPLE) --stage all --layers $(LAYERS)

.PHONY: res
res:
	$(PYTHON) -m $(MODULE) $(RES_EXAMPLE) --stage all --layers $(LAYERS)

.PHONY: grid
grid:
	$(PYTHON) -m $(MODULE) $(CAP_EXAMPLE) --stage grid --layers $(LAYERS)

.PHONY: skeleton
skeleton:
	$(PYTHON) -m $(MODULE) $(CAP_EXAMPLE) --stage skeleton --layers $(LAYERS)

.PHONY: layout
layout:
	$(PYTHON) -m $(MODULE) $(CAP_EXAMPLE) --stage layout --layers $(LAYERS)

# --- Custom run ---

.PHONY: run
run:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run FILE=path/to/file.json [STAGE=...] [LAYERS=...]"; \
		exit 1; \
	fi
	$(PYTHON) -m $(MODULE) $(FILE) --stage $(STAGE) --layers $(LAYERS)

# --- Debugging helpers ---

.PHONY: dump
dump:
	$(PYTHON) -m $(MODULE) $(CAP_EXAMPLE) --stage all --layers $(LAYERS) > debug.txt
	@echo "Wrote debug.txt"

.PHONY: dump-res
dump-res:
	$(PYTHON) -m $(MODULE) $(RES_EXAMPLE) --stage all --layers $(LAYERS) > debug_res.txt
	@echo "Wrote debug_res.txt"

.PHONY: diff
diff:
	@if [ ! -f debug_old.txt ] || [ ! -f debug.txt ]; then \
		echo "Need debug_old.txt and debug.txt"; \
		exit 1; \
	fi
	diff debug_old.txt debug.txt || true