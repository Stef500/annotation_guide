#!/bin/bash

# Build script for LaTeX annotation guide
# Compiles the LaTeX template to PDF using XeLaTeX

set -e

# Get build type from environment or default to draft
BUILD_TYPE="${1:-${BUILD_TYPE:-draft}}"

echo "Building BRAT Annotation Guide (mode: $BUILD_TYPE)..."

# Create output directory if it doesn't exist
mkdir -p output

# Set compilation options based on build type
case "$BUILD_TYPE" in
    "final")
        echo "Building in FINAL mode with full processing..."
        # Full compilation with bibliography
        xelatex -output-directory=output templates/main.tex
        if [ -f output/main.aux ]; then
            biber output/main
            xelatex -output-directory=output templates/main.tex
            xelatex -output-directory=output templates/main.tex
        fi
        ;;
    "draft"|*)
        echo "Building in DRAFT mode for faster compilation..."
        # Draft mode - single pass, faster compilation
        xelatex -output-directory=output -interaction=nonstopmode templates/main.tex
        ;;
esac

# Check if PDF was generated successfully
if [ -f "output/main.pdf" ]; then
    echo "Build complete. PDF available in output/main.pdf"
    ls -la output/main.pdf
else
    echo "ERROR: PDF generation failed!"
    exit 1
fi