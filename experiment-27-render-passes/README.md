# Experimento 27 — Render Passes / Light Groups / Compositing por camadas (headless)

## O que o experimento prova (que eu não sabia antes)

Que dá pra dirigir, **100% headless via Python**, o fluxo de **separar uma
cena renderizada do Blender em camadas independentes** (beauty, sombra, e a
contribuição isolada de cada luz) e consumir essas camadas como **PNGs
sobrepostos em 2D** numa página web — animando opacidade/blend pra fazer
efeito especial, **sem nenhuma engine 3D em runtime**, mantendo a qualidade
do Cycles.

## Etapa do fluxo Blender→consumer validada

- **Geração via feature sofisticada do Blender:** Cycles **Light Groups**
  (separação por luz) + **Shadow Catcher** (sombra isolada) + **compositor
  por nodes** (File Output roteando cada pass pra um arquivo).
- **Consumer:** página HTML/JS 2D empilhando os PNGs com `mix-blend-mode`
  (luzes somam via `screen`, sombra/AO multiplicam) e animando opacidade.

## Plugin/feature do Blender usado

- **Cycles Light Groups** (`view_layer.lightgroups` + `object.lightgroup`)
  — gera um pass `Combined_<grupo>` por grupo de luz. É o coração do
  "cada luz/cor numa imagem separada".
- **Shadow Catcher** (`object.is_shadow_catcher` + `film_transparent`) pra
  camada de sombra pura com alpha.
- **Compositor** (`CompositorNodeOutputFile`) pra rotear cada pass pra PNG.

## Saídas (pasta `passes/`)

| Arquivo | Conteúdo | Blend no viewer |
|---|---|---|
| `beauty.png` | imagem final completa | normal (base) |
| `shadow.png` | sombra isolada (shadow catcher, alpha) | multiply |
| `ao.png` | ambient occlusion (contato/profundidade) | multiply |
| `lg_window.png` | só a luz fria da janela | screen |
| `lg_lamp.png` | só o abajur quente | screen |
| `lg_ambient.png` | só o spot ambiente magenta | screen |

## Como rodar

```
blender --background --python build_and_render.py
```

Variáveis de ambiente opcionais (default = final):
`EXP27_RESX=1920 EXP27_RESY=1080 EXP27_SAMPLES=256`

O viewer abre `viewer/index.html` (carrega os PNGs de `../passes/`).

## Achados técnicos (Blender 4.3)

1. **Light group é atributo do OBJETO da luz**, não do data-block:
   `object.lightgroup = "grupo"` (não `light.lightgroup`). Os grupos têm
   que ser registrados antes em `view_layer.lightgroups.add(name=...)`.
   O pass aparece no compositor como socket `Combined_<grupo>`.
2. **O pass `Shadow` legado do Cycles não expõe socket utilizável** no
   compositor headless (vem `enabled=False` e some). A sombra isolada
   confiável sai via **Shadow Catcher numa segunda passada**: piso vira
   catcher, demais objetos ficam `visible_camera=False` mas
   `visible_shadow=True`, com `film_transparent=True`.
3. **AgX** (`view_settings.view_transform='AgX'`) domou os estouros das
   luzes fortes — sem ele a janela estourava pra branco puro.

## Honestidade técnica

- A cena é geometria de caixas (sem assets externos baixados) — o foco do
  experimento é o **pipeline de passes**, não modelagem. Os light groups e
  o shadow catcher funcionam idênticos com qualquer cena (assets CC0,
  geo nodes, etc.).
- O viewer **não recalcula nada em 3D**: só varia opacidade/blend dos PNGs
  que saíram do Blender. É exatamente o "2D com qualidade de Blender" pedido.
