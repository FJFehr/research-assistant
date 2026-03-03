#!/usr/bin/env bash
set -euo pipefail

name="${1:?Usage: ./run.sh <paper-name>}"

echo "=== Step 1: extracting annotations from annotated papers/${name}.pdf ==="
uv run extract "annotated papers/${name}.pdf"

echo ""
echo "=== Step 2: summarising extracted/${name}.txt ==="
uv run summarise "extracted/${name}.txt"
