# Progresso — blender-experiments-2026

## Ultima atualizacao
2026-05-19

## O que ja foi feito

### Setup (2026-05-19)
- Blender 5.1.2 funcional, addon `blender-mcp` instalado e habilitado
- MCP server adicionado ao Claude Code (escopo user) — funciona em foreground
- Modo headless via Python validado (preferido pra batch)

### Experimento 1: cubo cardboard simples
- `demo_cardboard_cube.py` — cubo + material "Cardboard Outer" do pack Superhive, render Cycles + GLB
- **Resultado:** render no Blender OK, GLB exportado **falhou silenciosamente** (saiu branco translucido)
- **Causa identificada:** exportador glTF descarta node trees procedurais — material era node group customizado

### Experimento 2: pipeline PBR baking
- `pipeline/bake_and_export.py` — bake automatico de baseColor + roughness + normal, reconstroi Principled BSDF, exporta GLB
- `pipeline/batch_run.py` — matriz forma x material, 1 combo por processo
- 20 combos gerados (5 formas: cube/sphere/cylinder/torus/suzanne x 4 materiais: Cardboard Outer/Inner/Mat1/Mat2)
- `viewer/index.html` — pagina com `<model-viewer>` lado-a-lado com render Cycles
- **Resultado:** materiais Cardboard Outer/Inner funcionam perfeito no GLB. Mat1/Mat2 saem cinza (sao materiais pra texto)
- **Verificado visualmente** via screenshot do viewer (playwright)

### Repo
- GitHub: https://github.com/mr-velvet/blender-experiments-2026
- Branch: master
- Commits: init + feat (pipeline) + chore (gitignore)

## Estrutura atual
```
blender-experiments-2026/
├── LEARNINGS.md            # conhecimento tecnico reutilizavel (LER PRIMEIRO)
├── PROGRESS.md             # este arquivo
├── README.md
├── demo_cardboard_cube.py  # primeira demo (gera GLB quebrado — referencia)
├── pipeline/
│   ├── bake_and_export.py  # core: 1 combo (forma x material) -> GLB
│   ├── batch_run.py        # batch: matriz NxM
│   └── fix_manifest.py     # utility: caminhos relativos
├── setup/addon.py          # blender-mcp addon (ja instalado no Blender)
├── viewer/index.html       # grid Cycles vs GLB, controles de env/exposure
└── out/                    # gitignored: glb/, renders/, baked_textures/, manifest.json
```

## O que NAO foi feito (proximos passos)

### Curto prazo (proxima sessao)
- Testar com outros materiais comprados (que voce ja tem)
- Validar pipeline com materiais que tem displacement (so bake basico nao pega)
- Comparar `Principled BSDF puro pre-existente` vs `bake` — se material ja for BSDF nativo, pular bake e exportar direto

### Medio prazo
- HDR environment proprio pra renders (em vez do sun simples)
- Bake de AO + thickness pra dar mais profundidade nos GLBs
- Testar o node `glTF Material Output` (alternativa ao bake)
- Pipeline pra materiais de pack PBR padrao (basecolor.jpg + roughness.jpg + normal.jpg) — caminho diferente, sem bake

### Longo prazo / ideias
- Modo MCP interativo: testar trabalhar ao vivo na cena com Blender aberto
- Bake de modelos complexos (nao so primitivos) — Suzanne ja foi, mas modelo real comprado
- Pipeline reversa: dado um GLB, abrir no Blender e modificar
- Animacao simples (rotacao, scale, morph targets) preservada no GLB

## Servidor local
Viewer em http://localhost:8765/viewer/index.html (rodar `python -m http.server 8765` na raiz se cair)
