# Learnings — Automacao Blender (sessao 2026-05-19)

Conhecimento tecnico reutilizavel pra proximos experimentos com Blender headless + materiais comprados (Superhive/BlenderMarket/Polyhaven/etc).

---

## 1. Setup que funciona

- **Blender 5.1.2** + addon `blender-mcp` (declara `blender: (3, 0, 0)`, roda em 5.1 sem mexer).
- Addon instalavel programaticamente via `bpy.ops.preferences.addon_install(filepath=..., overwrite=True)` seguido de `addon_enable(module=...)` + `save_userpref()`. Nao precisa abrir UI do Blender.
- MCP server adicionado ao Claude Code via `claude mcp add blender -s user -- uvx.exe blender-mcp`. **Escopo `user`** garante que vale em qualquer projeto.
- Path do executavel no Windows: `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`.

## 2. Dois modos de operacao — quando usar cada

| Modo | Quando usar | Trade-off |
|---|---|---|
| **Headless via Python** (`blender --background --python script.py`) | Pipelines batch, geracao automatizada, CI, qualquer coisa reproduzivel | Determinismo total; sem feedback visual ao vivo |
| **MCP server interativo** | Trabalho ao vivo na cena (mover objeto, ajustar material, debugar visualmente) | Precisa Blender aberto + "Start MCP Server" no painel BlenderMCP da sidebar (N) |

**Default: headless.** So abrir Blender + MCP quando precisar de iteracao visual.

## 3. **A pegadinha critica do glTF/GLB export**

> O exportador glTF do Blender **descarta silenciosamente** qualquer node tree procedural que nao termine num `Principled BSDF` reconhecivel. O GLB sai com BSDF default branco translucido (parece vidro/plastico).

Isso afeta praticamente **todo material comprado bom** (Superhive etc), porque eles normalmente sao construidos como um `node group` customizado ligado direto no `Material Output > Surface`.

### Sintomas
- No Blender o material aparece perfeito (papelao, metal, madeira)
- No GLB exportado, no model-viewer/three.js/Babylon: cubo branco translucido com luz passando

### Como diagnosticar em 5 segundos
```python
mat = bpy.data.materials['NomeDoMaterial']
out = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
src = out.inputs['Surface'].links[0].from_node
print(src.type)  # se NAO for 'BSDF_PRINCIPLED' -> vai dar problema no export
```

### Solucao: **bake PBR** antes de exportar
Pipeline implementado em `pipeline/bake_and_export.py`:

1. Append material no objeto
2. **Smart UV unwrap** (essencial — sem UV bom, bake fica esticado)
3. Pra cada pass (`DIFFUSE`, `ROUGHNESS`, `NORMAL`):
   - Cria image data block
   - Adiciona `ShaderNodeTexImage` no material, marca como active
   - `bpy.ops.object.bake(type=...)`
   - Remove o node temp
4. Constroi um material novo: `Principled BSDF` + 3 `ShaderNodeTexImage` apontando pros PNGs bakeados
5. Roughness/Normal devem ter `colorspace_settings.name = 'Non-Color'`
6. Normal precisa de `ShaderNodeNormalMap` entre a textura e o BSDF
7. Substitui material no objeto, exporta GLB

**Settings de bake importantes:**
- `scene.render.bake.use_pass_direct = False` + `use_pass_indirect = False` — pra nao bakear sombras/iluminacao
- `scene.render.bake.use_pass_color = True`
- `scene.render.bake.margin = 8` (pixel bleeding pra evitar seams)
- `scene.cycles.samples = 16` (bake nao precisa de muito sample)

### Quando NAO precisa de bake
- Material ja eh um `Principled BSDF` puro com texturas — passa direto pro GLB
- Material usa apenas nodes que o glTF entende (Image Texture, Normal Map, Separate/Combine RGB simples)
- Existe o node `glTF Material Output` que permite controle granular de export sem bake (avancado)

## 4. Resolucao de bake — heuristica

| Bake res | Tamanho GLB tipico (1 obj) | Quando usar |
|---|---|---|
| 512 | ~1 MB | Preview rapido, mobile, asset thumbnail |
| 1024 (default) | ~3-4 MB | Padrao bom; fica bem em viewer web |
| 2048 | ~12-15 MB | Hero asset, foto closeup |
| 4096 | ~50+ MB | Cinema/print — raramente vale a pena pra web |

Materiais procedurais com pattern alta frequencia (paper grain, scratches) **ganham** menos com resolucao alta — o pattern eh procedural, vai virar pixel art em qualquer resolucao. Texturas image-based (paper002 etc) escalam melhor.

## 5. Append vs Link de material

```python
with bpy.data.libraries.load(src_blend, link=False) as (data_from, data_to):
    data_to.materials = [mat_name]
```

- `link=False` (append) — copia o material pro arquivo atual, **inclui node groups e texturas dependentes**. Use sempre pra bake/export.
- `link=True` — referencia externa. Quebra se mover o .blend. Nao usar pra GLB.

## 6. Smart UV unwrap — parametros

```python
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
```

- `angle_limit` em radianos (66 graus padrao do Blender)
- `island_margin=0.02` — espacamento entre ilhas UV. Sem isso, bleeding entre faces.
- Pra **esfera/torus/suzanne**: smart_project funciona bem
- Pra **cubo**: idealmente usar `cube_project` mas smart funciona

## 7. Batch generation — padrao 1 combo por processo

Em vez de gerar N combos numa unica invocacao do Blender, **invocar Blender N vezes**, cada uma com 1 combo:
- Isola estado (vazamento de data blocks entre runs)
- Crash de 1 combo nao mata os outros
- Da pra paralelizar trivialmente (multiprocessing) se precisar
- Caching natural: se GLB ja existe, pula

Ver `pipeline/batch_run.py`.

## 8. Caminhos no manifest — Windows pegadinha

`Path.relative_to(ROOT).as_posix()` — usa o `as_posix()` no fim. Sem isso, no Windows o JSON sai com `\\` que quebra `fetch()` no browser.

## 9. Verificacao visual obrigatoria

Render do Cycles dentro do Blender **NAO eh prova** de que o GLB funciona. Sempre testar o GLB num viewer externo (model-viewer eh o mais facil: `<model-viewer src="x.glb">`). 

Pipeline atual ja gera os dois lado-a-lado em `viewer/index.html` — comparacao visual eh o teste de aceitacao.

## 10. Lights e camera — defaults razoaveis

```python
# Camera 3/4
cam.location = (4, -4, 3.2)
cam.rotation_euler = (1.0, 0, 0.785)

# Sun key light
sun_data.energy = 3.0
sun.rotation_euler = (0.785, 0.3, 0.5)

# World cinza neutro
bg.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
bg.inputs['Strength'].default_value = 0.5
```

Pro model-viewer no HTML: `environment-image="neutral"` + `tone-mapping="aces"` + `exposure="1.0"` da resultado decente sem HDR custom.

## 11. Gotchas conhecidos

- **`use_nodes = True`** — deprecated em Blender 6.0, mas necessario em 5.1. Warning eh esperado.
- **Materiais "Mat1/Mat2"** do pack Cardboard sao pra texto (`TextBase`), nao escalam pra cubo/esfera — bake sai cinza. Sempre conferir pra que objeto o material foi feito.
- **Texturas externas**: o `libraries.load(link=False)` copia o **datablock** mas se a textura referencia path absoluto que nao existe, o bake sai preto. Conferir `bpy.data.images[*].filepath` apos append.
- **glTF embedded vs separate**: `export_format='GLB'` embute tudo num arquivo binario. Pra dev/debug, `GLTF_SEPARATE` da .gltf+.bin+texturas separadas (mais facil de inspecionar).

## 12. Workflow recomendado pra material novo comprado

1. Abrir o .blend headless pra **listar o conteudo**:
   ```python
   print([m.name for m in bpy.data.materials])
   print([o.name for o in bpy.data.objects])
   print([ng.name for ng in bpy.data.node_groups])
   ```
2. **Diagnostico do material** (passo 3 acima): vale bake?
3. Rodar 1 combo de teste (`pipeline/bake_and_export.py --shape cube --material "X" --src-blend ...`)
4. Abrir GLB no model-viewer pra validar
5. Se OK, adicionar ao `MATERIALS` em `batch_run.py` e rodar batch completo
6. Reportar resultado na pagina `viewer/index.html`

## 13. Limites honestos do que dah pra automatizar

| Funciona bem (autonomo) | Precisa intervencao manual |
|---|---|
| Append material + aplicar em primitivo | Materiais que exigem geometria especifica (text, displacement intenso) |
| Smart UV unwrap pra primitivos | UV unwrap pra modelos organicos complexos |
| Bake PBR (diffuse/roughness/normal) | Bake de displacement/SSS/transmission |
| Export GLB | Setup de animacao/rigging |
| Render preview Cycles 64 samples | Iluminacao cinematica (HDR setup, area lights tuning) |
| Batch geracao de variacoes | Modelagem organica de zero |
| Deformacao procedural (subsurf+displace) | Sculpt detalhado de feicoes especificas |
| VDM stamping em primitivos com poucas faces | VDM stamping em mesh densa organica (vira spike) |

## 14. Cubo + Smart UV + materiais com Object Coord = lixo

Pack Clay Doh (e provavelmente outros com `Object Mapping+ Node`) usa coordenadas de objeto/mundo internamente. Quando rodo `smart_project` no cubo + bakeio, cada face recebe pedaco descontinuo do volume procedural → resultado: listras, distorcoes, cubo virou "casca de madeira".

**Solucoes:**
- **Dropar cubo do batch** se materiais sao procedurais com Object Coord (decisao usada no batch Clay Doh)
- Forcar `cube_project` em vez de `smart_project` pra cubos (faces alinhadas com eixos preserva continuidade)
- Materiais com Generated/UV coord nao sofrem isso

Formas organicas (sphere/torus/suzanne) nao tem esse problema porque smart_project ja respeita topologia continua.

## 15. Deformacao real da geometria antes do export (massinha amassada)

`faces/squash_and_export.py` — adiciona modifiers ANTES do bake:

```python
subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
subsurf.levels = 4
tex = bpy.data.textures.new(name="Clouds", type='CLOUDS')
tex.noise_scale = 1.0 / noise_scale
disp = obj.modifiers.new(name="Displace", type='DISPLACE')
disp.texture = tex
disp.strength = 0.25
disp.mid_level = 0.5
bpy.ops.object.modifier_apply(modifier=subsurf.name)
bpy.ops.object.modifier_apply(modifier=disp.name)
```

**Importante:**
- Apply na ORDEM (Subsurf primeiro pra ter geometria, Displace depois)
- Use `CLOUDS` (smooth bumps) em vez de `NOISE` (white noise = serrilhado)
- `strength=0.15` sutil; `0.3` bem amassado; `>0.5` derrete o cubo todo
- `noise_scale=0.5` bumps grandes; `2.0` bumps medios; `5.0` bumps pequenos
- GLB sai 3-5x maior (geometria densa), mas silhouette muda ao rotacionar (nao eh ilusao)

Combinar com bake do material: faz a deformacao primeiro, depois bakeia o material em cima da mesh ja deformada. Normal map captura detalhes finos, geometria captura volume grosso.

## 16. VDM brush stamping algoritmico (sem bpy.ops.sculpt)

**O problema:** VDM (Vector Displacement Map) brushes sao stamps de displacement 3D, RGB → XYZ em tangent space. Operadores `bpy.ops.sculpt.brush_stroke` sao fragil — exigem sculpt mode + brush asset + stroke dict + texture sample carregada. Em scripts headless da problema.

**A solucao:** algoritmo manual em `faces/vdm_stamp.py`:

```
1. Pra cada poly F na mesh ORIGINAL (antes de subdividir):
     anchor = (center, normal, tangent_u, tangent_v, radius=sqrt(area)*0.5)
2. Subdivide a mesh densamente (subsurf 4-5)
3. Carrega EXR como bpy.data.images, le pixels em float
4. Pra cada anchor, pra cada vertex novo:
     d = vert.co_world - anchor.center
     if abs(d.dot(n)) > radius*1.5: skip  # vertex muito longe do plano da face
     u_local = d.dot(tangent_u); v_local = d.dot(tangent_v)
     if max(|u_local|, |v_local|) > radius*stamp_scale: skip  # fora do quadrado
     uv = ((u_local/half)*0.5+0.5, (v_local/half)*0.5+0.5)
     r,g,b = sample_exr_bilinear(pixels, uv)  # ja centrado em 0, nao em 0.5
     delta = (tangent_u*r + tangent_v*g + normal*b) * displace_strength
     falloff = radial cosine na borda (0.85-1.0)
     vert.co += delta * falloff (em local space)
```

**Convencao VDM:**
- R = tangent u (deslocamento no eixo horizontal do brush)
- G = tangent v (vertical)
- B = normal (pra fora da face — "altura" do detalhe)
- Valores **centrados em 0** (nao 0.5), variam em [-0.2, 0.8] tipicamente
- Linear Rec.709 colorspace (nao sRGB)

**Pack Human Face VDM (DoubleGum):** 30 EXRs 512x512 float, cada um eh uma face humana diferente. `Texture/Map_ (N).exr` (espaco no nome).

## 17. Edge crease via bmesh em Blender 5.1+

A API antiga `edge.crease = 1.0` nao funciona mais — atributo nao existe na BMEdge. Tem que ir via bmesh layer:

```python
bm = bmesh.new()
bm.from_mesh(obj.data)
crease_layer = bm.edges.layers.float.get("crease_edge")
if crease_layer is None:
    crease_layer = bm.edges.layers.float.new("crease_edge")
for e in bm.edges:
    e[crease_layer] = 1.0
bm.to_mesh(obj.data)
bm.free()
```

Depois, no modifier Subsurf: `mod.use_creases = True` (default ja eh True).

**Quando preservar crease em batch:**
- ✅ Cube, cylinder (poliedros quadrangulares) — preserva quinas duras
- ❌ Icosphere, sphere com muitos segments, suzanne — vira "ourico" porque cada triangulo vira spike preservado
- Heuristica: `len(obj.data.polygons) <= 60` ou `shape in ("cube", "cylinder")`

## 18. VDM stamping em mesh organica = virus com espinhos

Algoritmo de stamp colocar 1 anchor por face. Se a mesh original tem 80 faces triangulares pequenas (icosphere subdiv=2), bakeia 80 caras minusculas → mesh vira porco-espinho de massinha.

**Workarounds:**
- Usar formas com poucas faces grandes: cube (6), cylinder com vertices=12 (14), icosphere com subdivisions=1 (20)
- Pra suzanne/sphere: precisaria identificar regioes planas grandes ("patches" de bochecha, testa) e estampar so la — nao implementado
- Filtrar anchors por area minima: `if poly.area < 0.3: skip` (nao testado, mas direto)

## 19. Pattern de viewer com modal de detalhe + deep-link

Padrao usado em `claydoh/index.html` e `viewer/index_v2.html`:

- Card clicavel abre modal fullscreen com `<model-viewer>` grande + render Cycles lado a lado
- Click no modelo dentro do card NAO abre modal (`e.target.closest("model-viewer")` retorna early)
- URL hash sincronizada com modal aberto (`#combo_id`) → deep-link funciona
- Close por X, click no backdrop, ou ESC
- Botao "baixar .glb" no footer do modal (download link)
- Manifest com paths absolutos GCS pra evitar duplicacao entre v1/v2

Implementacao JS:
```js
function openModal(it) {
  history.replaceState(null, "", "#" + it.combo_id);
  // ... popular modal ...
  document.getElementById("modal").classList.add("open");
}
function openFromHash() {
  const id = location.hash.replace(/^#/, "");
  const it = ITEMS.find(x => x.combo_id === id);
  if (it) openModal(it);
}
window.addEventListener("hashchange", openFromHash);
```

## 20. Deploy padrao no GCS (st.did.lu)

Estrutura usada: `gs://didlu-imagestore/<projeto>/v<N>/`:
- `index.html` na raiz
- `out/manifest.json` (ou `manifest_v2.json` com URLs absolutas pros assets de uma v1)
- `out/glb/*.glb`, `out/renders/*.png`

Versionamento (v1, v2, ...) pra invalidar cache agressivo do bucket. v2 pode reaproveitar assets da v1 via manifest com URLs absolutas (`https://st.did.lu/projeto/v1/out/...`) → economiza upload de centenas de MB.

Upload via gcloud:
```bash
"/c/Program Files (x86)/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd" \
  storage cp --recursive out/glb gs://didlu-imagestore/projeto/v1/out/
```

URL curta: `https://st.did.lu/<path>` (CNAME DNS pro bucket).

## 21. Pegadinhas ao extrair assets de um pack monolitico (.blend gigante com N modelos)

Aplicado em `extract/extract_assets.py` no pack Everything Library (gratuito, ~85 buildings + 178 animals num so .blend cada).

### Setup tipico do pack
Hierarquia geralmente: `ROOT_EMPTY (BUILDINGS) > Categoria (Empty) > Asset (Empty) > Meshes`. Cada filho direto de uma categoria eh um asset coerente (ex: Bank, Pagoda, Yurt, Elephant). Quando voce quer reusar so o modelo individual em outros projetos, precisa quebrar em N arquivos.

### Bug 1: objetos linkados em multiplas collections → exporter duplica nodes
Pack original linka cada objeto na collection especializada (`Buildings`) E na **Scene Collection raiz** (provavelmente porque o autor usou drag-drop ou alguma operacao que duplica linkagem). Resultado: `obj.users == 2`. Quando exporta com `use_selection=True`, o glTF exporter expande pra **3 copias do Empty + 6 copias dos meshes** num asset que deveria ter 4 nodes.

**Fix:** ao carregar o .blend, unlink da Scene Collection raiz os objetos que tambem estao em alguma sub-collection:
```python
scene_coll = bpy.context.scene.collection
for o in list(scene_coll.objects):
    other_colls = [c for c in o.users_collection if c != scene_coll]
    if other_colls:
        scene_coll.objects.unlink(o)
```

### Bug 2: layer_collection.hide_viewport=True → visible_get() retorna False → exporter ignora tudo
A collection do pack veio com **olhinho desligado no outliner** (layer_collection.hide_viewport=True). Isso faz `obj.visible_get() == False` mesmo com `obj.hide_viewport == False` e `hide_render == False`. O exporter glTF com `use_visible=True` ignora silenciosamente, e voce ganha GLBs de **132 bytes** (so header).

**Fix:** depois de abrir o .blend, walk recursivo na `view_layer.layer_collection` desligando hide_viewport/exclude:
```python
def unexclude(lc):
    if lc.exclude: lc.exclude = False
    if lc.hide_viewport: lc.hide_viewport = False
    if lc.collection.hide_viewport: lc.collection.hide_viewport = False
    for ch in lc.children:
        unexclude(ch)
unexclude(bpy.context.view_layer.layer_collection)
```

### Bug 3: assets vem em coordenadas absolutas do mundo, sem centralizacao
Meshes do pack tinham vertices em escala 1000+ unidades porque a cena original posicionava tudo num grid grande. Cada GLB exportado tinha bbox enorme e descentralizado — model-viewer enquadra a cena toda e o asset aparece minusculo num canto.

**Fix:** calcular bbox global dos meshes do asset, mover **todos** os descendants (matrix_world.translation) pra origem antes do export, reverter depois:
```python
bb_min = Vector((1e18, 1e18, 1e18)); bb_max = Vector((-1e18, -1e18, -1e18))
for m in mesh_descs:
    mw = m.matrix_world
    for v in m.data.vertices:
        wp = mw @ v.co
        for k in range(3):
            bb_min[k] = min(bb_min[k], wp[k]); bb_max[k] = max(bb_max[k], wp[k])
offset = Vector((-(bb_min.x+bb_max.x)*0.5, -(bb_min.y+bb_max.y)*0.5, -bb_min.z))  # apoia em Y=0 do glTF
for d in descendants:
    mw = d.matrix_world.copy(); mw.translation += offset; d.matrix_world = mw
bpy.context.view_layer.update()
```

**OBS:** mover so o Empty pai NAO funciona — em Blender, parent compoe matrix_local, mas filho com matrix_world propria nao herda translacao mundial. Precisa mexer em todos.

### Bug 4 (preventivo): exportar animacoes/morph/skin
Mesmo sem mexer, animacoes do pack viram nodes extras / aumentam GLB. Pra extrair so geometria:
```python
bpy.ops.export_scene.gltf(..., export_animations=False, export_morph=False, export_skins=False)
```

### Pattern reutilizavel
Script generico: `extract_assets.py --src <blend> --out-dir <dst> --root-name BUILDINGS`. Funciona em qualquer pack que use hierarquia `Empty > Empty > Mesh`. Suporta `--dry-run`, `--only <asset>`, `--skip-existing`. Processo unico de Blender para os N assets — usa scene compartilhada com hide+show dos outros objetos pra isolar selecao.

### Custo
263 GLBs (~39 MB total) em ~3 minutos de Blender (1 processo, scene shared). Cada GLB tem 0.3-1.2s de export.
