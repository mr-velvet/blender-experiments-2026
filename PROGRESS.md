# Progresso — blender-experiments-2026

## Ultima atualizacao
2026-05-20 (sessao 4 — experimento 8: shatter cubo Clay Doh + player tipo YouTube)

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

### Experimento 6: estruturas infinitas com instancing + demo Three.js navegavel
- Pasta `infinite/` — 4 cenas 3D com formas geometricas simples + escadas, navegaveis em browser
- **6a (stair_lib.py):** biblioteca de 6 escadas via bmesh + addon
  - `stair_straight`, `stair_spiral`, `stair_L`, `stair_suspended`, `step_pyramid` (zigurat) — bmesh puro
  - `stair_archimesh` — usa addon `archimesh` (extension Blender 5.x)
- **6b (build_structures.py):** 4 estruturas infinitas via instancing massivo
  - **Escher**: grid 4x4x4 plataformas em 4 camadas com twist por camada, 5 tipos de escada alternando direcao — 112 objs / 55KB GLB
  - **Torre**: 14 niveis x 8 plataformas hexagonais petalas + pillars + escadas helicoidais centrais torcidas — 340 objs / 57KB GLB
  - **Zigurat**: grid 4x4 step pyramids conectados por pontes + escadas em cada lateral — 57 objs / 18KB GLB
  - **Mix**: 8 zigurats em torno + torre helicoidal central + camada de plataformas suspensas no topo — 52 objs / 41KB GLB
- **6c (index.html):** demo Three.js completa
  - Switch entre 4 cenas sem reload (GLTFLoader troca scene root)
  - 2 modos com toggle: **FPS** (PointerLockControls + WASD + gravidade + pulo + raycast pra detectar chao em escadas) e **Free-fly** (mouse drag + WASD + Q/E up/down)
  - HUD com pills, contador fps, hints contextuais por modo
  - Lock prompt animado pra entrada no FPS mode
- **Addons Blender 5.x instalados** (extension system novo): `archimesh`, `modern_primitive`, `maze_generator`, `sapling_tree_gen` via `bpy.ops.extensions.package_install` headless
- **Hospedado:** https://st.did.lu/blender-infinite/v1/index.html
- **Insight tecnico chave:** instancing nativo via `bpy.data.objects.new(name, shared_mesh_data)` (todos os 340 objetos da torre compartilham 4 datas distintas) gera GLBs **dezenas de vezes menores** que duplicar geometria; glTF 2.0 lida com instancing nativamente, Three.js + GLTFLoader respeita

### Experimento 7: modelo escaneado (app 3D scanner) + stress test de instancing
- Pasta `scanned/` — analise de mesh + LODs + demo Three.js navegavel com instancing massivo
- **Input:** GLB do scanner (objeto organico ~16cm, 11506 tris, 13262 verts, 1 material PBR com textura JPEG 2048x2048, 1.2MB total)
- **Analise:** mesh **leve** (11.5k tris eh metade do padrao AAA). Peso real esta na textura (2K JPEG = 16MB descomprimido na VRAM)
- **LOD pipeline (`scripts/make_lods.py`):** decimate modifier do Blender + downscale de textura
  - lod0: 11506 tris, 1.2MB (original)
  - lod1: 5752 tris, 1.1MB (decimate 0.5)
  - lod2: 3837 tris, 1.0MB (decimate 0.25 — trava aqui, topologia minima)
  - lod_tex512: 5752 tris, 437KB (tex downscaled)
  - lod_tiny: 3837 tris, 305KB
- **Demo (`scanned/index.html`):** Three.js + InstancedMesh + PointerLockControls
  - 5 LODs selecionaveis em runtime, 4 layouts (grid/ring/forest/tower)
  - Slider de 1 a 20000 instancias
  - Toggle Instancing ON/OFF (InstancedMesh vs Mesh por copia)
  - HUD com FPS, frame ms, draw calls, tris renderizados, contagem de texturas (renderer.info)
  - 2 modos navegacao: FPS (PointerLock + WASD + gravidade) e Fly (mouse drag + WASD + Q/E)
- **Benchmark com instancing ON (LOD1):**
  - 500 instancias: 2.9M tris, 3 draw calls, 60 fps
  - 1000 instancias: 5.7M tris, 3 draw calls, 60 fps
  - 5000 instancias: 28.8M tris, 3 draw calls, 30 fps
  - 10000 instancias: 57.5M tris, 3 draw calls, 22 fps
  - 20000 instancias: 115M tris, 3 draw calls, 25 fps (frustum culling no GPU)
- **Insight:** com instancing ativo, GPU fica fill-rate bound (overdraw das pedras grandes) e nao mais draw-call bound. Sem instancing, 5000 copias = 1500+ draw calls mas ainda 60 fps porque o browser frustum culla agressivo.
- **Hospedado:** https://st.did.lu/blender-scanned/v1/index.html

### Experimento 8: cubo Clay Doh quebrando + player tipo YouTube (2026-05-20 sessao 4)
- Pasta `shatter/` — pipeline completa: simulacao rigid body no Blender, bake em keyframes, GLB animado, player HTML/JS com controles tipo YouTube
- **Setup multi-agente:** Observer (general-purpose) em paralelo dando feedback tecnico antecipado; Implementer (main) executando
- **Cell Fracture em Blender 5.1:** nao vem mais built-in, virou extension `bl_ext.blender_org.cell_fracture`. Instalavel headless via `bpy.ops.extensions.package_install(repo_index=0, pkg_id="cell_fracture", enable_on_install=True)`. **Bug critico em headless:** apos enable, o op `bpy.ops.object.add_fracture_cell_objects` nao registra no RNA mesmo com `addon_utils.check()` retornando `(True, True)`. **Workaround:** importar o modulo (`import bl_ext.blender_org.cell_fracture as cf`) e chamar `cf.main(bpy.context, **kwargs)` direto — pula o sistema de RNA.
- **Cell Fracture com source=VERT_OWN:** clamp em `min(source_limit, len(verts))`. Cubo crudo tem 8 verts → max 8 shards. **Solucao:** subdivide o cubo com `bpy.ops.mesh.subdivide(number_cuts=5)` antes — 386 verts → ~46 shards efetivos (algumas celulas Voronoi caem fora).
- **Pipeline rigid body → keyframes em headless:**
  1. `bpy.ops.rigidbody.world_add()`, configurar substeps=20, frame_end no point_cache
  2. Pra cada shard: `bpy.ops.rigidbody.object_add()`, type='ACTIVE', collision_shape='CONVEX_HULL'
  3. Trigger dramatico: shards iniciam com `rigid_body.kinematic=True`, keyframe em frame 1 e frame 15, depois `kinematic=False` keyframe em frame 16 — cubo "espera" antes de cair
  4. `bpy.ops.ptcache.bake_all(bake=True)` com `temp_override(point_cache=scene.rigidbody_world.point_cache)` — caso contrario falha silencioso em headless
  5. `bpy.ops.nla.bake(visual_keying=True, step=1, bake_types={'OBJECT'})` — gera Action por shard com 120 keyframes TRS
  6. `bpy.ops.rigidbody.objects_remove()` + `rigidbody.world_remove()` — limpar antes do export pra glTF nao misturar sim live com keys
- **Export GLB:** `export_animations=True, export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=False` — sampling forcado eh ESSENCIAL pra scrubbing (sem isso vira Bezier que trava)
- **Material:** Clay Doh procedural com Object Coord → GLB de 35MB (exporter embed texturas baked horrendas). Solucao: `apply_solid_clay` Principled BSDF puro com base color rosa-coral `(0.85, 0.45, 0.40)` + sheen 0.4 — GLB final 360KB com 46 shards animados.
- **Player HTML/JS (`shatter/index.html`):**
  - Three.js + GLTFLoader + AnimationMixer + OrbitControls + RoomEnvironment (PBR builtin sem HDR)
  - Timeline scrubbable: range slider custom, click pra seek, hover tooltip com frame+tempo, knob com hover scale
  - Controles: play/pause (Space), frame ±1 (←/→), ±10 (Shift+arrows), Home/End, L (loop toggle), 0-9 (jump %), speed buttons (0.25/0.5/1/2x)
  - Pattern critico de scrubbing: `action.paused=true; action.time=t; mixer.update(0)` — setar `timeScale=0` quebra
  - Scrubbing durante play: pausa no mousedown, retoma no mouseup
  - HUD com timer MM:SS.cc + frame counter (X / 120)
  - Tema visual: bg dark (#1a1816), accent coral (#f4a380), tipografia clean — combina com look clay
- **Hospedado:** https://st.did.lu/blender-shatter/v1/index.html
- **Tamanho final:** GLB 360KB + HTML 13KB. Carrega instantaneo.

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
├── infinite/                 # experimento 6 (estruturas infinitas + Three.js)
│   ├── index.html            # demo Three.js (FPS + free-fly)
│   ├── scripts/
│   │   ├── stair_lib.py      # biblioteca de 6 escadas
│   │   ├── build_structures.py # gera 4 cenas + exporta GLB
│   │   ├── preview_renders.py # renders de checagem (Eevee)
│   │   ├── inspect_addons.py
│   │   └── install_picks.py  # instala addons via extensions repo
│   └── out/glb/              # GLBs + .blend de cada cena
├── extract/                  # experimento 5 (extrator de pack monolitico)
├── setup/addon.py
└── out/, claydoh/out/, faces/out/, infinite/out/   # gitignored: glb/, renders/, baked_textures/
```

## Hospedado em GCS (st.did.lu)
| Experimento | URL |
|---|---|
| Cardboard v2 (modal) | https://st.did.lu/blender-cardboard/v2/index.html |
| Clay Doh v1 | https://st.did.lu/blender-claydoh/v1/index.html |
| Clay Doh v2 (modal) | https://st.did.lu/blender-claydoh/v2/index.html |
| Faces + Clay Doh v1 | https://st.did.lu/blender-claydoh-faces/v1/index.html |
| Infinite v1 (FPS demo navegavel) | https://st.did.lu/blender-infinite/v1/index.html |
| Scanned v1 (instancing stress test) | https://st.did.lu/blender-scanned/v1/index.html |
| Shatter v1 (cubo quebrando + player tipo YouTube) | https://st.did.lu/blender-shatter/v1/index.html |

## O que NAO foi feito (proximos passos)

### Curto prazo
- **Infinite v2**: aplicar materiais Clay Doh nos GLBs (re-usar pipeline do experimento 3 — bake + GLB pra cada subobjeto)
- **Infinite — Wave Function Collapse**: usar `wfc_3d_generator` addon pra estruturas realmente nao-periodicas
- **Infinite — sapling_tree_gen**: scatterar arvores procedurais pelas plataformas (variacao organica num cenario geometrico)
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
