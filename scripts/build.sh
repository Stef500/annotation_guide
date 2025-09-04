#!/bin/bash

# Build script for LaTeX annotation guide
# Compiles the LaTeX template to PDF using Tectonic

set -e

# Get build type from environment or default to draft
BUILD_TYPE="${1:-${BUILD_TYPE:-draft}}"

echo "🚀 Building BRAT Annotation Guide with Tectonic (mode: $BUILD_TYPE)..."

# Create output directory if it doesn't exist
mkdir -p output

# Performance: Clear aux files for clean build
if [ "$BUILD_TYPE" = "final" ]; then
    echo "🧹 Cleaning auxiliary files for final build..."
    rm -f output/*.aux output/*.toc output/*.bbl output/*.blg output/*.log
fi

# Set compilation options based on build type
case "$BUILD_TYPE" in
    "final")
        echo "Building in FINAL mode with full processing..."
        # Tectonic handles everything automatically - bibliography, multiple passes, etc.
        tectonic --outdir=output templates/main.tex
        ;;
    "draft"|*)
        echo "Building in DRAFT mode..."
        # Draft mode - Tectonic is already optimized, but we can use --chatter=minimal
        tectonic --outdir=output --chatter=minimal templates/main.tex
        ;;
esac

# Check if PDF was generated successfully
if [ -f "output/main.pdf" ]; then
    echo "✅ Build complete. PDF available in output/main.pdf"
    ls -la output/main.pdf
    
    # Show Tectonic statistics
    echo "📊 Build statistics:"
    echo "  Engine: Tectonic (XeTeX-based)"
    echo "  Mode: $BUILD_TYPE"
    echo "  Output: $(ls -lh output/main.pdf | awk '{print $5}')"
else
    echo "❌ ERROR: PDF generation failed!"
    echo "Check the logs above for details."
    exit 1
fi