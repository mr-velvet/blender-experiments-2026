# blender-experiments-2026

Experimentos de automacao do Blender via Python headless e MCP.

## Documentacao
- **[LEARNINGS.md](./LEARNINGS.md)** — aprendizados tecnicos reutilizaveis. **LER PRIMEIRO antes de comecar novo experimento.**
- **[PROGRESS.md](./PROGRESS.md)** — estado atual da sessao + proximos passos.

## Setup
- Blender 5.1.2
- blender-mcp addon instalado (setup/addon.py)
- MCP server configurado no Claude Code (escopo user)

## Quickstart

```bash
# Gerar 1 combo
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python pipeline/bake_and_export.py -- \
  --shape cube --material "Cardboard Outer" \
  --src-blend "caminho/do/material.blend" \
  --out-glb out/glb/teste.glb \
  --out-render out/renders/teste.png \
  --tex-dir out/baked_textures \
  --combo-id teste

# Gerar batch inteiro
python pipeline/batch_run.py

# Ver no browser
python -m http.server 8765
# abrir http://localhost:8765/viewer/index.html
```

## Estrutura
```
pipeline/    # scripts de bake e batch
viewer/      # pagina HTML com model-viewer pra inspecionar GLBs
setup/       # addon do MCP
out/         # outputs (gitignored)
```
