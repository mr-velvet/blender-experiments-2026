"""Manipulacoes estruturais do Home Builder 5 (continuacao do exp 18).

Testa 4 coisas que o user pediu, todas via blender --background --python:

  A. PAREDES GROSSAS    - Thickness alto (0.45m). Furos de porta/janela tem que
                          atravessar a espessura toda mesmo grossa.
  B. CASA LONGA         - corredor comprido com varios quartos longos em fileira,
                          divisorias internas com portas de passagem.
  C. CORTE DOLLHOUSE    - gera a casa longa fechada e DEPOIS remove a parede de um
                          lado inteiro (manipulacao postuma) -> estrutura aberta.
  D. TETO PARAMETRIZAVEL- mesma planta renderizada com pe-direito BAIXO (2.4m) e
                          ALTO (3.4m). Teto = laje solida posta apos gerar as paredes.

Reusa camera/luz/material/render do 03_build_houses.py.
"""
import bpy, sys, os, math
from mathutils import Vector

sys.path.append(os.path.dirname(__file__))
import hb_lib
import importlib
importlib.reload(hb_lib)

# carrega o 03 pra reusar camera/luz/render
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bh", os.path.join(os.path.dirname(__file__), "03_build_houses.py"))
bh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bh)

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
RENDERS = os.path.join(OUT, "renders")
BLENDS = os.path.join(OUT, "blends")
GLB = os.path.join(OUT, "glb")
for d in (RENDERS, BLENDS, GLB):
    os.makedirs(d, exist_ok=True)

THICK_FAT = 0.45   # parede grossa


# ---------------- A. paredes grossas ----------------
def house_fat_walls():
    """Casa 6x4 com paredes BEM grossas (0.45m). Furos atravessam a espessura toda."""
    pts = [(0, 0), (6, 0), (6, 4), (0, 4)]
    walls = hb_lib.build_room_loop(pts, name="fat", thickness=THICK_FAT)
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=2.5)
    hb_lib.add_opening(walls[0], 'WINDOW', offset_x=0.8, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[2], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    return pts


# ---------------- B. casa longa com comodos longos ----------------
def _long_house_walls(thickness=hb_lib.WALL_THICKNESS, height=hb_lib.WALL_HEIGHT):
    """Constroi o esqueleto da casa longa e retorna (pts, walls_ext, divs).

    18m de comprimento x 4m. 4 quartos longos (cada ~4.4m) separados por 3
    divisorias internas. Cada divisoria tem porta de passagem -> circulacao
    em enfiada (corredor de comodos).
    """
    L, W = 18.0, 4.0
    pts = [(0, 0), (L, 0), (L, W), (0, W)]
    walls = hb_lib.build_room_loop(pts, name="long", thickness=thickness, height=height)
    # parede frontal (walls[0]) com porta de entrada + janelas ao longo
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=1.2)
    for ox in (4.5, 8.5, 12.5, 16.5):
        hb_lib.add_opening(walls[0], 'WINDOW', offset_x=ox, z=hb_lib.WIN_FROM_FLOOR)
    # parede do fundo (walls[2]) com janelas
    for ox in (2.0, 6.0, 10.0, 14.0):
        hb_lib.add_opening(walls[2], 'WINDOW', offset_x=ox, z=hb_lib.WIN_FROM_FLOOR)

    # 3 divisorias internas verticais em x = 4.5, 9.0, 13.5 -> 4 quartos
    divs = []
    for i, x in enumerate((4.5, 9.0, 13.5)):
        d = hb_lib.new_wall(f"long_div{i}", W, (x, 0, 0), 90,
                            thickness=thickness, height=height)
        # porta de passagem entre quartos consecutivos
        hb_lib.add_opening(d, 'DOOR', offset_x=2.5)
        divs.append(d)
    return pts, walls, divs


def house_long():
    pts, walls, divs = _long_house_walls()
    hb_lib.add_floor(pts)
    return pts


# ---------------- C. corte dollhouse (remove uma parede) ----------------
def house_long_cut():
    """Casa longa gerada FECHADA e depois cortada: remove a parede frontal inteira.

    walls[0] e a parede frontal (y=0, comprida). Removendo-a, ve-se todos os
    quartos por dentro de uma vez (corte transversal tipo dollhouse). As divisorias
    e suas portas de passagem ficam expostas.
    """
    pts, walls, divs = _long_house_walls()
    hb_lib.add_floor(pts)
    # MANIPULACAO POSTUMA: a casa ja esta montada e fechada. Agora removemos a frontal.
    hb_lib.remove_wall(walls[0])
    return pts


# ---------------- D. teto parametrizavel ----------------
def _house_with_ceiling(ceiling_height):
    """Casa 6x5 com 1 divisoria, fechada por um TETO na altura `ceiling_height`.

    As paredes sobem ate ceiling_height + slab pra encostar na laje (pe-direito
    parametrizado). Removemos a parede frontal pra dar pra ver o teto por dentro.
    """
    slab = 0.15
    wall_h = ceiling_height + slab
    L, W = 6.0, 5.0
    pts = [(0, 0), (L, 0), (L, W), (0, W)]
    walls = hb_lib.build_room_loop(pts, name="ceil", height=wall_h)
    # divisoria interna com porta
    div = hb_lib.new_wall("ceil_div", W, (3.0, 0, 0), 90, height=wall_h)
    hb_lib.add_opening(div, 'DOOR', offset_x=2.3)
    # janelas nas laterais
    hb_lib.add_opening(walls[1], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[3], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    # MANIPULACAO POSTUMA 1: teto solido na altura do pe-direito
    hb_lib.add_ceiling(pts, ceiling_height, slab=slab)
    # MANIPULACAO POSTUMA 2: tira a frontal pra ver o teto por dentro (corte dollhouse)
    hb_lib.remove_wall(walls[0])
    return pts


def house_ceiling_low():
    return _house_with_ceiling(2.4)   # pe-direito baixo


def house_ceiling_high():
    return _house_with_ceiling(3.4)   # pe-direito alto


HOUSES = {
    "05_fat_walls":    house_fat_walls,
    "06_long":         house_long,
    "07_long_cut":     house_long_cut,
    "08_ceiling_low":  house_ceiling_low,
    "09_ceiling_high": house_ceiling_high,
}


def frame_camera_dollhouse(pts, open_side_y=0.0):
    """Camera de corte: olha o lado aberto (parede removida) bem de frente e perto.

    Para a casa longa cortada, a frontal removida fica em y=open_side_y. Posiciona
    a camera desse lado, baixa e proxima, pra ver os comodos por dentro nitidamente.
    """
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span_x = max(xs) - min(xs)
    cam_data = bpy.data.cameras.new("CamDoll")
    cam = bpy.data.objects.new("CamDoll", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    # do lado aberto (y menor), levemente de cima, recuado o bastante p/ pegar o comprimento
    cam.location = (cx, open_side_y - span_x * 0.55, hb_lib.WALL_HEIGHT * 1.1)
    target = Vector((cx, cy, hb_lib.WALL_HEIGHT * 0.45))
    direction = target - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 28
    bpy.context.scene.camera = cam
    return cam


def build_one(key, fn):
    hb_lib.reset_scene()
    pts = fn()
    mat = bh.neutral_material()
    bh.assign_neutral_material(mat)
    bh.frame_camera(pts)
    bh.setup_light()

    blend_path = os.path.join(BLENDS, f"{key}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    wb = os.path.join(RENDERS, f"{key}_structure.png")
    bh.render_workbench(wb)
    print(f"[{key}] structure -> {wb}")

    ev = os.path.join(RENDERS, f"{key}_render.png")
    bh.render_eevee(ev)
    print(f"[{key}] render -> {ev}")

    bh.frame_camera_top(pts)
    tp = os.path.join(RENDERS, f"{key}_plan.png")
    bh.render_workbench(tp)
    print(f"[{key}] plan -> {tp}")

    # render extra de corte para casas com parede frontal removida (lado aberto em y=0)
    if key in ("07_long_cut", "08_ceiling_low", "09_ceiling_high"):
        frame_camera_dollhouse(pts, open_side_y=0.0)
        dh = os.path.join(RENDERS, f"{key}_dollhouse.png")
        bh.render_eevee(dh)
        print(f"[{key}] dollhouse -> {dh}")

    n_walls = len([o for o in bpy.data.objects if 'IS_WALL_BP' in o])
    n_doors = len([o for o in bpy.data.objects if o.get('IS_ENTRY_DOOR_BP')])
    n_wins = len([o for o in bpy.data.objects if o.get('IS_WINDOW_BP')])
    n_ceil = len([o for o in bpy.data.objects if o.get('IS_CEILING_BP')])
    print(f"[{key}] paredes={n_walls} portas={n_doors} janelas={n_wins} tetos={n_ceil}")


def main():
    only = None
    if "--house" in sys.argv:
        only = sys.argv[sys.argv.index("--house") + 1]
    for key, fn in HOUSES.items():
        if only and key != only:
            continue
        print(f"\n########## {key} ##########")
        build_one(key, fn)


if __name__ == "__main__":
    main()
