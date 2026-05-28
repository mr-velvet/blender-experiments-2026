# Experimento 18 — Home Builder 5 dirigido headless

Addon **Home Builder 5** (AndrewPeel, free, open-source — extensions.blender.org): desenha
paredes, portas, janelas e salas parametricas para design de interiores/arquitetura.

**Goal:** dado apenas um print do addon, encontra-lo, instalar gratis, dirigir via Python
headless, gerar varias casas, tirar prints e renderizar em baixa resolucao sem textura.
Teste de autonomia.

## A etapa critica

Os operadores oficiais do addon (`home_builder_walls.draw_walls`, `place_door`, etc.) sao
**100% modais** — dependem de cliques e movimento de mouse na viewport. Nao rodam headless.

A solucao foi dirigir as **classes internas** que esses operadores usam por baixo:
`hb_types.GeoNodeWall` e `hb_types.GeoNodeCage`. Toda a geometria continua vindo do
Geometry Nodes do addon — nada e recriado a mao.

## Scripts

| Script | Funcao |
|---|---|
| `01_install.py` | instala + habilita o addon headless via extensions; verifica import |
| `02_inspect.py` | lista os inputs reais de `GeoNodeWall`/`GeoNodeCage` + props default |
| `04_debug_cage.py` | descobriu que `Show Cage=False` -> 0 verts (boolean nao corta) |
| `hb_lib.py` | biblioteca: `new_wall`, `add_opening`, `build_room_loop` (anel + mitra) |
| `03_build_houses.py` | gera as 4 casas, salva .blend, renderiza 3 vistas cada |

```
blender --background --python scripts/03_build_houses.py            # todas
blender --background --python scripts/03_build_houses.py -- --house 01_rect
```

## Receita

**Parede:**
```python
w = GeoNodeWall(); w.create("Wall")
w.set_input('Length', L); w.set_input('Height', H); w.set_input('Thickness', T)
w.obj.location = (x, y, 0); w.obj.rotation_euler.z = radians(angle)
# canto: set_input('Left Angle' / 'Right Angle', turn/2)
```

**Abertura (porta/janela):**
```python
cage = GeoNodeCage(); cage.create("Door")
cage.set_input('Dim X', width); cage.set_input('Dim Y', wall_t+folga); cage.set_input('Dim Z', height)
cage.set_input('Show Cage', True)   # False gera 0 verts -> boolean nao corta
cage.obj.parent = wall.obj
cage.obj.location = (offset_x, -(wall_t+folga)/2, z)   # cage cresce de um canto; centraliza Y
mod = wall.obj.modifiers.new(..., type='BOOLEAN'); mod.operation='DIFFERENCE'; mod.object=cage.obj
cage.obj.hide_render = True          # cutter invisivel no render
```

## Gotchas

- `read_factory_settings(use_empty=True)` desregistra o addon (a PropertyGroup `obj.home_builder`
  some). Limpar a cena deletando objetos, **nao** resetando prefs.
- `Show Cage=False` -> 0 verts. NAO setar a prop: no default o node ja gera cubo solido de 8 verts
  (cutter). Esconder do render com `hide_render`. (Ver fix do furo abaixo.)
- `GeoNodeCage` E a parede crescem de `(0,0,0)` ate `(Dim,Dim,Dim)` (origem num canto), nao centrado.
  A parede vai de y=0 a y=+Thickness — posicionar o cutter assumindo centro em Y fura so metade.
- Blender 5.1: engine Eevee e `BLENDER_EEVEE`, nao `BLENDER_EEVEE_NEXT`. Addon exige Blender 5.0+.

## Fix do furo passante (rodada 2)

**Sintoma:** as aberturas apareciam como retangulos rasos chanfrados, nao buracos vazados.

**Causa:** o cage cortador era posicionado com `location.y = -cut_y/2`, supondo a parede centrada
em Y. Ela **nao e** — a parede do Home Builder cresce de `y=0` ate `y=+Thickness`. O cage tambem
cresce de `(0,0,0)`. Com o offset errado o cutter atravessava so metade da espessura, e o boolean
comia uma fatia rasa em vez de furar de lado a lado.

**Fix** (`hb_lib.add_opening`): `Dim Y = Thickness + folga` e `location.y = -folga/2` (cubo cortador
vai de `-folga/2` a `Thickness+folga/2`, cobrindo `0..Thickness` inteiro). Validado por raycast
headless (`06_verify_fix.py`): no centro do vao o raio nao bate em nada (vazio); numa parede cheia
bate 2x (entra/sai). Tambem: NAO setar `Show Cage=True` — o default ja gera o cubo solido de 8 verts
que serve de cutter (corrige o gotcha antigo que dizia o contrario).

## Modelo navegavel em 1a pessoa (rodada 2)

`07_export_glb.py` exporta cada casa como GLB com os furos **aplicados na malha** (converte
GeoNodeWall + boolean em mesh real via `object.convert(target='MESH')`) e **remove os cages** antes
de exportar. GLB Y-up, pronto pra three.js/Godot/Unity (60-102 verts/casa).

`viewer/index.html` carrega o GLB num viewer Three.js com camera de 1a pessoa (olho a 1.6m).
Walkthrough capturado via Playwright em `out/walkthrough/`: de fora vendo os vaos passantes,
de dentro olhando paredes/janelas, e a porta interna da casa de 2 comodos ligando os ambientes.

## Caveat honesto

Sem teto (proposito: prova de conceito sem textura, paredes vazadas pra navegar). Na casa hexagonal,
janelas perto do canto ainda podem recortar parcial pela colisao com a mitra (ajuste de offset resolve).

## Saidas (gitignored em `out/`)

4 casas x 3 vistas (render 3/4 Eevee, estrutura solid Workbench, planta top-ortografico), 720px,
sem textura. `.blend` em `out/blends/`, GLB em `out/glb/`, walkthrough 1a pessoa em `out/walkthrough/`.
