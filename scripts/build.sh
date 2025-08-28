#!/bin/bash

# Build script for LaTeX annotation guide
# Compiles the LaTeX template to PDF using XeLaTeX

set -e

echo "Building BRAT Annotation Guide..."

# Create output directory if it doesn't exist
mkdir -p output

# Compile LaTeX to PDF
xelatex -output-directory=output templates/main.tex

echo "Build complete. PDF available in output/main.pdf"