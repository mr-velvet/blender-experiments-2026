#!/bin/bash
# Run 4 matrices sequentially. Total: ~27 renders × ~50s = ~22min
cd "$(dirname "$0")/.."

echo "=== Matrix 1/4: WEAR ==="
cmd.exe //c "scripts\\run-blender.cmd --python scripts\\05_render_matrix.py -- matrices/wear.json wear" 2>&1 | tail -20

echo "=== Matrix 2/4: SCALE ==="
cmd.exe //c "scripts\\run-blender.cmd --python scripts\\05_render_matrix.py -- matrices/scale.json scale" 2>&1 | tail -20

echo "=== Matrix 3/4: CORRUGATION ==="
cmd.exe //c "scripts\\run-blender.cmd --python scripts\\05_render_matrix.py -- matrices/corrugation.json corrugation" 2>&1 | tail -20

echo "=== Matrix 4/4: SHAPES ==="
cmd.exe //c "scripts\\run-blender.cmd --python scripts\\05_render_matrix.py -- matrices/shapes.json shapes" 2>&1 | tail -20

echo "=== ALL MATRICES DONE ==="
