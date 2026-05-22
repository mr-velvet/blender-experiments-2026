# Experimento 13 — Easy Cardboard 3.1 (autonomia total)

## Goal

Validar autonomia do agente para usar um addon comercial complexo do Blender (Easy Cardboard 3.1, Superhive) num pipeline 100% headless: descobrir como o asset funciona, configurar o modifier, fazer bake, exportar GLB com texturas embedded, montar demo web e deployar — sem perguntar nada ao user apos o briefing inicial.

## Demo

https://st.did.lu/cardboard-experiment/v1/index.html

## Descobertas tecnicas sobre o asset

O **Easy Cardboard 3.x** nao eh um addon Python tradicional. Eh distribuido como um arquivo **`.blend` contendo Geometry Nodes** (44 node groups) e um material shader complexo (`Easy Cardboard 3`). O fluxo:

1. **Append** o node group `📦 Easy Cardboard 3.0` (geometry) e o material `Easy Cardboard 3` em outro `.blend`
2. **Atribui** o node group como `Geometry Nodes modifier` ao seu mesh
3. O modifier **solidifica** o mesh + **adiciona detalhes de borda** (Smart Solidify 2.0) + **fibras** + **dano nas quinas**
4. A **corrugacao em si NAO eh geometria** — eh textura no shader, mapeada via UV Direction Mask (caras com UV alinhadas a direcao do corrugado mostram listas; caras perpendiculares ficam lisas)
5. Por isso o asset exige **UV map no mesh de entrada** (ver Image #1 do asset: "Easy Cardboard 3 currently requires a UV map")

## Pipeline

`scripts/02_build_box.py` — script unico que faz tudo via `blender --background`:

1. Append node group + material do `assets/easy-cardboard-3.1.blend`
2. Cria cubo 30×20×15cm via bmesh com 8 subdivisoes por aresta (~1200 verts apos solidify), smart UV project
3. Adiciona GeometryNodes modifier apontando pro node group apendado
4. Configura sockets (Thickness 3mm, Wear 0.05, Displacement Strength 0.15, etc) via `mod[item.identifier]`
5. Apply modifier (freeze geometria)
6. Bake Cycles 32 samples × 2048² × 3 maps (DIFFUSE color + NORMAL tangent + ROUGHNESS)
7. Substitui o material complexo do asset por um Principled BSDF simples consumindo as 3 texturas bakeadas
8. Export GLB com `export_image_format='AUTO'` — texturas embedded

## Stack

- **Blender 5.1.2** headless via `blender --background --python script.py`
- **Cycles** para bake (Eevee nao bakeia)
- **Three.js 0.169** + GLTFLoader + OrbitControls + RoomEnvironment para a demo
- **GCS** (`didlu-imagestore/cardboard-experiment/v1/`) para hospedagem

## Estrutura

```
experiment-13-easy-cardboard/
├── assets/
│   └── easy-cardboard-3.1.blend       # asset comercial, gitignored
├── scripts/
│   ├── 01_inspect.py                  # inspeciona node groups/materials/images do asset
│   ├── 02_build_box.py                # pipeline principal
│   ├── run-blender.cmd                # wrapper Windows
│   ├── deploy-glb.cmd                 # upload GCS
│   ├── deploy-html.cmd
│   ├── fix-meta.cmd                   # content-type + cache
│   └── check-deploy.cmd
├── output/                             # gitignored (blends, GLBs, bakes)
│   ├── cardboard_box.glb               # 8MB GLB final
│   ├── cardboard_box.blend             # working file
│   ├── cardboard_color.png             # 2048² baked basecolor
│   ├── cardboard_normal.png            # 2048² baked normal
│   └── cardboard_roughness.png         # 2048² baked roughness
└── web/
    ├── index.html                      # demo Three.js
    └── cardboard_box.glb               # copia local pro deploy
```

## Decisoes do agente (todas autonomas)

| Decisao | Escolha | Razao |
|---|---|---|
| Versao Blender | 5.1.2 (3 instaladas) | 4.4 binario com problema; 5.1 funciona e abre o asset sem erros criticos |
| Dimensoes da caixa | 30×20×15cm | Proporcoes de shipping box padrao; mostra todos os lados ao spectator |
| Subdivisoes do cubo | 8 cuts/aresta | Smart Solidify 2.0 precisa de verts pra trabalhar; 8 da ~1200 verts apos solidify |
| Resolucao do bake | 2048² | Suficiente pra mostrar fibras e corrugacao sem GLB ficar enorme |
| Cycles samples | 32 | Bake nao precisa de muitos samples, surface eh quase-difusa |
| Wear / Displacement | 0.05 / 0.15 | Conservador — caixa nova reconhecivel. Primeiro tentei 0.25/1.0, deformou demais |
| Trocar material antes do export | Sim | Exporter glTF nao consegue exportar shader node group complexo; bake + Principled BSDF eh padrao da industria |

## Validacao

Screenshot via Playwright MCP confirmou:
- Caixa com geometria de shipping box reconhecivel
- Tampa, lateral lisa
- **Lateral menor mostrando o corrugado** (linhas verticais classicas) — exatamente como caixa real onde a quina revela a corrugacao
- Texturas baked carregam corretamente no GLB
- OrbitControls + auto-rotate quando idle

## Issues conhecidos

- `Failed to add relation "VFont -> Node"` no depsgraph eval — inofensivo, vem do subgrupo `FS Explanation` que tem texto de UI sem fonte alvo no append
- `Material.use_nodes` deprecated warning — Blender 6.0 vai remover, mas em 5.1 ainda funciona
- `cycles | ERROR Image file does not exist` no bake — falso positivo: a imagem eh criada in-memory e salva via `image.save()` depois, funciona corretamente
