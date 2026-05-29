"""
02_build_house.py — constroi a casa de bonecas (dollhouse) cortada ao meio.

Estrutura 100% gerada pelo Home Builder 5 (GeoNodeWall/GeoNodeCage via hb_lib).
A casa tem 3 andares; em cada andar a parede FRONTAL (face em Y=0, virada pra
camera) e OMITIDA -> esse e o "corte" do dollhouse: olhando de frente ve-se todos
os comodos abertos de uma vez.

Convencao de eixos:
  X = largura (0..W, esquerda->direita)
  Y = profundidade (0..D, frente->fundo). FRENTE = Y=0 (aberta). FUNDO = Y=D.
  Z = altura. Andares empilhados.

Layout (decisao do TD):
  Terreo (andar 0):  Sala de estar (esquerda) | Cozinha+jantar (direita)
  Andar 1:           Quarto de casal (esquerda) | Banheiro (direita)
  Andar 2:           Quarto infantil (esquerda) | Escritorio (direita)

Cada andar: paredes externas (fundo + 2 laterais, SEM frente) + 1 divisoria central
com vao de passagem. Piso e laje (teto do andar) extrudados do contorno.

Salva out/dollhouse_structure.blend com metadados dos comodos (bounding boxes em
mundo) em out/rooms.json, pro passo de mobiliar saber onde por cada movel.

Roda:
  blender --background --python 02_build_house.py
"""
import bpy
import sys
import os
import json
import math
from mathutils import Vector

sys.path.append(os.path.dirname(__file__))
import hb_lib

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "out")
OUT_DIR = os.path.abspath(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)


def log(*a):
    print("[house]", *a, flush=True)


# ---------------------------------------------------------------------------
# parametros da casa
# ---------------------------------------------------------------------------
W = 8.0          # largura total (X)
D = 5.0          # profundidade total (Y)
WALL_T = 0.12    # espessura parede
SLAB = 0.18      # espessura da laje/piso
CEIL_H = 2.55    # pe-direito (piso ate base da laje)
FLOOR_PITCH = CEIL_H + SLAB   # altura de 1 andar completo
N_FLOORS = 3
DIV_X = 4.5      # x da divisoria central (sala maior que cozinha)
DOOR_W = 0.95
DOOR_H = 2.05

hb_lib.reset_scene()
log(f"casa {W}x{D}m, {N_FLOORS} andares, pitch {FLOOR_PITCH:.2f}m")

# guarda info dos comodos pra etapa de mobiliar
rooms = []
all_walls = []


def floor_z(i):
    return i * FLOOR_PITCH


def build_floor(idx, left_name, right_name):
    """Constroi 1 andar: 3 paredes externas (fundo+laterais, SEM frente) +
    divisoria central com vao. Piso embaixo, laje em cima."""
    z0 = floor_z(idx)
    h = CEIL_H + SLAB  # paredes vao ate a base da proxima laje
    pre = f"F{idx}"

    # --- paredes externas SEM a frente (Y=0) ---
    # parede fundo: de (0,D) a (W,D)  -> ao longo de +X em Y=D
    wb = hb_lib.new_wall(f"{pre}_back", W, (0, D, z0), 0, WALL_T, h)
    # parede esquerda: de (0,0) a (0,D) -> ao longo de +Y em X=0 (angulo 90)
    wl = hb_lib.new_wall(f"{pre}_left", D, (0, 0, z0), 90, WALL_T, h)
    # parede direita: de (W,0) a (W,D) -> ao longo de +Y em X=W (angulo 90)
    wr = hb_lib.new_wall(f"{pre}_right", D, (W, 0, z0), 90, WALL_T, h)
    # divisoria central: de (DIV_X,0) a (DIV_X,D) -> ao longo de +Y (angulo 90)
    wd = hb_lib.new_wall(f"{pre}_div", D, (DIV_X, 0, z0), 90, WALL_T, h)
    # vao de passagem na divisoria, perto do fundo
    hb_lib.add_opening(wd, 'DOOR', offset_x=D - 1.4, width=DOOR_W, height=DOOR_H, z=0.0)

    floor_walls = [wb, wl, wr, wd]
    all_walls.extend(floor_walls)

    # --- piso do andar (laje embaixo) ---
    contour = [(0, 0), (W, 0), (W, D), (0, D)]
    flr = hb_lib.add_ceiling(contour, ceiling_height=z0 - SLAB, slab=SLAB, name=f"{pre}_floor")
    flr['IS_FLOOR_SLAB'] = True

    # --- laje/teto do andar (em cima) ---
    # so o ultimo andar ganha teto fechado por cima; andares intermediarios a laje
    # ja e o piso do de cima. Pra simplicidade: cada andar poe sua propria laje em
    # cima, que serve de teto desse andar.
    ceil = hb_lib.add_ceiling(contour, ceiling_height=z0 + CEIL_H, slab=SLAB, name=f"{pre}_ceil")

    # --- registra os 2 comodos ---
    # comodo esquerdo: x 0..DIV_X, comodo direito: x DIV_X..W. y 0..D. z0..z0+CEIL_H
    rooms.append({
        "floor": idx, "name": left_name, "side": "left",
        "x0": WALL_T, "x1": DIV_X - WALL_T / 2,
        "y0": WALL_T, "y1": D - WALL_T,
        "z": z0,
        "cx": (WALL_T + DIV_X - WALL_T / 2) / 2,
        "cy": (WALL_T + D - WALL_T) / 2,
        "w": (DIV_X - WALL_T / 2) - WALL_T,
        "d": (D - WALL_T) - WALL_T,
    })
    rooms.append({
        "floor": idx, "name": right_name, "side": "right",
        "x0": DIV_X + WALL_T / 2, "x1": W - WALL_T,
        "y0": WALL_T, "y1": D - WALL_T,
        "z": z0,
        "cx": (DIV_X + WALL_T / 2 + W - WALL_T) / 2,
        "cy": (WALL_T + D - WALL_T) / 2,
        "w": (W - WALL_T) - (DIV_X + WALL_T / 2),
        "d": (D - WALL_T) - WALL_T,
    })
    log(f"andar {idx}: {left_name} | {right_name} (z0={z0:.2f})")


# ---------------------------------------------------------------------------
# constroi os 3 andares
# ---------------------------------------------------------------------------
build_floor(0, "Sala de estar", "Cozinha")
build_floor(1, "Quarto de casal", "Banheiro")
build_floor(2, "Quarto infantil", "Escritorio")

# janela no fundo de cada comodo (na parede de fundo Y=D), pra dar ar de casa
for idx in range(N_FLOORS):
    z0 = floor_z(idx)
    # acha a parede de fundo desse andar
    back = next(w for w in all_walls if w.obj.name.startswith(f"F{idx}_back"))
    # 2 janelas: uma em cada comodo
    hb_lib.add_opening(back, 'WINDOW', offset_x=2.0, width=1.1, height=1.1, z=1.0)
    hb_lib.add_opening(back, 'WINDOW', offset_x=6.0, width=1.1, height=1.1, z=1.0)

log(f"total paredes: {len(all_walls)} | comodos: {len(rooms)}")

# ---------------------------------------------------------------------------
# salva metadados e o .blend
# ---------------------------------------------------------------------------
meta = {
    "W": W, "D": D, "wall_t": WALL_T, "slab": SLAB,
    "ceil_h": CEIL_H, "floor_pitch": FLOOR_PITCH, "n_floors": N_FLOORS,
    "div_x": DIV_X,
    "rooms": rooms,
}
with open(os.path.join(OUT_DIR, "rooms.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)
log("rooms.json salvo")

out_blend = os.path.join(OUT_DIR, "dollhouse_structure.blend")
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
log("saved:", out_blend)
log("DONE")
