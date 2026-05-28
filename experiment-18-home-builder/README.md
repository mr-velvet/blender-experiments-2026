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
- `Show Cage=False` -> 0 verts -> boolean nao tem o que subtrair. Usar `True` + `hide_render`.
- `GeoNodeCage` cresce de `(0,0,0)` ate `(Dim X, Dim Y, Dim Z)` (origem num canto), nao centrado.
- Blender 5.1: engine Eevee e `BLENDER_EEVEE`, nao `BLENDER_EEVEE_NEXT`. Addon exige Blender 5.0+.

## Caveat honesto

Na casa hexagonal, algumas janelas posicionadas perto do canto sairam com recorte parcial/em-L
(o offset colidiu com a mitra do canto). O conceito de abertura via boolean esta validado nas
demais casas; ajustar o offset das janelas resolveria.

## Saidas (gitignored em `out/`)

4 casas x 3 vistas (render 3/4 Eevee, estrutura solid Workbench, planta top-ortografico),
720px, sem textura. `.blend` de cada casa em `out/blends/`.
