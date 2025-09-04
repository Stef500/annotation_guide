# Makefile for BRAT Annotation Guide Template
# XeLaTeX compilation with performance optimization

# Configuration
TEX_ENGINE = xelatex
MAIN_FILE = main.tex
OUTPUT_DIR = ../output
BIB_ENGINE = biber

# Compilation flags for XeLaTeX optimization
TEX_FLAGS = -interaction=nonstopmode -halt-on-error -output-directory=$(OUTPUT_DIR)
TEX_FLAGS_DRAFT = $(TEX_FLAGS) -draftmode

# Default target
.PHONY: all clean draft final watch help

all: final

# Draft compilation (faster, for development)
draft:
	@echo "Building draft version..."
	@mkdir -p $(OUTPUT_DIR)
	$(TEX_ENGINE) $(TEX_FLAGS_DRAFT) $(MAIN_FILE)
	@echo "Draft build complete."

# Final compilation (full processing)
final:
	@echo "Building final version..."
	@mkdir -p $(OUTPUT_DIR)
	$(TEX_ENGINE) $(TEX_FLAGS) $(MAIN_FILE)
	@if [ -f $(OUTPUT_DIR)/main.bcf ]; then \
		cd $(OUTPUT_DIR) && $(BIB_ENGINE) main; \
	fi
	$(TEX_ENGINE) $(TEX_FLAGS) $(MAIN_FILE)
	$(TEX_ENGINE) $(TEX_FLAGS) $(MAIN_FILE)
	@echo "Final build complete."

# Watch mode for development
watch:
	@echo "Starting watch mode..."
	@while inotifywait -e modify -r .; do \
		make draft; \
	done

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -f $(OUTPUT_DIR)/*.aux $(OUTPUT_DIR)/*.log $(OUTPUT_DIR)/*.out
	@rm -f $(OUTPUT_DIR)/*.toc $(OUTPUT_DIR)/*.lof $(OUTPUT_DIR)/*.lot
	@rm -f $(OUTPUT_DIR)/*.bbl $(OUTPUT_DIR)/*.blg $(OUTPUT_DIR)/*.bcf
	@rm -f $(OUTPUT_DIR)/*.run.xml $(OUTPUT_DIR)/*.synctex.gz
	@rm -f $(OUTPUT_DIR)/*.fls $(OUTPUT_DIR)/*.fdb_latexmk
	@echo "Clean complete."

# Deep clean (remove all output)
distclean: clean
	@rm -f $(OUTPUT_DIR)/*.pdf
	@echo "Deep clean complete."

# Performance test
benchmark:
	@echo "Running compilation benchmark..."
	@time make clean && time make final
	@echo "Benchmark complete."

# Help target
help:
	@echo "BRAT Annotation Guide Template - Build System"
	@echo "Available targets:"
	@echo "  all      - Build final version (default)"
	@echo "  draft    - Build draft version (faster)"
	@echo "  final    - Build final version (complete)"
	@echo "  watch    - Watch files and rebuild draft on changes"
	@echo "  clean    - Remove auxiliary files"
	@echo "  distclean- Remove all generated files"
	@echo "  benchmark- Run compilation performance test"
	@echo "  help     - Show this help message"