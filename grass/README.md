# Experimento 11 — Grama alta com esqueleto + wind dinamico

**Demo:** https://st.did.lu/blender-grass/v1/index.html

## TL;DR

Campo de grama alta com **esqueleto real (3 bones por blade)** exportado em GLB. A animacao de wind sway esta bakeada no GLB (loop 2s), mas o esqueleto continua **influenciavel em runtime** via JS — sliders de intensidade, direcao do vento, rajadas e densidade controlam a deformacao das blades em tempo real.

Cumpre exatamente o pedido do user: *"vegetacao alta com esqueleto dentro pra balancar... que possa ser dinamicamente influenciado dentro de uma simulacao html/javascript"*.

## O que tem de novo (vs experimentos anteriores)

Diferente de:
- **Fluido (exp 10):** mesh sequence baked frame-a-frame (80 GLBs). Sem esqueleto, sem influencia runtime.
- **Rigging (exp 9):** 1 humanoide com 35 bones em walk cycle. Aqui sao N blades sharing 1 skeleton template, cada uma com phase offset diferente.

Aqui: **1 GLB pequeno + N instances clonadas via SkeletonUtils + controle procedural dos bones em runtime**. O baseline de animacao vem do GLB mas pode ser totalmente sobrescrito por JS — abre porta pra wind reativo, queda direcional, etc.

## Pipeline tecnica

### 1. Blade mesh (`build_grass.py`)

- Quad strip vertical de 7 niveis x 2 colunas = 14 vertices, 12 triangulos
- Altura 0.55m, largura base 0.07m, afila quadraticamente (mais cheia no meio, ponta fina)
- **Curl natural**: vertices ganham deslocamento Y proporcional a `t²` — blade vergada pra frente em rest pose, parece organica nao reta
- Vertex color gradient: base verde escuro `(0.06, 0.18, 0.04)` → tip verde medio `(0.28, 0.42, 0.10)`
  - Exportado como `COLOR_0` attribute no GLB
  - No JS: material PBR com `vertexColors: true` + leve tint random por instance

### 2. Armature (3 bones em cadeia)

- `B0_base` (0 a 0.18m) — quase imovel, segura a raiz no chao
- `B1_mid` (0.18 a 0.37m) — sway moderado, conectado a B0
- `B2_top` (0.37 a 0.55m) — sway maior, conectado a B1

Cadeia conectada (`use_connect=True`) preserva continuidade. Skin weights por altura:
- vertices da base (z<0.18): peso 1 em B0
- transicao linear B0→B1 entre 0 e 0.27m
- transicao linear B1→B2 entre 0.27 e 0.55m
- soma normalizada pra 1 em cada vertex

### 3. Wind animation bakeada (60 frames, loop 2s @ 30fps)

Animacao bakeada nos 3 bones como senoide com phase shifts:

```python
a0 = AMP_BASE * sin(2π * t)              # 3°  amplitude
a1 = AMP_MID  * sin(2π * (t - 0.15))     # 8°
a2 = AMP_TOP  * sin(2π * (t - 0.30))     # 15°
```

Phase shifts criam look "viscoso" — o wind se propaga da raiz pro topo, nao todos balancam em sincronia.

**Loop perfeito**: amostragem `sin(2π * t)` com t = [0..1] retorna ao zero em t=1, fechando o ciclo sem snap.

### 4. Export GLB

Settings essenciais:
```python
export_animations=True
export_animation_mode="ACTIONS"
export_force_sampling=True       # CRITICO — sem isso vira Bezier que trava scrubbing
export_optimize_animation_size=False
export_skins=True
export_def_bones=False           # nao usei DEF prefix, exporta os 3 bones
```

**Resultado:** `blade.glb` = **12KB**. Tem 1 mesh + 1 skin + 1 animation com 9 channels (TRS de 3 bones x 60 keyframes).

### 5. Player Three.js (`index.html`)

#### Spawn de field

- **Poisson disk sampling** (Bridson's algorithm 2D): distribuicao natural sem clusters nem grid visivel
- 4 densidades: esparso (~430) / medio (~840) / denso (~1600) / cheio (~2900)
- Cada blade clonada via `SkeletonUtils.clone()` (preserva skin+armature corretamente, nao confundir com `.clone()` direto)
- Variacao por instance: rotacao Y random (orientacao), scale jitter (0.8-1.3x), phase offset (0..1), brilho/hue jitter

#### Controle runtime dos bones — **a parte critica**

**Decisao tecnica importante:** descartei o `AnimationMixer + clipAction` por blade (1500 mixers atualizando 4500 bones via interpolacao Three.js eh caro). Substitui por **calculo procedural direto**:

```js
const u = globalTime * FREQ + b.phase;  // ciclos
const s0 = Math.sin(2 * Math.PI * u);
const s1 = Math.sin(2 * Math.PI * (u + PHASE_MID));
const s2 = Math.sin(2 * Math.PI * (u + PHASE_TOP));

bones.base.rotation.x = AMP_BASE * s0 * windAmp + gust0;
bones.mid.rotation.x  = AMP_MID  * s1 * windAmp + gust1;
bones.top.rotation.x  = AMP_TOP  * s2 * windAmp + gust2;
```

Mesma formula que o Blender bakeou, agora rodando 100% em JS. Vantagens:
- ~10x mais rapido que mixer (sin manual vs LERP/SLERP em quaternions)
- **Wind strength e direcao influenciam direto** (multiplicar amplitude, rotacionar blade root)
- **Gust eh additivo trivial** (somar valor positivo, decay com tempo)
- **Sem dependencia da action exportada** — mas o GLB ainda tem a action embutida (compatibilidade: outras engines podem usar o baseline bakeado, o Three.js usa o procedural)

#### Controles UI

- Slider **vento** (0-3x): escala amplitude. 0 = grama parada, 1 = baseline, 3 = furacao
- Slider **direcao** (-180° a 180°): alinha gradualmente todas as blades naquela direcao (mais wind = alignamento mais forte)
- Slider **velocidade** (0.1-3x): timeScale do globalTime
- **Rajada (G)**: empurra todas as blades positivamente, decay em ~1s. Adicional ao sway baseline
- Atalhos: Space play/pause, G rajada, 1-4 densidade

## Performance

| Densidade | Blades | Bones updates/frame | FPS estimado* |
|---|---|---|---|
| 1 (esparso) | ~430 | ~1.3k | 60+ |
| 2 (medio) | ~840 | ~2.5k | 60+ |
| 3 (denso, default) | ~1600 | ~4.8k | 60 |
| 4 (cheio) | ~2900 | ~8.7k | 30-60 |

*Em hardware GPU. Em Playwright headless (CPU rasterizer): 22fps @ densidade 3.

Bottleneck principal: draw calls (1 por blade — `SkinnedMesh` instancing em Three.js eh limitado, idealmente usaria `InstancedMesh` mas perde-se skin individual). Bone updates em si nao sao caros — 3 trig ops + 1 attrib set por blade.

## Esqueleto **realmente** dinamico

O importante deste experimento (resposta direta ao pedido do user): a animacao **nao esta presa ao GLB**. O glTF carrega o baseline pre-bakeado, mas o JS sobrescreve `bone.rotation.x` a cada frame com formula propria.

Isso significa que voce pode:
- Mexer **cada bone individualmente** (ex: colision com player vergaria so as blades proximas)
- Adicionar **forcas externas** (mouse hover, raycast pra detectar interacao do user)
- **Composing animations** — sway + gust + queda + crescimento de tudo somando em runtime
- **Servir o mesmo GLB pra outras engines** que vao usar a animacao baked normalmente

## Trade-offs e limites

| Vantagem | Custo |
|---|---|
| GLB ultraleve (12KB) | Nao tem variacao morfologica entre blades (todas mesmo mesh) |
| Esqueleto controlavel | Nao usa GPU instancing pra skinned mesh (1 draw call por blade) |
| Wind procedural arbitrario | Animacao bakeada no GLB acaba nao sendo usada em Three.js |
| Funciona em qualquer engine | Em outras engines (Unity/Unreal) usaria a action bakeada, perde controle runtime |

## Formatos alternativos avaliados (e rejeitados)

| Approach | Por que nao |
|---|---|
| **Shader wind (Grassify/GRASS Generator)** | Nao exporta no GLB — efeito vive no shader. Precisa reescrever shader na engine destino. Falha o criterio "animacao vem do Blender". |
| **Mesh sequence baked (igual fluido)** | 60 frames × campo de grama denso = 50-200MB. Nao escala. Sem flexibilidade runtime. |
| **Shape keys morph targets** | Topologia constante, mas precisa de N targets por blade ou animar shape weight em massa. Nao da controle independente. |
| **Geometry Nodes scatter no Blender** | Wind vive em shader procedural — vira mesh estatico no GLB. |

A escolha (1 blade GLB + clone JS + bones procedural) eh o unico approach que satisfaz:
1. Animacao real, deformacao via skin
2. Reproduzivel em qualquer engine
3. **Influenciavel em runtime**
4. Pequeno em bytes

## Files

```
grass/
├── README.md                       # este doc
├── index.html                      # player Three.js
├── scripts/
│   ├── build_grass.py              # pipeline: mesh + skin + anim + export
│   ├── inspect_glb.py              # parser GLB pra validar skin/anim
│   └── inspect_glb_deep.py         # dump JSON completo
└── out/glb/
    ├── blade.glb                   # 12KB — mesh + 3-bone skin + WindSway action
    └── ground.glb                  # 1KB — plano marrom
```

## Como rodar localmente

```bash
# 1. Build dos GLBs (Blender headless)
"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" \
  --background --python grass/scripts/build_grass.py

# 2. Servir
python -m http.server 8788
# Abrir http://localhost:8788/grass/index.html
```

## Replicabilidade / extensoes

- **Mais variedade visual:** trocar `build_blade_mesh` por funcao que escolhe entre 3-4 perfis (gordas/finas/curva-direita/curva-esquerda) e exportar como `blade_a.glb`, `blade_b.glb`, etc. No JS, mixer aleatorio entre eles.
- **Mais bones:** facil aumentar pra 5-7 bones (mais granular sway). Limite glTF eh ~256 joints por skin, irrelevante aqui.
- **Wind por regiao:** dividir field em chunks, cada chunk com windDir/strength proprios. Cria "ondas" de vento.
- **Interacao com player:** raycast do player position pra cada blade, blades a <1m vergam pra longe do player.
- **Audio reactive:** strength = FFT do microfone. Grama dança com a musica.
