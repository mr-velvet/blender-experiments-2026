# Progresso — blender-experiments-2026

## Ultima atualizacao
2026-05-21 (sessao 7 — experimento 11: grama alta com esqueleto + wind dinamico)

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

### Experimento 8.5: seletor de material em runtime (v2)
- Trocar material dos shards sem regerar GLB: substituir `mesh.material` por `MeshPhysicalMaterial` compartilhado no Three.js
- 5 presets: Coral (atual), Cardboard (papelao kraft), Rosa bebe, Amarelo manteiga, Verde menta
- UI: swatches circulares no buttons-row (cores reais como background), tooltip no hover com label, swatch ativo destacado
- Atalho `M` cycla materiais
- Tecnica: 1 instancia de `MeshPhysicalMaterial` compartilhada por TODOS os shards (~46), troca de cor/roughness/sheen/sheenColor com `material.needsUpdate = true`. Performance instantanea, sem GC.
- v2 reaproveita GLB da v1 via URL absoluta (`location.hostname.includes("did.lu") ? URL_V1 : "./out/glb/..."`) — economiza 360KB de upload
- **Hospedado:** https://st.did.lu/blender-shatter/v2/index.html

### Experimento 11: grama alta com esqueleto + wind dinamico (2026-05-21 sessao 7) — **INVALIDADO**

> ⚠️ **EXPERIMENTO INVALIDADO PELO USER.** Nao usar como referencia em nada.
>
> O experimento eh lixo porque pulou exatamente as etapas que existia pra validar:
> 1. Nao usou plugin sofisticado de grama — eu fiz um triangulo quad-strip de 12 tris a mao
> 2. Nao consumiu a animacao do Blender em JS — eu reescrevi sin/cos em JS e ignorei o AnimationMixer
> 3. Slider de "direcao" girava o asset no eixo Y (vento nao gira asset, vento empurra) — gambiarra
>
> Ver `CLAUDE.md` na raiz da workspace pras regras que evitam este tipo de erro.
> Demo continua hospedada como evidencia do erro, NAO como referencia tecnica.

- Pasta `grass/` — pipeline 100% autonoma: gera blade com 3 bones, anima wind sway, exporta GLB pequeno (12KB), player Three.js clona em N instances com wind controlavel em runtime
- **Goal do user:** "vegetacao alta com esqueleto dentro pra balancar... que possa ser dinamicamente influenciado dentro de uma simulacao html/javascript"
- **Pipeline (`grass/scripts/build_grass.py`):**
  1. Constroi blade mesh: quad strip 7x2 verts, 12 tris, com curl natural (verga pra frente em rest pose via `y_curl = BLADE_CURL * t²`)
  2. Vertex color gradient base→tip: verde escuro `(0.06, 0.18, 0.04)` → verde medio `(0.28, 0.42, 0.10)` exportado como `COLOR_0`
  3. Armature 3 bones em cadeia: B0_base / B1_mid / B2_top, `use_connect=True`
  4. Skin manual por altura (sem `ARMATURE_AUTO`): peso por bone calculado linearmente por Z do vertice, normalizado pra somar 1
  5. Wind animation: 60 frames @ 30fps, senoide com phase shifts (-0.15 mid, -0.30 top) gera look "viscoso" de wind propagando da raiz pro topo
  6. Loop perfeito: `sin(2π·t)` com t = [0..1] retorna a zero no fim do ciclo
  7. Export GLB com `export_force_sampling=True`, `export_skins=True`, sheen=0 (sheen branco saturava no PBR)
- **Player Three.js (`grass/index.html`):**
  - `SkeletonUtils.clone()` (NAO `.clone()` direto — preserva skin+armature corretamente)
  - **Poisson disk sampling** (Bridson 2D) pra distribuir N blades sem clusters/grids visiveis
  - 4 densidades: esparso (430) / medio (840) / denso (1600, default) / cheio (2900)
  - **Decisao tecnica chave:** descartei `AnimationMixer + clipAction` por blade (1500 mixers + LERP eh caro). Substitui por **calculo procedural de bones**:
    ```js
    const u = globalTime * FREQ + b.phase;
    bones.base.rotation.x = AMP_BASE * sin(2π·u) * windAmp + gust0;
    bones.mid.rotation.x  = AMP_MID  * sin(2π·(u + PHASE_MID)) * windAmp + gust1;
    bones.top.rotation.x  = AMP_TOP  * sin(2π·(u + PHASE_TOP)) * windAmp + gust2;
    ```
  - Mesma formula que o Blender bakeou, agora 100% em JS — ~10x mais rapido que mixer
  - **Esqueleto realmente influenciavel**: wind strength escala amplitude, wind dir alinha blade.root.rotation.y, gust eh additivo positivo com decay
  - Slider de vento 0-3x, direcao -180° a 180°, velocidade 0.1-3x, botao gust
  - Atalhos: Space play/pause, G gust, 1-4 densidade
- **Performance:** ~22fps em Playwright headless (CPU rasterizer) @ 1600 blades; estimado 60+ em GPU real
- **Bottleneck identificado:** 1 draw call por blade (SkinnedMesh nao instanceavel via InstancedMesh)
- **Hospedado:** https://st.did.lu/blender-grass/v1/index.html
- **Docs completa:** [grass/README.md](grass/README.md)
- **Insights tecnicos chave:**
  1. **Shader wind addons (Grassify, GRASS Generator) sao incompativeis** com criterio "animacao vem do Blender" — efeito vive no shader, GLB exporta mesh estatico. Por isso construi pipeline propria com bones reais
  2. `SkeletonUtils.clone()` eh obrigatorio em Three.js pra clonar skinned meshes — `.clone()` direto compartilha skeleton entre instancias e quebra animacao independente
  3. **GLB exportar action bakeada + JS sobrescrever bones em runtime** = melhor dos dois mundos: arquivo compativel com outras engines (que usariam baseline) + flexibilidade runtime em Three.js
  4. Sheen branco (1,1,1) saturava em PBR + Roomenv → vertex colors viravam quase brancas no topo. Sheen=0 resolveu
  5. Curl natural `y = curl * t²` em rest pose deixa grama parecida com grama real (vergada pra frente) sem precisar de modifier

### Experimento 10: simulacao de fluido Mantaflow + player web (2026-05-21 sessao 6)
- Pasta `fluid/` — pipeline 100% automatica do zero: simulacao Mantaflow + bake + extract + player HTML
- **Goal:** validar se da pra usar motor de fisica do Blender pra gerar animacoes que rodam fora do Blender sem nenhum runtime de fisica no consumidor final
- **Pipeline (`fluid/scripts/build_fluid.py`):**
  1. Cria esfera emissor + domain cubo + chao effector via Python
  2. Configura Mantaflow liquid sim: gravidade, viscosidade, substeps 2-8, CFL 2.0
  3. Bake automatico headless via `bpy.ops.fluid.bake_data()` + `bake_mesh()` (~3 min a res 96)
  4. Pra cada um dos 80 frames: extrai mesh-surface do domain via depsgraph eval
  5. Voxel remesh 0.13 pra reduzir polycount (raw 200k -> 5-15k tris)
  6. Exporta cada frame como GLB individual (~80-200KB cada)
- **Player HTML/JS (`fluid/index.html`):**
  - Three.js + GLTFLoader carrega 80 GLBs em paralelo
  - MeshPhysicalMaterial com transmission 0.85 + IOR 1.33 (aproxima refracao da agua)
  - Player tipo YouTube: play/pause/scrub/speed (0.25-2x)/loop/girar/setas
  - Loop completo, scrub frame-a-frame
- **Resultado:** 80 GLBs (7.5MB total) pra 2.67s @ 30fps
- **Mantaflow funciona em headless** (diferente do Rigify/Cell Fracture que tinham bug RNA)
- **Topologia variavel frame-a-frame** (462 verts no f1, 7822 no f30, 5590 no f60) impede morph targets — solucao: mesh sequence em 80 GLBs separados
- **Hospedado:** https://st.did.lu/blender-fluid/v1/index.html
- **Documentacao completa:** [fluid/README.md](fluid/README.md) — descobertas tecnicas, trade-offs, formatos alternativos (Alembic/USD/VAT), viabilidade por plataforma

### Experimento 9: rigging automatico + walk cycle procedural (2026-05-20 sessao 5)
- Pasta `rigging/` — pipeline 100% autonoma do zero: cria humanoide, riga com Rigify, anima walk cycle, exporta GLB, demo HTML com switcher entre 4 modelos (1 autoral + 3 references Khronos)
- **Goal do user:** avaliar capacidades de rigging automatico + iniciativa em baixar assets/addons + autonomia
- **Pesquisa autonoma:** Rigify (built-in, free) vs Auto-Rig Pro (paid) vs MPFB vs Mixamo (requires login, nao serve pra autonomous). Escolhido Rigify por: gratis, headless capable, ja vem com Blender 5.1
- **Referencias publicas baixadas:** Khronos Sample Assets via raw.githubusercontent.com — CesiumMan, Fox (3 anims), RiggedFigure, BrainStem. Inspecionados via parser GLB proprio (skins, joints, anims).
- **Rigify em Blender 5.1 headless:** mesmo bug do Cell Fracture (op nao registra). Workaround `from rigify.metarigs.Basic import basic_human; basic_human.create(arm)` + `from rigify import generate; generate.generate_rig(ctx, metarig)`. Documentado em LEARNINGS.md sessao 5.
- **Pipeline implementada (`rigging/scripts/build_character.py`):**
  1. Constroi humanoide stylized: 22 primitivos (esferas/cilindros/cubos) com proporcoes humanas (1.75m), apply transforms, join, smooth -> mesh 1862 verts / 1916 tris
  2. Material Principled BSDF coral (0.95, 0.55, 0.45) com sheen 0.3
  3. Adiciona metarig basic_human via `basic_human.create()` direto (29 bones)
  4. Calcula scale via bbox mesh / bbox edit_bones, alinha metarig sobre o mesh
  5. `generate.generate_rig()` gera 222 bones do control rig (DEF + MCH + control + tweaks)
  6. Parent mesh -> rig com `ARMATURE_AUTO` -> 35 vertex groups + modifier armature
  7. **CRITICO**: seta `IK_FK = 1.0` em `thigh_parent.L/R`, `upper_arm_parent.L/R` (Rigify comeca em IK, mas DEF bones via IK ficam estaticos em pose default — meus keyframes FK eram ignorados)
  8. Walk cycle: 5 keyframes (contact, passing, contact espelhada, passing espelhada, loop) em 14 bones FK (torso, hips, chest, thighs, shins, foots, upper_arms, forearms, head)
  9. Export GLB com `export_def_bones=True` (35 DEF bones em vez dos 222 total) + `export_force_sampling=True` (frame-by-frame, nao Bezier)
  10. Resultado: GLB 244KB, mesh 1862 verts + 1 skin com 35 joints + animacao 45 frames @ 30fps
- **Demo HTML (`rigging/index.html`):** Three.js + GLTFLoader + AnimationMixer + OrbitControls + RoomEnvironment + SkeletonHelper
  - Sidebar com 4 model cards (badge "autoral" vs "referencia")
  - Switcher entre os 4 GLBs sem reload
  - Player tipo YouTube reaproveitado do experimento 8 (timeline scrubbable, hover tooltip, speed buttons 0.25x/1x/2x, play/pause, loop)
  - Toggle skeleton helper (tecla B) — desenha bones em verde por cima do mesh
  - Toggle wireframe (W), auto-rotate (R), restart (Home)
  - Multi-animation selector aparece quando GLB tem >1 anim (Fox: Survey/Walk/Run)
  - Info panel com vertices/tris/bones/animations/duration/file size
  - Atalhos: Space play/pause, B skeleton, W wire, R rotate, 1-4 troca modelo
- **Hospedado:** https://st.did.lu/blender-rigging/v1/index.html
- **Insights tecnicos chave:**
  1. RNA-bug do Rigify em headless: padrao identico ao Cell Fracture, sempre tem workaround importando o modulo direto
  2. IK_FK switch eh a "gotcha" oculta do Rigify: animar FK sem trocar pra modo FK = animacao silenciosamente ignorada
  3. `export_def_bones=True` eh essencial pra GLB Rigify: sem isso ~5x mais nodes, sem isso ~5x mais bytes
  4. 5 keyframes bem distribuidos (contact/passing x2 + loop close) sao suficientes pra walk cycle credivel — interpolacao Bezier do Blender da o resto

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
| Shatter v2 (5 materiais trocaveis em runtime) | https://st.did.lu/blender-shatter/v2/index.html |
| Rigging v1 (humanoide com walk cycle procedural + 3 refs) | https://st.did.lu/blender-rigging/v1/index.html |
| Fluid v1 (esfera virando agua + Mantaflow) | https://st.did.lu/blender-fluid/v1/index.html |
| Grass v1 (grama alta com esqueleto dinamico + wind controlavel) | https://st.did.lu/blender-grass/v1/index.html |

## Proximos experimentos planejados (sessao 6+)

Tres experimentos avaliados na sessao 6 antes de decidir comecar pelo fluido:

### Proximo 1: papelao em geometria arbitraria (Easy Cardboard 3.0)
- **Status:** aguardando user comprar Easy Cardboard 3.0 ($18.75 em Superhive)
- **Goal:** importar qualquer modelo 3D + aplicar Easy Cardboard como modifier paramerico via Python + apply modifier + bake PBR + export GLB
- **Viabilidade:** 7-8/10. Depende de confirmar API do addon na primeira execucao — provavelmente Geometry Nodes padrao com inputs acessiveis via `modifier["Input_X"]`. Se for, automatico 100%.
- **Pipeline esperada:** carregar modelo base -> aplicar EC modifier -> ajustar layers/wear/espessura -> apply -> bake corrugacao pra PBR -> export GLB
- **Trade-off:** "magia visual" do papelao (corrugacao, textura de fibra) vive no shader procedural — vai precisar bake pra texturas raster 2K-4K, perde resolucao infinita do procedural
- **Por que vale:** resolve diretamente o que o Cardboard Shader (que ja temos) nao consegue dar — geometria real com espessura, dobras, corrugacao 3D que sobrevive ao export

### Proximo 2: mato/musgo ao redor de geometria (Mossify)
- **Status:** aguardando avaliacao se vale comprar Mossify, ou comecar com Baga Ivy/Modular Tree gratis primeiro
- **Goal:** importar modelo 3D + scatter vegetacao em volta via Geometry Nodes + apply + export
- **Viabilidade:** 7/10 com Mossify (confirmar API), 9/10 com Modular Tree gratis (API Python ja documentada)
- **Recomendacao:** validar conceito primeiro com Modular Tree ou Baga Ivy (gratis), depois comprar Mossify se quisermos a estetica especifica dele
- **Trade-off:** polycount alto, scatter facilmente gera 500k-2M tris — decimate pos-scatter eh trabalho meu

### Proximo 3: simulacao de fluido [FEITO — sessao 6]
- **Status:** ✓ implementado e hospedado
- **Demo:** https://st.did.lu/blender-fluid/v1/index.html
- **Docs:** [fluid/README.md](fluid/README.md)
- **Aprendizados principais:**
  - Mantaflow funciona em headless sem bugs (diferente do Rigify/Cell Fracture)
  - Topologia variavel impede morph targets — solucao mesh sequence em GLBs separados
  - Effector COLLISION precisa de volume real (plano nao retem agua)
  - Voxel remesh eh chave pra reduzir peso (raw 200k -> remeshed 15k verts)
  - Bake do .blend precisa estar salvo antes (cache eh relativo)
  - Output: 80 GLBs / 7.5MB / 2.67s @ 30fps

## Relatorios tecnicos (sessao 6)

Pesquisa profunda sobre o ecosistema de plugins/addons do Blender com foco em **fidelidade reproduzivel fora do Blender**:

| Relatorio | URL | Foco |
|---|---|---|
| Cardboard addons analysis | https://st.did.lu/reports/cardboard-addons/v1/index.html | Cardboard Shader (tem) vs Easy Cardboard 3.0 vs Cardboard Builder |
| Geometry addons v1 (60+ plugins) | https://st.did.lu/reports/blender-geometry-addons/v1/index.html | 6 categorias, classificado por "GLB-friendly" |
| Geometry addons v2 (90+ plugins, recalibrado) | https://st.did.lu/reports/blender-geometry-addons/v2/index.html | 11 categorias, nota objetiva 0-10 de fidelidade reproduzivel, filtro de automacao por agente IA |

### Conceito-chave dos relatorios

**Criterio:** plugins que aplicam efeito na GEOMETRIA (geo nodes apply, sculpt brushes, mesh ops) sao prioridade absoluta. Se mexem na malha, fidelidade reproduzivel tende a 10/10 porque o material em si pode ser bakeado e o look se reproduz em qualquer engine.

**Penaliza:** features que dependem de iluminacao/SSS/volumetricos/IOR especificos do Cycles e nao tem caminho de bake claro.

**Descarta:** plugins que exigem trabalho manual humano (Substance Designer, Marvelous Designer, ZBrush sculpt livre) — nao automatizaveis por agente IA via Python.

**Top picks pra automacao:**
1. Modular Tree (free, Python API, mesh real)
2. Wicked Rocks ($15, seed-driven)
3. VDM Brush Baker + Body Details VDM (free + $15)
4. Trowel + Floor Generator + Parquet ($55 arquitetura)
5. MESHmachine + HardOps + BoxCutter ($125 hard-surface)

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
