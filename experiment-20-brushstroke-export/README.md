# Experimento 20 — Brushstroke Tools no GLB/FBX

**Pergunta técnica do user:** "Se eu exportar GLB/FBX, os brushes saem? Imagino que se saem, vão sair como estruturas na superfície dos modelos."

**Resposta:** SIM, saem como geometria real na superfície. Com uma pegadinha:
o exportador glTF do Blender **ignora** o tipo `CURVES`, e o brushstroke
object é criado como `CURVES` (hair_curves) por default. Precisa **converter
para MESH** antes de exportar.

## Plugin

[Brushstroke Tools 1.2.1](https://extensions.blender.org/add-ons/brushstroke-tools/)
do Blender Studio (Simon Thommes). Free, oficial, instalável via
`bpy.ops.extensions.package_install(pkg_id="brushstroke_tools")`.

Tagline do addon: "Brushstroke painting tools" — usado em curtas Blender Studio.
Tags: `Paint, Geometry Nodes, Material`.

## Arquitetura por baixo

`brushstroke_tools.new_brushstrokes(method='SURFACE_FILL')` cria:

1. **Surface object** = a mesh target (sua casa, parede, etc.) — precisa ter
   **UV map ativa** (`uv_layers.active_index >= 0`)
2. **Brushstrokes object** (`type='CURVES'`) com 3 modifiers GeoNodes
   encadeados: `Surface Input → Masking → Brushstrokes`. Esse modifier final
   instancia milhares de strips/planos curvos pela superfície
3. **Flow object** (auxiliar, define a direção das pinceladas via modifier
   `.brushstroke_tools.pre_processing`)

**Sockets principais do modifier 'Brushstrokes' (do `estimate_dimensions`):**
- `Socket_7` = density
- `Socket_11` = length
- `Socket_13` = width

## Pipeline executada (terreo da casa do exp 19)

1. **Aplicar modifiers nas superfícies target** — paredes externas do térreo
   (4) + piso + laje. As paredes do Home Builder são GeoNodes vivos com 0
   verts; precisam ser bakeadas pra mesh real
2. **Smart UV project** em cada uma — Brushstroke exige UV ativa
3. **Ativar UV explicitamente** (`uv_layers.active_index = 0`) — gotcha:
   `smart_project` cria UV mas não seta como ativa
4. **`new_brushstrokes`** em cada uma — gera 6 brushstroke objects + 6 flow
   objects (12 novos)
5. **Convert para MESH** (`bpy.ops.object.convert(target='MESH')`) — bakea o
   GeoNodes em mesh real
6. **Export GLB com `use_selection=True, export_apply=True`**

## Números

| Cenário | Tamanho GLB | Verts | Tris | Meshes |
|---|---|---|---|---|
| Térreo SEM brushstrokes | 17 KB | 364 | 254 | 6 |
| Térreo COM brushstrokes (convertido) | **5.61 MB** | **66.325** | **84.014** | 12 |

**Razão:** 330× maior em tamanho, 182× mais verts, 331× mais tris.

## Gotchas descobertos

1. **UV map criada por `smart_project` vem desativada** (`active_index=-1`).
   Brushstroke Tools rejeita com erro `"Surface Object needs an available UV
   Map"` mesmo tendo UV listada. Fix: setar `data.uv_layers.active_index = 0`
2. **`bpy.ops.object.select_all` falha em contexto não-OBJECT** com erro
   críptico `"poll() failed, context is incorrect"`. Sempre garantir
   `bpy.ops.object.mode_set(mode='OBJECT')` antes
3. **Exportador glTF ignora `type='CURVES'`** — log do export lista só as
   primitivas MESH. Sem o convert pra MESH, o GLB sai sem nenhuma pincelada
   apesar do export aparentemente ter sucesso (mesmo tamanho do GLB sem
   brushstrokes — 17.896 bytes nos dois)
4. **`to_mesh()` falha em hair_curves** (`"Object does not have geometry
   data"`). É necessário usar `convert(target='MESH')` que faz o trabalho

## Estética — caveat honesto

Apliquei com **preset default** sem ajustar style. Resultado: pinceladas
caem como "ninho" branco cobrindo a casa toda (visual no viewer). Bonito
artisticamente em contextos certos (curtas Blender Studio), mas não é o
que normalmente se espera de "pintura à mão na arquitetura".

Não afinei porque o objetivo do experimento era a **pergunta técnica
(sai no GLB?)**, não a estética. Pra produzir visual usável, é preciso:
- Carregar styles dos assets do addon (`assets/styles/`)
- Configurar density/length/width pra escala da superfície (defaults vêm
  de `estimate_dimensions` com bbox total — fica ruim em paredes grandes
  e planas)
- Configurar material (default fica branco/sem cor)
- Ajustar flow direction (direção das pinceladas)

## Arquivos

- `out/glb/terreo_brushstroke_NO_apply.glb` — sem brushstrokes (17 KB)
- `out/glb/terreo_brushstroke_CONVERTED.glb` — com brushstrokes convertidos pra MESH (5.6 MB)
- `out/scene_with_brushstrokes.blend` — cena Blender pronta pra reabrir
- `out/renders/brushstroke_*.png` — renders Eevee do efeito no Blender
- `viewer/index.html` — viewer Three.js comparativo

## Hospedado

https://st.did.lu/blender-exp20-brushstroke/v1/index.html
