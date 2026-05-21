# Experimento 10 — Simulação de fluido Mantaflow + player web

**Goal:** validar se é possível tirar proveito do motor de física do Blender (Mantaflow) pra gerar animações de fluido que rodam fora do Blender, sem nenhum runtime de física no consumidor final.

**Resultado:** sim, viável.

**Demo:** https://st.did.lu/blender-fluid/v1/index.html

---

## TL;DR

- Pipeline 100% headless via Python (`bpy`)
- Esfera (emissor) cai por gravidade, vira água, espalha no chão
- 2,67 segundos a 30fps = 80 frames
- Output final: **80 GLBs separados (~7,5 MB total)** + manifest + player HTML
- Player tipo YouTube: play/pause, scrub timeline, velocidade 0,25-2x, loop, girar, setas
- Roda em qualquer engine que abre GLB: Three.js, Unity, Unreal, Babylon, model-viewer

---

## O que está aqui

```
fluid/
├── README.md                    # este arquivo
├── index.html                   # player web (versão hospedada idêntica)
├── scripts/
│   ├── probe_mantaflow.py       # sonda inicial — confirma API Mantaflow em headless
│   ├── build_fluid.py           # pipeline principal: setup cena + bake Mantaflow
│   └── extract_frames.py        # extrai 80 GLBs do .blend baked
└── out/                         # GITIGNORED — não comitado
    ├── fluid_sim.blend          # cena Blender com cache
    ├── cache_fluid_*/           # cache Mantaflow (OpenVDB + BOBJECT)
    └── glb/
        ├── manifest.json        # lista de frames + metadata
        └── frames/
            ├── f0001.glb
            ├── f0002.glb
            └── ... 80 arquivos
```

---

## Como reproduzir

```bash
# 1. Bake da simulação (3-5 min)
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" \
  --background \
  --python fluid/scripts/build_fluid.py

# 2. Extrair frames como GLBs individuais (~1 min)
"/c/Program Files/Blender Foundation/Blender 5.1/blender.exe" \
  --background \
  --python fluid/scripts/extract_frames.py

# 3. Servir local
cd fluid && python -m http.server 8771
# abrir http://localhost:8771
```

---

## A pergunta central que respondemos

> Dá pra fazer simulação de física no Blender, exportar o resultado, e rodar em qualquer lugar sem simular nada em runtime?

**Sim.** O conceito de "bake" do Blender resolve isso: a simulação roda uma vez, vira geometria estática (uma malha por frame), e o consumidor final só toca a sequência. Nenhuma física em runtime. Funciona porque:

1. Mantaflow simula partículas internamente, gera mesh-surface a cada frame
2. A gente captura essa mesh-surface por frame (snapshot estático)
3. Empacota num formato que qualquer engine lê
4. O player só troca qual mesh está visível a cada frame

A engine de consumo (Three.js, Unity, Unreal) trata isso como **animação tradicional** — não sabe que aquilo era fluido. Pra ela é só "mesh A no frame 1, mesh B no frame 2, mesh C no frame 3...".

---

## Pipeline técnica passo a passo

### 1. Setup da cena (build_fluid.py)

```python
# Emissor (esfera no alto)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0, 0, 3.0))
emitter.modifiers.new("Fluid", 'FLUID')
emitter_mod.fluid_type = 'FLOW'
emitter_mod.flow_settings.flow_type = 'LIQUID'
emitter_mod.flow_settings.flow_behavior = 'GEOMETRY'  # vira liquido, não emite continuamente

# Domain (cubo invisível)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
domain.scale = (5, 5, 3.5)  # XY amplo pra água espalhar
domain.modifiers.new("Fluid", 'FLUID')
domain_mod.fluid_type = 'DOMAIN'
ds.domain_type = 'LIQUID'
ds.resolution_max = 96       # 96 = balanceado (64 leve / 128 detalhado)
ds.use_mesh = True           # gera mesh-surface por frame
ds.timesteps_min = 2
ds.timesteps_max = 8         # mais substeps = menos penetração do effector
ds.cfl_condition = 2.0       # default 4.0; menor = mais substeps

# Chão (effector colisão)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
floor.scale = (10, 10, 1.0)  # cubo grande achatado, top em z=0
floor.modifiers.new("Fluid", 'FLUID')
floor_mod.fluid_type = 'EFFECTOR'
floor_mod.effector_settings.effector_type = 'COLLISION'
```

### 2. Bake automático

```python
# Salvar .blend ANTES (Mantaflow exige caminho relativo de cache)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))

# Bake data (partículas) + mesh (surface reconstruída)
bpy.context.view_layer.objects.active = domain
bpy.ops.fluid.bake_data()    # ~100s a res 96
bpy.ops.fluid.bake_mesh()    # ~65s a res 96
```

### 3. Extração da mesh sequence (extract_frames.py)

```python
for f in range(1, FRAMES_TOTAL + 1):
    scene.frame_set(f)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    domain_eval = domain.evaluated_get(depsgraph)
    raw_mesh = bpy.data.meshes.new_from_object(domain_eval, depsgraph=depsgraph)

    # Remesh voxel pra reduzir polycount (raw 200k → 5-15k tris)
    temp = bpy.data.objects.new(f"_t_{f}", raw_mesh)
    rm = temp.modifiers.new("Remesh", 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = 0.13  # maior = mais leve

    # Apply + extract + export GLB
    final_mesh = ...
    bpy.ops.export_scene.gltf(filepath=f"f{f:04d}.glb", use_selection=True)
```

### 4. Player HTML/JS (Three.js)

```js
// Carrega manifest + todos os 80 GLBs em paralelo
const promises = manifest.frames.map(async (fi, idx) => {
  const gltf = await loader.loadAsync(`frames/${fi.file}`);
  frameMeshes[idx] = { frame: fi.frame, mesh: gltf.scene };
});
await Promise.all(promises);

// Loop: troca mesh ativo a cada frame
function animate() {
  if (isPlaying && now - lastFrameTime >= 1000 / (fps * speed)) {
    if (currentMesh) scene.remove(currentMesh);
    currentMesh = frameMeshes[currentFrameIndex].mesh;
    scene.add(currentMesh);
    currentFrameIndex++;
  }
}
```

---

## Descobertas técnicas (durante o experimento)

### 1. Mantaflow funciona em headless via Python

Diferente do Rigify (experimento 9) e Cell Fracture (experimento 8) que tinham bugs com operadores RNA em headless, **Mantaflow funciona perfeitamente** via `bpy.ops.fluid.bake_data()` e `bake_mesh()`. Não precisa workaround.

### 2. Mesh-surface tem topologia variável

Esse foi o bloqueio principal pra exportar como GLB único.

- Frame 1 (esfera intacta): 462 vértices
- Frame 30 (espalhada): 7822 vértices
- Frame 60 (ondulando): 5590 vértices

Cada frame é uma **malha completamente nova** — não é a esfera deformada. Mantaflow re-reconstrói a superfície a cada frame via marching cubes a partir das partículas internas.

**Consequência:** morph targets / shape keys / animation tradicional do glTF não funcionam (exigem topologia constante).

### 3. Tentativa fracassada #1 — animar visibility/scale por frame

Tentei criar 80 objetos diferentes no Blender, cada um visível só no seu frame via keyframes em `hide_viewport` ou `scale=0/1`. **O exporter glTF agressivamente filtra invisíveis no frame 1 e exporta só o primeiro mesh.** Confirmado via inspeção do GLB resultante (apenas 1 nó, 1 mesh).

### 4. Solução que funcionou — 80 GLBs separados

Mais simples e robusto. Exporta cada frame como arquivo independente. Player JS troca qual mesh está visível a cada frame. Funciona em qualquer engine que abre GLB sem loader custom.

### 5. Effector COLLISION precisa de volume real

Plano (0 espessura) marcado como effector COLLISION **não retém a água** — ela passa direto. Solução: usar cubo achatado com volume (10×10×1 com top em z=0).

### 6. Coordenada local do domain ≠ world

A mesh extraída do domain via `new_from_object(domain_eval)` vem em **coordenadas locais do domain**, não world. Como o domain estava em z=1.5, todas as malhas extraídas tinham origem deslocada -1.5 em Z. **Solução:** aplicar offset manual `v.co.z += 1.5` em cada vértice antes do export, ou exportar com `export_apply=True` (que aplica transformações).

### 7. Substeps importam pra colisões em velocidade

Resolução 96 voxels + gravidade padrão = água com velocidade alta na queda. Sem substeps suficientes, ela penetra effector. Setei `timesteps_min=2, timesteps_max=8, cfl_condition=2.0`. Mais substeps = bake mais lento mas física mais estável.

### 8. Voxel remesh é a chave pra reduzir peso

Raw mesh por frame: até 358k vértices (frame 60).
Após voxel remesh com `voxel_size=0.13`: 5-25k vértices.
Total GLBs: de ~60 MB pra ~7,5 MB.

Trade-off: voxel maior = silhueta mais "blocada" nos detalhes finos (pingos).

### 9. Mantaflow exige .blend salvo

`bpy.ops.fluid.bake_data()` cria pasta de cache **relativa ao .blend**. Se o arquivo ainda não foi salvo, falha silenciosamente. Solução: `bpy.ops.wm.save_as_mainfile(...)` antes de tudo.

### 10. Borda do domain aparece como linha reta na água

Quando a água espalha e bate na parede do domain (cubo de simulação), forma borda reta. Pra evitar, domain precisa ser muito maior que o splash esperado (XY 5-10x o raio da esfera). Caso contrário, parte da estética fica artificial.

---

## Trade-offs e limitações

### O que sobrevive perfeitamente

- **Forma** da água em cada frame (geometria fiel)
- **Movimento** (caindo, splash, espalhamento, ondas, pingos secundários)
- **Cor base** (via Principled BSDF padrão exportado)

### O que aproximamos

- **Look "água transparente brilhante"** — depende de IOR/refração que glTF padrão não tem. Resolvido no Three.js usando `MeshPhysicalMaterial.transmission: 0.85` + `IOR: 1.33`. Fica ~80% do look do Blender Cycles.
- **Caustics** (padrões de luz no fundo) — não exporta nativamente. Pode ser adicionado em runtime como textura procedural separada.
- **Subsurface scattering** (líquidos opacos como leite/suco) — não exporta.

### Bake time

- Resolução 64: ~30s data + 20s mesh = 50s total
- Resolução 96 (usei): ~100s data + 65s mesh = 165s total
- Resolução 128: ~5-8 min total
- Resolução 256: ~30-60 min

Quanto mais alta a resolução, mais detalhe nos pingos pequenos, mas com retorno decrescente.

---

## Sobre o peso e formatos alternativos

**Hoje (mesh sequence em 80 GLBs):**
- 7,5 MB total
- ~2,8 MB por segundo de animação
- Funciona em qualquer engine que abre GLB sem loader custom

**Alternativas pra ter num arquivo único:**

| Formato | Peso estimado | Pros / Cons |
|---|---|---|
| **80 GLBs (atual)** | 7,5 MB | Universal, sem loader custom. Mais pesado. |
| **Alembic (.abc)** | 2-3 MB | Padrão indústria pra mesh cache. Unity/Unreal nativo. Three.js precisa loader não-oficial. |
| **USD (.usdz/.usda)** | 3-4 MB | Moderno (Pixar). Unity/Unreal recentes leem. Three.js suporte parcial. |
| **VAT (Vertex Animation Texture)** | 1,5-2 MB | Exige shader custom mas é simples. Roda em qualquer engine WebGL. Exige topologia constante (precisa preparo). |
| **GLB + draco compression** | 4-5 MB | Mantém compatibilidade GLB. Tira 30-50% sem perda perceptível. |

**Todos esses formatos:** a física ainda foi feita uma única vez no Blender, baked, virou geometria estática. Nenhum simula nada em runtime. **A escolha do formato é só sobre empacotamento e tamanho final** — não muda o conceito do experimento.

---

## Esse fluxo é viável pra produção?

**Web (Three.js, browser):**
- 7,5 MB pra hero piece de 2,7s é razoável
- Carrega em 2-5s numa conexão razoável
- Viável pra demos, galerias, landing pages
- Não viável pra ter 20 fluidos diferentes na mesma página

**Unity / Unreal (jogos):**
- 7,5 MB por animação é OK pra cena inteira
- Workflow ideal seria Alembic via importer oficial (mais compacto, mais nativo)
- Mesma física no Blender, só muda o formato de export

**Mobile (React Native + Three.js):**
- Aceitável pra animação única
- Compactar pra ~3-4 MB com menos frames ou draco compression

---

## O que NÃO foi testado

- **Líquidos com viscosidade alta** (mel, chocolate) — Mantaflow suporta via `viscosity_base/exponent`, não testei
- **Interação fluido + objetos rígidos** (gota caindo num cubo, p. ex.) — funciona em Mantaflow, não testei aqui
- **Fluido em movimento contínuo** (jato d'água, fonte) — exige `flow_behavior='INFLOW'` em vez de `'GEOMETRY'`
- **Whitewater/foam** — Mantaflow suporta, exigiria pass adicional no bake
- **Resolução 128+ pra qualidade cinema** — só testei até 96

---

## Próximos refinamentos possíveis

1. **Draco compression** nos GLBs → cai 30-50% sem perda perceptível
2. **Convert to Alembic** → gera 1 arquivo .abc compacto pra Unity/Unreal
3. **Aumentar resolução pra 128** → mais detalhe nos pingos secundários
4. **Domain maior** → elimina bordas retas onde água bate na parede invisível
5. **Material avançado** → adicionar Fresnel + caustics fake via textura procedural no Three.js
6. **Variar cenários** → líquido viscoso, fluido contínuo, fluido + obstáculo

---

## Links

- **Demo hospedada:** https://st.did.lu/blender-fluid/v1/index.html
- **Repositório:** https://github.com/mr-velvet/blender-experiments-2026
- **Commit base:** ver `git log -- fluid/`

---

## Apêndice — comandos Python úteis

```python
# Bake só data, sem mesh
bpy.ops.fluid.bake_data()

# Bake só mesh (precisa data já bakeado)
bpy.ops.fluid.bake_mesh()

# Bake tudo de uma vez (data + mesh juntos)
bpy.ops.fluid.bake_all()

# Free cache (pra re-bakear do zero)
bpy.ops.fluid.free_all()

# Pular pra um frame específico (necessário antes de extrair)
scene.frame_set(f)

# Extrair mesh "como está no frame atual"
depsgraph = bpy.context.evaluated_depsgraph_get()
mesh = bpy.data.meshes.new_from_object(
    domain.evaluated_get(depsgraph),
    depsgraph=depsgraph
)
```

---

*Documentado em 2026-05-21 — sessão 6.*
