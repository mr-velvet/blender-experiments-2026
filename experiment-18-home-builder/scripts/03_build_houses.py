"""Gera varias casas com o Home Builder 5 e renderiza cada uma em baixa res, sem textura.

Para cada casa:
  1. monta paredes (anel fechado) + portas/janelas via hb_lib (classes do addon)
  2. salva .blend
  3. "print de estrutura": render OpenGL workbench (solid), rapido, baixa res
  4. "render": Eevee baixa res, sem textura (so cor neutra de parede)

Tudo headless. Camera isometrica 3/4 + sol simples.
"""
import bpy
import sys
import os
import math
from mathutils import Vector

sys.path.append(os.path.dirname(__file__))
import hb_lib  # noqa

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
RENDERS = os.path.join(OUT, "renders")
BLENDS = os.path.join(OUT, "blends")
os.makedirs(RENDERS, exist_ok=True)
os.makedirs(BLENDS, exist_ok=True)

RES = 720  # baixa res


# ---------- casas (cada uma: dict com contorno + aberturas) ----------
def house_rect():
    """Casa retangular simples 6x4m: porta na frente, 2 janelas."""
    pts = [(0, 0), (6, 0), (6, 4), (0, 4)]
    walls = hb_lib.build_room_loop(pts, name="rect")
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=2.5)            # parede frontal
    hb_lib.add_opening(walls[0], 'WINDOW', offset_x=0.6, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[2], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    return pts


def house_L():
    """Casa em L."""
    pts = [(0, 0), (7, 0), (7, 3), (4, 3), (4, 6), (0, 6)]
    walls = hb_lib.build_room_loop(pts, name="L")
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=3.0)
    hb_lib.add_opening(walls[0], 'WINDOW', offset_x=0.6, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[5], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[2], 'WINDOW', offset_x=1.2, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    return pts


def house_two_rooms():
    """Casa retangular 8x5 com parede divisoria interna + porta interna."""
    pts = [(0, 0), (8, 0), (8, 5), (0, 5)]
    walls = hb_lib.build_room_loop(pts, name="2r")
    # parede divisoria interna (nao faz parte do anel)
    div = hb_lib.new_wall("2r_div", 5.0, (4, 0, 0), 90)
    hb_lib.add_opening(div, 'DOOR', offset_x=2.0)               # porta interna
    # externas
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=1.5)
    hb_lib.add_opening(walls[0], 'WINDOW', offset_x=5.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[2], 'WINDOW', offset_x=2.0, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[2], 'WINDOW', offset_x=5.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_opening(walls[1], 'WINDOW', offset_x=2.5, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    return pts


def house_hex():
    """Casa hexagonal (testa mitra de canto em angulos nao-retos)."""
    r = 3.5
    pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    walls = hb_lib.build_room_loop(pts, name="hex")
    hb_lib.add_opening(walls[0], 'DOOR', offset_x=1.4)
    for i in (1, 2, 3, 4, 5):
        hb_lib.add_opening(walls[i], 'WINDOW', offset_x=1.3, z=hb_lib.WIN_FROM_FLOOR)
    hb_lib.add_floor(pts)
    return pts


HOUSES = {
    "01_rect": house_rect,
    "02_L": house_L,
    "03_two_rooms": house_two_rooms,
    "04_hex": house_hex,
}


# ---------- camera, luz, materiais, render ----------
def neutral_material():
    mat = bpy.data.materials.new("WallNeutral")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.76, 0.72, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def assign_neutral_material(mat):
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.materials.clear()
            obj.data.materials.append(mat)


def frame_camera(pts):
    """Camera 3/4 isometrica enquadrando o contorno."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys), 4.0)
    dist = span * 1.9

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    # camera mais baixa (olho ~1.6m), 3/4 frontal, p/ evidenciar fachada+aberturas
    cam.location = (cx + dist * 0.65, cy - dist * 0.8, hb_lib.WALL_HEIGHT * 1.5)
    target = Vector((cx, cy, hb_lib.WALL_HEIGHT * 0.4))
    direction = target - Vector(cam.location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = 35
    bpy.context.scene.camera = cam
    return cam


def frame_camera_top(pts):
    """Camera ortografica de topo (planta baixa) — evidencia layout/divisorias."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), max(ys) - min(ys), 4.0)

    cam_data = bpy.data.cameras.new("CamTop")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = span * 1.25
    cam = bpy.data.objects.new("CamTop", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (cx, cy, 30.0)
    cam.rotation_euler = (0, 0, 0)
    bpy.context.scene.camera = cam
    return cam


def setup_light():
    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(40))
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.40, 0.45, 0.52, 1.0)
        bg.inputs[1].default_value = 0.7


def render_workbench(path):
    """Print de estrutura: solid shading, rapidissimo."""
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_WORKBENCH'
    scn.render.resolution_x = RES
    scn.render.resolution_y = RES
    scn.render.resolution_percentage = 100
    scn.display.shading.light = 'STUDIO'
    scn.display.shading.show_shadows = True
    scn.display.shading.show_cavity = True
    scn.render.film_transparent = False
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_eevee(path):
    """Render baixa res sem textura (material neutro), Eevee samples baixos."""
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = RES
    scn.render.resolution_y = RES
    scn.render.resolution_percentage = 100
    try:
        scn.eevee.taa_render_samples = 16
    except Exception:
        pass
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


def build_one(key, fn):
    hb_lib.reset_scene()
    pts = fn()
    mat = neutral_material()
    assign_neutral_material(mat)
    frame_camera(pts)
    setup_light()

    # salva blend
    blend_path = os.path.join(BLENDS, f"{key}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    # print de estrutura 3/4 (workbench)
    wb = os.path.join(RENDERS, f"{key}_structure.png")
    render_workbench(wb)
    print(f"[{key}] structure -> {wb}")

    # render eevee baixa res 3/4
    ev = os.path.join(RENDERS, f"{key}_render.png")
    render_eevee(ev)
    print(f"[{key}] render -> {ev}")

    # planta baixa (top ortografico, workbench) — mostra layout/divisorias/aberturas
    frame_camera_top(pts)
    tp = os.path.join(RENDERS, f"{key}_plan.png")
    render_workbench(tp)
    print(f"[{key}] plan -> {tp}")

    # stats
    n_walls = len([o for o in bpy.data.objects if 'IS_WALL_BP' in o])
    n_doors = len([o for o in bpy.data.objects if o.get('IS_ENTRY_DOOR_BP')])
    n_wins = len([o for o in bpy.data.objects if o.get('IS_WINDOW_BP')])
    print(f"[{key}] paredes={n_walls} portas={n_doors} janelas={n_wins}")


def main():
    only = None
    if "--house" in sys.argv:
        only = sys.argv[sys.argv.index("--house") + 1]
    for key, fn in HOUSES.items():
        if only and key != only:
            continue
        print(f"\n########## CASA {key} ##########")
        build_one(key, fn)


if __name__ == "__main__":
    main()
