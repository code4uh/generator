# --- Config ---
PYTHON := python

# Modules
DEBUG_MODULE := arraylayout.debug.cli
RENDER_MODULE := arraylayout.render.cli

# Paths
SRC := src
CAP_EXAMPLE := examples/json/cap_array_v0_1.json
RES_EXAMPLE := examples/json/res_array_v0_1.json

# Common options
LAYERS ?= 2
STAGE ?= all
ASCII_MODE ?= detailed

# Render output
PNG_OUT ?= out
HTML_OUT ?= out/gallery.html
PREFIX ?= demo

# Export Python path
export PYTHONPATH := $(SRC)

# --- Targets ---

.PHONY: help
help:
	@echo "Debug:"
	@echo "  make cap                        # debug cap example (all stages)"
	@echo "  make res                        # debug res example (all stages)"
	@echo "  make grid                       # debug only grid stage for cap example"
	@echo "  make skeleton                   # debug only skeleton stage for cap example"
	@echo "  make layout                     # debug only layout stage for cap example"
	@echo "  make run FILE=...               # debug custom file"
	@echo "  make dump                       # write cap debug output to debug.txt"
	@echo "  make dump-res                   # write res debug output to debug_res.txt"
	@echo "  make diff                       # diff debug_old.txt and debug.txt"
	@echo ""
	@echo "Render:"
	@echo "  make render-cap                 # cap example -> layer PNGs"
	@echo "  make render-res                 # res example -> layer PNGs"
	@echo "  make render-cap-html            # cap example -> layer PNGs + HTML gallery"
	@echo "  make render-res-html            # res example -> layer PNGs + HTML gallery"
	@echo "  make render-cap-stacked         # cap example -> stacked PNG"
	@echo "  make render-res-stacked         # res example -> stacked PNG"
	@echo "  make render-cap-all             # cap example -> layer PNGs + stacked PNG + HTML"
	@echo "  make render-res-all             # res example -> layer PNGs + stacked PNG + HTML"
	@echo ""
	@echo "Optional variables:"
	@echo "  LAYERS=2"
	@echo "  STAGE=all"
	@echo "  ASCII_MODE=detailed"
	@echo "  PNG_OUT=out"
	@echo "  HTML_OUT=out/gallery.html"
	@echo "  PREFIX=demo"

# --- Debug runs ---

.PHONY: cap
cap:
	$(PYTHON) -m $(DEBUG_MODULE) $(CAP_EXAMPLE) --stage all --layers $(LAYERS)

.PHONY: res
res:
	$(PYTHON) -m $(DEBUG_MODULE) $(RES_EXAMPLE) --stage all --layers $(LAYERS)

.PHONY: grid
grid:
	$(PYTHON) -m $(DEBUG_MODULE) $(CAP_EXAMPLE) --stage grid --layers $(LAYERS)

.PHONY: skeleton
skeleton:
	$(PYTHON) -m $(DEBUG_MODULE) $(CAP_EXAMPLE) --stage skeleton --layers $(LAYERS)

.PHONY: layout
layout:
	$(PYTHON) -m $(DEBUG_MODULE) $(CAP_EXAMPLE) --stage layout --layers $(LAYERS)

.PHONY: run
run:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run FILE=path/to/file.json [STAGE=...] [LAYERS=...]"; \
		exit 1; \
	fi
	$(PYTHON) -m $(DEBUG_MODULE) $(FILE) --stage $(STAGE) --layers $(LAYERS)

.PHONY: dump
dump:
	$(PYTHON) -m $(DEBUG_MODULE) $(CAP_EXAMPLE) --stage all --layers $(LAYERS) > debug.txt
	@echo "Wrote debug.txt"

.PHONY: dump-res
dump-res:
	$(PYTHON) -m $(DEBUG_MODULE) $(RES_EXAMPLE) --stage all --layers $(LAYERS) > debug_res.txt
	@echo "Wrote debug_res.txt"

.PHONY: diff
diff:
	@if [ ! -f debug_old.txt ] || [ ! -f debug.txt ]; then \
		echo "Need debug_old.txt and debug.txt"; \
		exit 1; \
	fi
	diff debug_old.txt debug.txt || true

# --- Render helpers ---

.PHONY: prepare-out
prepare-out:
	@mkdir -p $(PNG_OUT)

# --- Render runs: layer PNGs ---

.PHONY: render-cap
render-cap: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(CAP_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX)

.PHONY: render-res
render-res: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(RES_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX)

# --- Render runs: HTML gallery ---

.PHONY: render-cap-html
render-cap-html: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(CAP_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX) \
		--html-out $(HTML_OUT)

.PHONY: render-res-html
render-res-html: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(RES_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX) \
		--html-out $(HTML_OUT)

# --- Render runs: stacked PNG ---

.PHONY: render-cap-stacked
render-cap-stacked: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(CAP_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-stacked-out $(PNG_OUT)/$(PREFIX)_stacked.png

.PHONY: render-res-stacked
render-res-stacked: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(RES_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-stacked-out $(PNG_OUT)/$(PREFIX)_stacked.png

# --- Render runs: all outputs ---

.PHONY: render-cap-all
render-cap-all: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(CAP_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX) \
		--png-stacked-out $(PNG_OUT)/$(PREFIX)_stacked.png \
		--html-out $(HTML_OUT)

.PHONY: render-res-all
render-res-all: prepare-out
	$(PYTHON) -m $(RENDER_MODULE) $(RES_EXAMPLE) \
		--ascii-mode $(ASCII_MODE) \
		--png-out $(PNG_OUT) \
		--prefix $(PREFIX) \
		--png-stacked-out $(PNG_OUT)/$(PREFIX)_stacked.png \
		--html-out $(HTML_OUT)