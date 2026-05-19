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
