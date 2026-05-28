# Experimento 19 — Casa multi-andar mobiliada via MCP (cena viva)

Primeira sessão usando **MCP do Blender** como modo de trabalho stateful, em vez do
loop headless `blender --background --python`. O Blender fica aberto, o agente envia
comandos via `mcp__blender__execute_blender_code` e o user **vê tudo ao vivo na tela**.

## Goal

Provar três coisas:

1. **A `hb_lib.py` do exp 18 funciona idêntica no MCP** — toda automação headless é
   reutilizável dentro da cena viva, sem reescrever nada.
2. **Construção incremental stateful** — casa multi-andar montada em etapas (térreo
   → laje → 1º andar → teto → escada → cozinha), salvando `.blend` a cada etapa.
3. **Mobília sofisticada via Home Builder 5** — não só paredes/portas/janelas, mas a
   API real de **cabinets paramétricos** (BaseCabinet, UpperCabinet, RefrigeratorCabinet).

## O que foi construído

Casa retangular 8m × 6m, 2 andares, pé-direito 2.7m (térreo) + 2.6m (1º andar):

| Componente | Como | Plugin |
|---|---|---|
| Paredes externas térreo + 1º andar | `hb_lib.build_room_loop` (mitra automática) | Home Builder 5 |
| Divisórias internas (banheiro, corredor) | `hb_lib.new_wall` | Home Builder 5 |
| Portas e janelas furadas de verdade | `hb_lib.add_opening` (boolean DIFFERENCE) | Home Builder 5 |
| Piso do térreo | `hb_lib.add_floor` (ngon) | Home Builder 5 |
| Laje entre andares | `hb_lib.add_ceiling` (extrusão) | Home Builder 5 |
| Teto da casa | `hb_lib.add_ceiling` | Home Builder 5 |
| Escada paramétrica reta (14 degraus, 2.82m) | `bpy.ops.mesh.archimesh_stairs` | **Archimesh** (built-in) |
| Furo na laje pra escada passar | Cube boolean cutter aplicado | (primitivo) |
| Cozinha: 4 base cabinets + 1 geladeira + 4 upper cabinets | `types_frameless.BaseCabinet/Upper/Refrigerator().create()` | Home Builder 5 |

## Decisões honestas que tomei sozinho

1. **Escada via Archimesh** porque o Home Builder 5 **não tem escada nativa**
   (operators: `walls, doors_windows, rooms, layouts, details, ops_obstacles, export`).
   A `stair_lib.py` do exp 6 é majoritariamente bmesh feito-a-mão — **proibido** pelas
   regras desta workspace. Archimesh é built-in oficial e tem `archimesh_stairs`
   paramétrico real, então é o caminho correto.

2. **Refiz janelas com folga de canto** porque a primeira tentativa colocou janelas
   a < 1m do canto, e o cage cutter da janela se sobrepôs ao cage cutter da mitra
   (boolean DIFFERENCE compete, gera "miolo no meio do vão"). Recálculo:
   `offset >= 1.2m do canto` resolveu.

3. **Furo na laje feito com cubo primitivo + boolean DIFFERENCE** porque nem Home
   Builder nem Archimesh têm operador "abrir vão em laje". Isso é primitivo, não é
   plugin sofisticado — mas é **incontornável**, registrado como caveat.

4. **Cozinha em linha reta**, não em L corner — primeiro fluxo, sem testar
   `CornerCabinet`/`DiagonalCornerBaseCabinet`. O Home Builder tem essas classes
   prontas; ficou pra próximo experimento.

## API que foi descoberta no Home Builder 5 (não estava no exp 18)

O addon distribui **3 product libraries**: `closets/`, `face_frame/`, `frameless/`.
Cada uma tem operadores próprios: `ops_cabinet`, `ops_appliance`, `ops_countertop`,
`ops_crown`, `ops_finished_ends`, `ops_defaults`.

A classe-base é `Cabinet(GeoNodeCage)` em `types_frameless.py`, exatamente o mesmo
padrão de `GeoNodeWall(GeoNodeObject)`. Para criar um cabinet sem ter que rodar o
operator modal `hb_frameless.place_cabinet`:

```python
import importlib
tf = importlib.import_module("bl_ext.blender_org.home_builder_5.product_libraries.frameless.types_frameless")

bc = tf.BaseCabinet()
bc.width = 0.60   # metros (default 0.9144 = 36in)
bc.depth = 0.60   # metros
bc.create("Kitchen_Base_1")
bc.obj.location = (x, y, 0)
bc.obj.rotation_euler.z = math.radians(180)  # parede de fundo
```

Defaults default americanos (36in, 24in depth). Cada cabinet gera ~20 objetos filhos
(carcassa, portas via `Doors()`, gavetas via `Drawer()`, puxadores `GeoNodeHardware`).
Tudo Geometry Nodes — fiel ao princípio de **plugin sofisticado faz o trabalho**.

Classes prontas descobertas: `BaseCabinet`, `TallCabinet`, `UpperCabinet`,
`RefrigeratorCabinet`, `LapDrawerCabinet`, `CornerCabinet`, `DiagonalCorner*`,
`PieCutCorner*` (3 variantes Base/Tall/Upper cada).

## Caveats honestos

1. **Render externo da casa saiu preto** — sem material e sem ambiente HDR, mesmo
   com luz pontual de 5000W. Não afina porque o teste é construção/automação, não
   apresentação. Quem quiser ver: abrir o `.blend` no Blender.
2. **Algumas janelas mostram listras dentro no viewport** — é o cage cutter wireframe
   visível (`display_type='WIRE'`). No render some.
3. **Casa não está totalmente "habitável"** — faltam: corrimão na escada (Archimesh
   tem a opção `back=True` que coloca espelho, mas não corrimão lateral), portas
   reais dos vãos (vão fica aberto), peças do banheiro (vaso, pia), camas nos
   quartos.

## Headless vs MCP — conclusão da sessão

**Headless (`blender --background --python script.py`):**
- ✅ Reprodutível 100% (mesmo input = mesmo output)
- ✅ Batch ilimitado, paralelizável
- ✅ Sem dependência de GUI / processo persistente
- ❌ Stateless — cada script abre, faz, fecha, exporta
- ❌ Sem feedback visual durante execução (o user só vê o .blend salvo)
- ❌ Debug ruim de erros geométricos sem screenshot

**MCP (Blender GUI aberto + servidor escutando):**
- ✅ Stateful — cena persiste entre comandos, dá pra construir incremental
- ✅ Feedback visual imediato (`get_viewport_screenshot`)
- ✅ Debug rápido — vê o resultado, ajusta, vê de novo
- ✅ User acompanha em tempo real (sente "presença" do agente)
- ❌ Exige Blender GUI aberto com addon habilitado (1 ação manual do user na vida)
- ❌ Não paraleliza (1 cena ao vivo de cada vez)
- ❌ Não é reprodutível "automatico" — depende do estado da cena no momento

**Quando usar cada um:**
- **MCP**: desenvolvimento iterativo, descoberta de API, ajuste fino, demo ao vivo
- **Headless**: pipelines de produção, batch (N casas, N variações), CI/CD

A `hb_lib.py` rodou idêntica nos dois mundos. Não foi preciso adaptar **nada** — o
mesmo `new_wall(name, length, location, angle_deg)` funciona via `bpy.ops`-headless
ou via `execute_blender_code`-MCP. Esta é a observação técnica mais valiosa da
sessão: **código `bpy` puro é portável entre os dois modos**, MCP é só o transporte.

## Arquivos

- `out/blends/01_terreo.blend` — só térreo
- `out/blends/02_dois_andares.blend` — + laje + 1º andar + teto
- `out/blends/03_com_escada.blend` — + escada + furo na laje
- `out/blends/04_com_cozinha.blend` — + cozinha completa
- `out/blends/05_final.blend` — versão final consolidada
- `out/renders/casa_final.png` — render Eevee (saiu escuro, ver caveat)
