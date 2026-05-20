# Progresso — blender-experiments-2026

## Ultima atualizacao
2026-05-20

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

### Experimento 3: Clay 4.Doh (DoubleGum) — pack premium 23 materiais
- Pasta `claydoh/` — pipeline reaproveitado do experimento 2 (bake_and_export.py funciona sem mudancas)
- `claydoh/inspect.py` — inventario do .blend (gera blend_inventory.json)
- `claydoh/batch_claydoh.py` — selecao curada de 8 materiais (Clay Doh, Bubble Gum, Porcelain, Crackle, Glitter, Plasticine, Pottery, Terracotta)
- 32 combos (4 formas: sphere/cylinder/torus/suzanne x 8 materiais) — **cubo dropado** (smart_project distorce procedural com Object Mapping)
- 32/32 OK no batch, todos GLBs validos (1.3-3.4MB cada)
- `claydoh/index.html` — pagina demo com tema clay (beige/terracotta), filtros por material/forma
- **Hospedado:** https://st.did.lu/blender-claydoh/v1/index.html
- **Doc do pack:** shader 100% procedural (sem displacement de geometria, so surface) — bake regular basta

### Experimento 3.5: viewer v2 com modal de detalhe
- `claydoh/index.html` + `viewer/index_v2.html` ganharam modal fullscreen ao clicar num card
- Deep-link via URL hash (#combo_id) — pode compartilhar link direto
- Cardboard tambem hospedado pela 1a vez (estava so local) em blender-cardboard/v1/
- **Hospedado v2:**
  - https://st.did.lu/blender-claydoh/v2/index.html
  - https://st.did.lu/blender-cardboard/v2/index.html

### Experimento 5: extrator de pack monolitico (Everything Library, gratuito)
- Pasta `extract/` — script generico que abre um .blend com N assets agrupados em hierarquia `ROOT > Categoria > Asset > Meshes` e exporta cada asset como GLB separado
- `extract/extract_assets.py` — driver headless: 1 processo Blender, N GLBs
- `extract/inspect_pack.py`, `inspect_hierarchy.py`, `debug_*.py` — utilitarios de inventario
- Resultado: 263 GLBs (~39 MB) em `D:/GLOBAL-ASSETS/EVERYTHING-LIBRARY/` (fora do repo)
  - BUILDINGS: 85 assets em 7 categorias (Business, Farm, Historical, Industrial, Residential, Ruins, Tents)
  - ANIMALS: 178 assets em 10 categorias (Amphibians, AnimalParts, Animals, Arachnids, Birds, BirdsUpright, FlyingInsects, Imaginary, Insects, Reptiles)
- Cada GLB: centralizado em XZ, apoiado em Y=0, vertex colors preservadas, sem animacao/skin/morph
- **Tres bugs descobertos e consertados:**
  1. **Scene Collection duplicada** — pack original linka todos objetos NA Scene Collection raiz E nas sub-collections (Animals/Buildings). Quando exporto com selecao do asset, o glTF exporter expande os usuarios duplicados gerando 16 nodes pra um asset de 4. Fix: unlink da Scene raiz mantendo so nas sub-collections.
  2. **layer_collection.hide_viewport=True** — collection `Animals` veio com olhinho desligado no outliner; isso faz `object.visible_get()` retornar False e o exporter pula tudo. Fix: walk recursivo desligando hide_viewport/exclude em todas layer_collections.
  3. **bbox centering** — assets vinham com vertices em coordenadas absolutas (escala 1000+ unidades). Fix: calcular bbox global dos meshes, mover todos descendentes (matrix_world) pra origem antes do export, reverter depois.
- Pattern aplicavel a qualquer pack monolitico (assets agrupados em hierarquia Empty>Empty>Mesh)

### Experimento 4: deformacao real + VDM faces stamping
- Pasta `faces/` — 3 sub-experimentos combinados
- **4a (massinha amassada):** `faces/squash_and_export.py` — adiciona Subsurf + Displace(noise/clouds) ANTES do export. GLB tem geometria deformada real (silhouette muda ao rotacionar), nao so normal map.
- **4b (VDM stamp algoritmico):** `faces/vdm_stamp.py` — implementacao manual de VDM brush stamping SEM `bpy.ops.sculpt.brush_stroke`:
  - Snapshot do centro/normal/tangentes/area de cada face ANTES da subdivisao
  - Subdivide mesh densamente (subsurf 4-5, com edge crease preservado pra primitivos quadrangulares: cube/cylinder)
  - Pra cada anchor, pra cada vertex no disco: sample bilinear do EXR, converte RGB -> deslocamento tangent-space (R=u, G=v, B=n), aplica com falloff radial (suave so na borda 0.85-1.0)
  - Pack usado: Human Face VDM Brushes (DoubleGum), 30 EXRs 512x512 float Linear Rec.709
  - **Funciona perfeitamente em formas com poucas faces grandes (cube, cylinder, icosphere subdiv=1)**. Formas organicas (suzanne, sphere com muitos segments) viram "vírus com espinhos" — 1 face minuscula por triangulo
- **4c (combinado):** batch 3 formas (cube/icosphere/cylinder) x 3 EXRs (Map_1/5/10) x 4 cores Clay Doh = 9 combos OK
- `faces/index.html` — pagina demo com modal, mostra EXR usado em cada card
- **Hospedado:** https://st.did.lu/blender-claydoh-faces/v1/index.html

### Learnings tecnicos
- VDM em Blender: RGB centrado em 0 (nao 0.5), valores ate ~0.8. R=tangent u, G=bitangent v, B=normal.
- Edge crease em Blender 5.1: atribuir via bmesh layer "crease_edge" (a API `e.crease` nao funciona mais)
- Pra preservar quinas do cubo em Subsurf alto: marcar TODAS as edges com crease=1 via bmesh ANTES de aplicar Subsurf modifier
- Operadores `bpy.ops.sculpt.*` evitados — algoritmo de stamping manual em mathutils.Vector eh muito mais robusto e determinístico

### Repo
- GitHub: https://github.com/mr-velvet/blender-experiments-2026
- Branch: master
- Ultimos commits: feat(claydoh) → feat(viewer v2 modal) → feat(faces VDM + squash)

## Estrutura atual
```
blender-experiments-2026/
├── LEARNINGS.md            # conhecimento tecnico reutilizavel (LER PRIMEIRO)
├── PROGRESS.md             # este arquivo
├── README.md
├── demo_cardboard_cube.py  # primeira demo (gera GLB quebrado — referencia)
├── pipeline/               # cardboard (experimento 2)
│   ├── bake_and_export.py  # core: 1 combo (forma x material) -> GLB
│   ├── batch_run.py        # batch: matriz NxM
│   └── fix_manifest.py
├── viewer/                 # cardboard viewer
│   ├── index.html          # v1 (sem modal)
│   ├── index_v2.html       # v2 com modal de detalhe
│   └── gen_manifest_v2.py  # gera manifest com URLs GCS absolutas
├── claydoh/                # experimento 3 (Clay 4.Doh)
│   ├── inspect.py
│   ├── batch_claydoh.py
│   ├── index.html          # com modal (v2 ja embutido)
│   └── gen_manifest_v2.py
├── faces/                  # experimento 4 (VDM stamp + Clay Doh)
│   ├── inspect_vdm.py
│   ├── squash_and_export.py  # 4a: subsurf + displace pre-export
│   ├── vdm_stamp.py          # 4b: stamping algoritmico de VDM
│   ├── batch_vdm.py          # 4c: batch combinado
│   └── index.html            # demo com modal + meta de EXR
├── setup/addon.py
└── out/, claydoh/out/, faces/out/   # gitignored: glb/, renders/, baked_textures/
```

## Hospedado em GCS (st.did.lu)
| Experimento | URL |
|---|---|
| Cardboard v2 (modal) | https://st.did.lu/blender-cardboard/v2/index.html |
| Clay Doh v1 | https://st.did.lu/blender-claydoh/v1/index.html |
| Clay Doh v2 (modal) | https://st.did.lu/blender-claydoh/v2/index.html |
| Faces + Clay Doh v1 | https://st.did.lu/blender-claydoh-faces/v1/index.html |

## O que NAO foi feito (proximos passos)

### Curto prazo
- Pasta `faces/` ainda nao tem v2 com modal hospedado (modal ja existe na pagina, so subir como v2)
- Resolver "virus com espinhos" pra meshes organicas (suzanne/sphere): decimar anchors por area minima, ou agrupar faces adjacentes em "patches" antes de estampar
- Combinar 4a (massinha amassada) com 3 (Clay Doh batch) — variante "deformado" do batch existente
- Comparar `Principled BSDF puro pre-existente` vs `bake` — pular bake quando possivel

### Medio prazo
- HDR environment proprio pra renders (em vez do sun simples)
- Bake de AO + thickness pra dar mais profundidade nos GLBs
- Testar o node `glTF Material Output` (alternativa ao bake)
- Pipeline pra materiais de pack PBR padrao (basecolor.jpg + roughness.jpg + normal.jpg) — caminho diferente, sem bake
- VDM stamping em "patches" de mesh organica (suzanne): identificar regioes planas grandes (bochecha, testa) e estampar so la

### Longo prazo / ideias
- Modo MCP interativo: testar trabalhar ao vivo na cena com Blender aberto
- Bake de modelos complexos (nao so primitivos) — Suzanne ja foi, mas modelo real comprado
- Pipeline reversa: dado um GLB, abrir no Blender e modificar
- Animacao simples (rotacao, scale, morph targets) preservada no GLB
- Aplicar pack VDM diferente (creature, abstract, etc) — vdm_stamp.py eh agnostico ao conteudo do EXR

## Servidor local
Viewer em http://localhost:8765/{viewer,claydoh,faces}/index.html (rodar `python -m http.server 8765` na raiz se cair)
