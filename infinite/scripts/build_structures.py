"""Gera 4 estruturas infinitas e exporta cada uma como GLB.

Estruturas:
  1. ESCHER: grid 3D de plataformas conectadas por escadas em loops impossiveis
  2. TOWER: torre vertical com modulos repetidos em altura (helicoidal)
  3. ZIGGURAT: zigurats encadeados em grid XZ
  4. MIX: mistura tudo num megaplex

Pipeline:
  - cria base modules (escadas + plataformas + pillars)
  - usa collection instancing + array modifier pra repetir (instancing real)
  - antes do export: realize all instances (make_real) ou usa GN realize node
  - exporta como GLB
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix

# importar lib local
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from stair_lib import (
    stair_straight, stair_spiral, stair_L, stair_suspended, step_pyramid, stair_archimesh, _new_mesh_obj
)

# habilitar extensions
import addon_utils
for a in ["bl_ext.blender_org.archimesh", "bl_ext.blender_org.modern_primitive"]:
    try:
        addon_utils.enable(a, default_set=True, persistent=True)
    except Exception:
        pass

OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "out", "glb"))
os.makedirs(OUT_DIR, exist_ok=True)


# ---------- helpers ----------

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    # purgar dados orfaos
    for block_type in (bpy.data.meshes, bpy.data.materials, bpy.data.collections):
        for b in list(block_type):
            if b.users == 0:
                block_type.remove(b)


def make_platform(size=3.0, thickness=0.25, name="Platform"):
    obj = _new_mesh_obj(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size
        v.co.y *= size
        v.co.z *= thickness
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def make_pillar(height=4.0, radius=0.2, name="Pillar"):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, vertices=12)
    obj = bpy.context.active_object
    obj.name = name
    obj.location.z = height / 2
    return obj


def add_material(obj, name, color, metallic=0.0, roughness=0.7):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return mat


# ---------- ESCHER ----------

def build_escher(grid=4, cell=10.0):
    """Grid 3D de plataformas em camadas conectadas por escadas variadas.
    Cada plataforma tem exatamente 1 escada subindo, alternando direcao,
    pra dar sensacao de loop nao-euclidiano."""
    clear_scene()

    plat_template = make_platform(size=4.0, thickness=0.4, name="EscherPlat")
    add_material(plat_template, "MatPlat", (0.88, 0.82, 0.7), roughness=0.85)
    plat_template.hide_set(False)

    # 6 templates de escada
    s_straight = stair_straight(steps=14, step_w=1.6, step_d=0.45, step_h=0.3, name="EscStraight")
    s_spiral = stair_spiral(steps=18, radius=1.7, step_h=0.28, step_w=1.4, name="EscSpiral")
    s_L = stair_L(steps_a=7, steps_b=7, step_d=0.45, step_w=1.5, step_h=0.3, name="EscL")
    s_susp = stair_suspended(steps=12, step_w=1.5, step_d=0.5, step_h=0.32, gap=0.18, name="EscSusp")
    s_arch = stair_archimesh(name="EscArchi")

    stair_pool = [s_straight, s_spiral, s_L, s_susp, s_arch]
    stair_colors = [
        (0.55, 0.45, 0.35),
        (0.5, 0.55, 0.65),
        (0.65, 0.5, 0.4),
        (0.55, 0.6, 0.5),
        (0.6, 0.45, 0.3),
    ]
    for i, s in enumerate(stair_pool):
        add_material(s, f"MatStair{i}", stair_colors[i], roughness=0.6)
        s.location = (-100 + i * 5, -100, 0)
        s.hide_render = True
        s.hide_set(True)

    plat_template.location = (-100, -90, 0)
    plat_template.hide_render = True
    plat_template.hide_set(True)

    instances = []
    floor_h = 4.5
    for iz in range(grid):
        # cada camada tem deslocamento "twist" — Escher feeling
        twist_x = (iz % 2) * cell * 0.5
        twist_y = (iz % 3) * cell * 0.3
        for ix in range(grid):
            for iy in range(grid):
                pl = bpy.data.objects.new(f"P_{ix}_{iy}_{iz}", plat_template.data)
                bpy.context.collection.objects.link(pl)
                pl.location = (ix * cell + twist_x, iy * cell + twist_y, iz * floor_h)
                instances.append(pl)
                # escada subindo pra proxima camada (se tiver)
                if iz < grid - 1:
                    s_template = stair_pool[(ix + iy + iz) % len(stair_pool)]
                    st = bpy.data.objects.new(f"S_{ix}_{iy}_{iz}", s_template.data)
                    bpy.context.collection.objects.link(st)
                    dir_idx = (ix * 3 + iy * 7 + iz) % 4
                    angle = dir_idx * (math.pi / 2)
                    st.rotation_euler = (0, 0, angle)
                    dx = math.cos(angle) * 2.0
                    dy = math.sin(angle) * 2.0
                    st.location = (ix * cell + twist_x + dx,
                                   iy * cell + twist_y + dy,
                                   iz * floor_h + 0.2)
                    instances.append(st)

    bpy.ops.object.light_add(type='SUN', location=(20, 20, 50))
    bpy.context.active_object.data.energy = 2.5

    return instances


# ---------- TOWER ----------

def build_tower(levels=14, radius=12.0, level_h=5.0):
    """Torre vertical: anel de plataformas rotaciona a cada andar + escada helicoidal central."""
    clear_scene()

    # plataforma "donut" central
    plat = make_platform(size=3.5, thickness=0.3, name="TowerPlat")
    add_material(plat, "MatTowerPlat", (0.7, 0.7, 0.78), metallic=0.3, roughness=0.5)
    plat.location = (-100, -100, 0)
    plat.hide_render = True
    plat.hide_set(True)

    s_spiral = stair_spiral(steps=22, radius=2.0, step_h=level_h / 22, step_w=1.3,
                            total_angle=math.pi * 1.8, name="TowerSpiral")
    add_material(s_spiral, "MatTowerStair", (0.5, 0.55, 0.65), metallic=0.4, roughness=0.4)
    s_spiral.location = (-100, -90, 0)
    s_spiral.hide_render = True
    s_spiral.hide_set(True)

    pillar = make_pillar(height=level_h, radius=0.18, name="TowerPillar")
    add_material(pillar, "MatPillar", (0.3, 0.32, 0.38), metallic=0.6, roughness=0.3)
    pillar.location = (-100, -80, 0)
    pillar.hide_render = True
    pillar.hide_set(True)

    instances = []
    petals = 8  # plataformas ao redor da torre por andar
    for lv in range(levels):
        z = lv * level_h
        twist = lv * (math.pi / petals / 2)  # rotaciona a cada andar
        for p in range(petals):
            ang = twist + p * (2 * math.pi / petals)
            pl = bpy.data.objects.new(f"TP_{lv}_{p}", plat.data)
            bpy.context.collection.objects.link(pl)
            pl.location = (radius * math.cos(ang), radius * math.sin(ang), z)
            pl.rotation_euler = (0, 0, ang)
            instances.append(pl)
            # pillar
            pi = bpy.data.objects.new(f"TPi_{lv}_{p}", pillar.data)
            bpy.context.collection.objects.link(pi)
            pi.location = (radius * math.cos(ang), radius * math.sin(ang), z + level_h / 2)
            instances.append(pi)
        # escada helicoidal central
        ss = bpy.data.objects.new(f"TS_{lv}", s_spiral.data)
        bpy.context.collection.objects.link(ss)
        ss.location = (0, 0, z)
        ss.rotation_euler = (0, 0, twist)
        instances.append(ss)

    bpy.ops.object.light_add(type='SUN', location=(10, 10, 30))
    bpy.context.active_object.data.energy = 2.0

    return instances


# ---------- ZIGGURAT ----------

def build_ziggurat(grid=4, cell=16.0):
    """Grid de zigurats (step pyramids) conectados por pontes/escadas."""
    clear_scene()

    pyr = step_pyramid(layers=7, base=10.0, step=1.0, name="ZigPyr")
    add_material(pyr, "MatZig", (0.78, 0.62, 0.42), roughness=0.85)
    pyr.location = (-100, -100, 0)
    pyr.hide_render = True
    pyr.hide_set(True)

    bridge = make_platform(size=2.0, thickness=0.2, name="ZigBridge")
    # alongar
    for v in bridge.data.vertices:
        v.co.x *= 2.5
        v.co.y *= 0.3
    add_material(bridge, "MatBridge", (0.4, 0.32, 0.25), roughness=0.7)
    bridge.location = (-100, -90, 0)
    bridge.hide_render = True
    bridge.hide_set(True)

    s_straight = stair_straight(steps=10, step_w=1.5, step_d=0.45, step_h=0.3, name="ZigStair")
    add_material(s_straight, "MatZigStair", (0.6, 0.5, 0.35), roughness=0.7)
    s_straight.location = (-100, -80, 0)
    s_straight.hide_render = True
    s_straight.hide_set(True)

    instances = []
    for ix in range(grid):
        for iy in range(grid):
            zp = bpy.data.objects.new(f"Z_{ix}_{iy}", pyr.data)
            bpy.context.collection.objects.link(zp)
            zp.location = (ix * cell, iy * cell, 0)
            instances.append(zp)
            # ponte ao vizinho +X
            if ix < grid - 1:
                br = bpy.data.objects.new(f"B_{ix}_{iy}_x", bridge.data)
                bpy.context.collection.objects.link(br)
                br.location = (ix * cell + cell / 2, iy * cell, 3.5)
                instances.append(br)
            # ponte ao vizinho +Y
            if iy < grid - 1:
                br = bpy.data.objects.new(f"B_{ix}_{iy}_y", bridge.data)
                bpy.context.collection.objects.link(br)
                br.location = (ix * cell, iy * cell + cell / 2, 3.5)
                br.rotation_euler = (0, 0, math.pi / 2)
                instances.append(br)
            # escada subindo cada lado do zig
            for d in range(4):
                ss = bpy.data.objects.new(f"ZS_{ix}_{iy}_{d}", s_straight.data)
                bpy.context.collection.objects.link(ss)
                ang = d * math.pi / 2
                ss.rotation_euler = (0, 0, ang + math.pi)
                ss.location = (ix * cell + math.cos(ang) * 6.0, iy * cell + math.sin(ang) * 6.0, 0)
                instances.append(ss)

    bpy.ops.object.light_add(type='SUN', location=(10, 10, 30))
    bpy.context.active_object.data.energy = 2.0

    return instances


# ---------- MIX ----------

def build_mix():
    """Megaplex: torre central + zigurats em volta + grid escher em camada superior."""
    clear_scene()

    # zigurats numa base 3x3
    pyr = step_pyramid(layers=5, name="MixPyr")
    for v in pyr.data.vertices:
        v.co *= 0.7
    add_material(pyr, "MatMixPyr", (0.7, 0.55, 0.4), roughness=0.85)
    pyr.location = (-100, -100, 0)
    pyr.hide_render = True
    pyr.hide_set(True)

    s_straight = stair_straight(steps=10, step_w=1.4, step_d=0.4, step_h=0.3, name="MixStr")
    add_material(s_straight, "MatMixStr", (0.5, 0.4, 0.3), roughness=0.7)
    s_straight.location = (-100, -90, 0)
    s_straight.hide_render = True
    s_straight.hide_set(True)

    s_spiral = stair_spiral(steps=24, radius=2.2, step_h=0.3, step_w=1.4,
                            total_angle=math.pi * 2.0, name="MixSpr")
    add_material(s_spiral, "MatMixSpr", (0.55, 0.6, 0.7), metallic=0.4, roughness=0.4)
    s_spiral.location = (-100, -80, 0)
    s_spiral.hide_render = True
    s_spiral.hide_set(True)

    s_susp = stair_suspended(steps=14, step_w=1.3, step_d=0.45, step_h=0.28, gap=0.25, name="MixSus")
    add_material(s_susp, "MatMixSus", (0.65, 0.7, 0.55), roughness=0.5)
    s_susp.location = (-100, -70, 0)
    s_susp.hide_render = True
    s_susp.hide_set(True)

    plat = make_platform(size=3.0, thickness=0.3, name="MixPlat")
    add_material(plat, "MatMixPlat", (0.85, 0.8, 0.7), roughness=0.85)
    plat.location = (-100, -60, 0)
    plat.hide_render = True
    plat.hide_set(True)

    instances = []
    GRID = 3
    CELL = 14.0
    # base ziggurats (skip centro pra dar lugar a torre)
    for ix in range(GRID):
        for iy in range(GRID):
            if ix == 1 and iy == 1:
                continue
            zp = bpy.data.objects.new(f"MZ_{ix}_{iy}", pyr.data)
            bpy.context.collection.objects.link(zp)
            zp.location = (ix * CELL - CELL, iy * CELL - CELL, 0)
            instances.append(zp)
            # escada straight em 1 direcao
            d = (ix + iy) % 4
            ang = d * math.pi / 2
            ss = bpy.data.objects.new(f"MS_{ix}_{iy}", s_straight.data)
            bpy.context.collection.objects.link(ss)
            ss.rotation_euler = (0, 0, ang + math.pi)
            ss.location = (ix * CELL - CELL + math.cos(ang) * 5.0,
                           iy * CELL - CELL + math.sin(ang) * 5.0, 0)
            instances.append(ss)

    # torre central espiral
    for lv in range(8):
        z = 5 + lv * 4.0
        ss = bpy.data.objects.new(f"MSp_{lv}", s_spiral.data)
        bpy.context.collection.objects.link(ss)
        ss.location = (0, 0, z)
        ss.rotation_euler = (0, 0, lv * math.pi / 4)
        instances.append(ss)

    # camada de plataformas suspensas no topo
    TOP_Z = 38.0
    for ix in range(GRID + 1):
        for iy in range(GRID + 1):
            pl = bpy.data.objects.new(f"MP_{ix}_{iy}", plat.data)
            bpy.context.collection.objects.link(pl)
            pl.location = (ix * CELL - CELL * 1.5, iy * CELL - CELL * 1.5, TOP_Z)
            instances.append(pl)
            # escadas suspensas ligando
            if ix < GRID:
                sus = bpy.data.objects.new(f"MSu_{ix}_{iy}", s_susp.data)
                bpy.context.collection.objects.link(sus)
                sus.location = (ix * CELL - CELL * 1.5 + 1.5, iy * CELL - CELL * 1.5, TOP_Z - 2.0)
                instances.append(sus)

    bpy.ops.object.light_add(type='SUN', location=(10, 10, 30))
    bpy.context.active_object.data.energy = 2.0

    return instances


# ---------- EXPORT ----------

def export_glb(name):
    """Exporta cena atual como GLB. As instancias compartilham mesh_data entao o GLB fica pequeno."""
    out_path = os.path.join(OUT_DIR, f"{name}.glb")
    # selecionar so objetos visiveis (descarta os templates -100)
    bpy.ops.object.select_all(action='DESELECT')
    visible = [o for o in bpy.context.scene.objects
               if o.type == 'MESH' and not o.hide_get() and o.location.x > -50]
    for o in visible:
        o.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        use_selection=True,
        export_format='GLB',
        export_apply=False,
        export_materials='EXPORT',
        export_lights=False,
        export_cameras=False,
        export_yup=True,
    )
    size = os.path.getsize(out_path) / 1024
    print(f"OK exported {name}.glb ({size:.1f} KB, {len(visible)} objs)")
    return out_path


# ---------- MAIN ----------

def main():
    builders = {
        "escher": lambda: build_escher(grid=4, cell=8.0),
        "tower": lambda: build_tower(levels=20, radius=5.0, level_h=4.5),
        "ziggurat": lambda: build_ziggurat(grid=3, cell=12.0),
        "mix": build_mix,
    }
    arg = sys.argv[-1]
    if arg in builders:
        builders[arg]()
        export_glb(arg)
    else:
        # all
        for name, fn in builders.items():
            print(f"\n=== building {name} ===")
            fn()
            export_glb(name)
            # tambem salva blend pra inspecao
            blend_path = os.path.join(OUT_DIR, f"{name}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=blend_path)


if __name__ == "__main__":
    main()
