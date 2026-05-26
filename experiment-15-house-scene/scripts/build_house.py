"""
Monta a casa completa: shell + 4 comodos mobiliados + luz + camera.
Roda no Blender headless:
    blender --background --python build_house.py -- [--no-render]

Salva o .blend em output/house.blend.

PLANTA (metros, Z=up, origem no centro da casa):
  X de -6.5 a +6.5  (13m largura)
  Y de -4.5 a +4.5  (9m profundidade)
  pe-direito 2.8m

  Y>0 (fundo)   |  QUARTO (X<0)        | ESCRITORIO (X>0)
  --------------+----------------------+--------------------
  Y<0 (frente)  |  SALA DE ESTAR (X<0) | COZINHA/JANTAR (X>0)

Parede divisoria em X=0 (separa esq/dir) e em Y=0 (separa frente/fundo),
com vaos de passagem.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import scene_lib as L

EXP = L.EXP
OUT = EXP / "output"

# ----- dimensoes da casa
HX, HY = 6.5, 4.5     # meia-largura, meia-profundidade
WALL_H = 2.8
WALL_T = 0.12

bpy.ops.wm.read_factory_settings(use_empty=True)

# ============================================================ SHELL
floor_mat = L.pbr_material(
    "Floor",
    "assets/_textures/wood_floor/Diffuse.jpg",
    normal="assets/_textures/wood_floor/nor_gl.jpg",
    rough="assets/_textures/wood_floor/Rough.jpg",
    scale_uv=6.0,
)
wall_mat = L.pbr_material(
    "Wall",
    "assets/_textures/beige_wall_001/Diffuse.jpg",
    normal="assets/_textures/beige_wall_001/nor_gl.jpg",
    rough="assets/_textures/beige_wall_001/Rough.jpg",
    scale_uv=4.0,
)

# piso
L._make_box("Floor", (HX * 2, HY * 2, 0.05), (0, 0, -0.025), floor_mat)

# paredes externas (4)
L._make_box("Wall_N", (HX * 2, WALL_T, WALL_H), (0, HY, WALL_H / 2), wall_mat)
L._make_box("Wall_S", (HX * 2, WALL_T, WALL_H), (0, -HY, WALL_H / 2), wall_mat)
L._make_box("Wall_E", (WALL_T, HY * 2, WALL_H), (HX, 0, WALL_H / 2), wall_mat)
L._make_box("Wall_W", (WALL_T, HY * 2, WALL_H), (-HX, 0, WALL_H / 2), wall_mat)

# divisoria central X=0 com vao no meio (2 segmentos)
seg = (HY - 0.9)  # deixa vao de 1.8m no centro
L._make_box("Div_X_N", (WALL_T, seg, WALL_H), (0, HY - seg / 2, WALL_H / 2), wall_mat)
L._make_box("Div_X_S", (WALL_T, seg, WALL_H), (0, -HY + seg / 2, WALL_H / 2), wall_mat)
# divisoria central Y=0 com vao (2 segmentos)
segx = (HX - 1.0)
L._make_box("Div_Y_W", (segx, WALL_T, WALL_H), (-HX + segx / 2, 0, WALL_H / 2), wall_mat)
L._make_box("Div_Y_E", (segx, WALL_T, WALL_H), (HX - segx / 2, 0, WALL_H / 2), wall_mat)


# ============================================================ helper
def A(slug):
    return L.import_gltf(slug)


# ============================================================ SALA DE ESTAR  (X<0, Y<0)
# sofa encostado na parede W, virado pro centro do comodo (+X)
sofa = A("Sofa_01")
L.place(sofa, x=-5.2, y=-2.6, rot_z_deg=90)          # frente p/ +X
# TV em cima da console, encostada na divisoria X=0, de frente pro sofa (-X)
console = A("ClassicConsole_01")
L.place(console, x=-1.0, y=-2.6, rot_z_deg=-90)
tv = A("Television_01")
L.place_on(tv, console, rot_z_deg=180)               # tela p/ -X (pro sofa)
# poltrona em angulo
arm = A("ArmChair_01")
L.place(arm, x=-3.2, y=-0.9, rot_z_deg=200)
# mesa de centro entre sofa e tv
coffee = A("CoffeeTable_01")
L.place(coffee, x=-3.2, y=-2.6, rot_z_deg=90)
# estante de livros no canto SW
shelf = A("wooden_bookshelf_worn")
L.place(shelf, x=-5.6, y=-4.0, rot_z_deg=0)
# planta no canto
plant = A("potted_plant_01")
L.place(plant, x=-1.0, y=-4.0)
# vaso decorando a mesa de centro
vase = A("brass_vase_04")
L.place_on(vase, coffee, target_height=0.22)

# ============================================================ COZINHA / JANTAR (X>0, Y<0)
# mesa redonda central com cadeiras ao redor
table = A("round_wooden_table_01")
L.place(table, x=3.2, y=-2.6, rot_z_deg=0)
chairs = [("dining_chair_02", 0), ("dining_chair_02", 90),
          ("dining_chair_02", 180), ("dining_chair_02", 270)]
import math
for slug, ang in chairs:
    c = A(slug)
    r = 0.95
    cx = 3.2 + r * math.sin(math.radians(ang))
    cy = -2.6 - r * math.cos(math.radians(ang))
    L.place(c, x=cx, y=cy, rot_z_deg=ang + 180)      # encosto p/ fora
# louças na mesa
tea = A("tea_set_01")
L.place_on(tea, table)
# fogao encostado na parede E
stove = A("electric_stove")
L.place(stove, x=5.7, y=-1.2, rot_z_deg=-90)
# estante metalica no canto SE (asset gigante -> normaliza altura)
msh = A("steel_frame_shelves_01")
L.place(msh, x=5.5, y=-3.8, rot_z_deg=0, target_height=2.0)
# panela e tigela em cima da estante metalica
pot = A("pot_enamel_01")
L.place_on(pot, msh, x=5.5, y=-3.8)

# ============================================================ QUARTO (X<0, Y>0)
# cama encostada na parede N
bed = A("GothicBed_01")
L.place(bed, x=-4.5, y=3.4, rot_z_deg=0)
# criado-mudo ao lado da cama
night = A("ClassicNightstand_01")
L.place(night, x=-2.6, y=3.8, rot_z_deg=0)
# abajur no criado-mudo
lamp = A("desk_lamp_arm_01")
L.place_on(lamp, night)
# comoda/armario encostado na parede W
cab = A("vintage_cabinet_01")
L.place(cab, x=-5.6, y=1.2, rot_z_deg=90, target_height=2.0)
# planta pequena no canto
plant2 = A("potted_plant_04")
L.place(plant2, x=-1.0, y=4.0)

# ============================================================ ESCRITORIO (X>0, Y>0)
# escrivaninha encostada na parede E
desk = A("metal_office_desk")
L.place(desk, x=4.9, y=1.4, rot_z_deg=-90)
# cadeira de frente pra escrivaninha
schair = A("SchoolChair_01")
L.place(schair, x=3.6, y=1.4, rot_z_deg=90)
# abajur de mesa na escrivaninha
desklamp = A("desk_lamp_arm_01")
L.place_on(desklamp, desk, x=4.9, y=0.7)
# garrafas de vinho decoram a escrivaninha
wine = A("wine_bottles_01")
L.place_on(wine, desk, x=4.9, y=2.0)
# poltrona/sofa de leitura no canto NW do escritorio
sofa2 = A("sofa_02")
L.place(sofa2, x=2.5, y=3.6, rot_z_deg=180)

# ============================================================ LUMINARIAS DE TETO
chand = A("Chandelier_01")
L.place(chand, x=-3.2, y=-2.6, on_floor=False, z_offset=WALL_H - 0.8)
ceil = A("modern_ceiling_lamp_01")
L.place(ceil, x=3.2, y=-2.6, on_floor=False, z_offset=WALL_H - 0.95)


# ============================================================ LUZ + CAMERA + RENDER
L.world_background(color=(0.95, 0.95, 0.97, 1.0), strength=0.6)
L.add_sun(energy=2.0, angle=(0.6, 0.1, 0.9))
# luz de area por comodo (preenchimento)
for (lx, ly) in [(-3.2, -2.6), (3.2, -2.6), (-3.2, 2.6), (3.2, 2.6)]:
    L.add_area_light(f"Fill_{lx}_{ly}", (lx, ly, 2.6), size=2.2, energy=120)

L.setup_render(samples=128, res=(1700, 1080))

# salva o .blend
OUT.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "house.blend"))
print(f"\nCena salva em {OUT / 'house.blend'}")

# renders multiplos (so se nao passar --no-render)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--no-render" not in argv:
    cams = {
        "overview_sw": ((-11, -10, 9), (0, 0, 0.8), 28),
        "overview_se": ((11, -10, 9), (0, 0, 0.8), 28),
        "living": ((-2.5, 0.5, 2.3), (-4.5, -3.0, 0.6), 30),
        "kitchen": ((1.5, 0.3, 2.3), (4.5, -3.2, 0.6), 30),
        "bedroom": ((-1.5, 0.5, 2.3), (-4.8, 3.5, 0.7), 30),
        "office": ((1.0, 0.3, 2.3), (4.8, 2.0, 0.7), 30),
    }
    rdir = OUT / "renders"
    rdir.mkdir(exist_ok=True)
    for name, (loc, look, lens) in cams.items():
        L.add_camera(loc, look, lens=lens)
        L.render_to(rdir / f"{name}.png")
        print(f"render {name} OK")
print("DONE")
