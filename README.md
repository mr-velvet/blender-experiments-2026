# blender-experiments-2026

Experimentos de automacao do Blender via Python headless e MCP.

## Documentacao
- **[LEARNINGS.md](./LEARNINGS.md)** — aprendizados tecnicos reutilizaveis. **LER PRIMEIRO antes de comecar novo experimento.**
- **[PROGRESS.md](./PROGRESS.md)** — estado atual da sessao + proximos passos.

## Demos hospedados
- **Cardboard:** https://st.did.lu/blender-cardboard/v2/index.html
- **Clay Doh:** https://st.did.lu/blender-claydoh/v2/index.html
- **Clay Doh + VDM Faces:** https://st.did.lu/blender-claydoh-faces/v1/index.html
- **Infinite (estruturas + FPS demo):** https://st.did.lu/blender-infinite/v1/index.html
- **Scanned (instancing stress test):** https://st.did.lu/blender-scanned/v1/index.html
- **Shatter v2 (cubo quebrando + player + materiais):** https://st.did.lu/blender-shatter/v2/index.html
- **Rigging (walk cycle procedural):** https://st.did.lu/blender-rigging/v1/index.html
- **Fluid (Mantaflow + player):** https://st.did.lu/blender-fluid/v1/index.html ← [docs detalhada](./fluid/README.md)
- **Grass (esqueleto dinamico + wind influenciavel):** https://st.did.lu/blender-grass/v1/index.html ← [docs detalhada](./grass/README.md)

## Relatorios tecnicos
- **Geometry addons v2 (90+ plugins, recalibrado):** https://st.did.lu/reports/blender-geometry-addons/v2/index.html
- **Cardboard addons (3 plugins comparados):** https://st.did.lu/reports/cardboard-addons/v1/index.html

## Setup
- Blender 5.1.2 (Blender 4.4 tambem instalado pra compatibilidade)
- blender-mcp addon instalado (setup/addon.py)
- MCP server configurado no Claude Code (escopo user)

## Quickstart

```bash
# 1. Bake basico (1 combo: forma + material -> GLB)
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python pipeline/bake_and_export.py -- \
  --shape sphere --material "Clay Doh" \
  --src-blend "C:\Users\manu\Downloads\BLENDER-CLAY\...Clay Doh 4.0.4.blend" \
  --out-glb out/glb/teste.glb --out-render out/renders/teste.png \
  --tex-dir out/baked_textures --combo-id teste

# 2. Batch inteiros (por experimento)
python pipeline/batch_run.py            # cardboard
python claydoh/batch_claydoh.py         # Clay Doh (32 combos)
python faces/batch_vdm.py               # VDM faces stamped + Clay Doh (9 combos)

# 3. Massinha amassada (deformacao real, nao so normal map)
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python faces/squash_and_export.py -- \
  --shape sphere --material "Clay Doh" --src-blend "..." \
  --out-glb out/teste_amassado.glb --tex-dir out/baked --combo-id teste \
  --subdiv-levels 4 --displace-strength 0.25 --noise-scale 2.0

# 4. VDM brush stamping (1 face humana no centro de cada face da mesh)
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --background --python faces/vdm_stamp.py -- \
  --shape cube --exr "C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Texture\Map_ (5).exr" \
  --material "Clay Doh" --src-blend "..." \
  --out-glb out/teste_faces.glb --tex-dir out/baked --combo-id teste \
  --subdiv-levels 5 --stamp-scale 0.7 --displace-strength 0.35

# Ver localmente
python -m http.server 8765
# http://localhost:8765/{viewer,claydoh,faces}/index.html
```

## Estrutura
```
pipeline/    # cardboard: bake + batch + viewer
claydoh/     # Clay 4.Doh (DoubleGum) - 32 combos
faces/       # VDM Face brushes + deformacao real + Clay Doh
viewer/      # cardboard viewer (v1 + v2 com modal)
setup/       # blender-mcp addon
```

Cada pasta de experimento tem `out/` gitignored com glb/renders/textures.
