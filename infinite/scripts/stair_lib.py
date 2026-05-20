"""Biblioteca de geradores de escada. Cada funcao retorna um objeto Blender 'escada'.

Geradores usam mix de:
- bmesh puro (escadas custom: straight, spiral, suspended)
- archimesh (escada parametrica via op)
- modern_primitive (steppyramid e outros)

Convencao: a escada nasce com base em z=0, sobe ao longo de +Z, e principal direcao horizontal e +X (ou +Y pra L-shape).
Todas tem propriedade ['stair_height'] e ['stair_run'] (footprint) pra encadeamento.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix


def _new_mesh_obj(name):
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def stair_straight(steps=12, step_w=1.2, step_d=0.35, step_h=0.22, name="StairStraight"):
    """Escada reta. Comeca em (0,0,0), sobe ao longo de +X."""
    obj = _new_mesh_obj(name)
    bm = bmesh.new()
    for i in range(steps):
        x0 = i * step_d
        z0 = i * step_h
        bmesh.ops.create_cube(bm, size=1.0)
        # mover o ultimo cube criado pra posicao do degrau
        verts = bm.verts[-8:]
        # scale + translate
        for v in verts:
            v.co.x = v.co.x * step_d + x0 + step_d / 2
            v.co.y = v.co.y * step_w
            v.co.z = v.co.z * step_h + z0 + step_h / 2
    bm.to_mesh(obj.data)
    bm.free()
    obj["stair_height"] = steps * step_h
    obj["stair_run"] = steps * step_d
    obj["stair_top"] = (steps * step_d, 0, steps * step_h)
    return obj


def stair_spiral(steps=18, radius=2.0, step_h=0.22, step_w=1.2, total_angle=math.pi * 1.5, name="StairSpiral"):
    """Escada helicoidal em torno de Z, sobe ao longo de +Z."""
    obj = _new_mesh_obj(name)
    bm = bmesh.new()
    angle_step = total_angle / steps
    for i in range(steps):
        ang = i * angle_step
        z0 = i * step_h
        # cada degrau eh um setor de anel (4 vertices)
        # raio interno e externo
        r_in = radius - step_w / 2
        r_out = radius + step_w / 2
        a0 = ang - angle_step / 2
        a1 = ang + angle_step / 2
        # 8 vertices: 4 base + 4 top
        pts_b = [
            (r_in * math.cos(a0), r_in * math.sin(a0), z0),
            (r_out * math.cos(a0), r_out * math.sin(a0), z0),
            (r_out * math.cos(a1), r_out * math.sin(a1), z0),
            (r_in * math.cos(a1), r_in * math.sin(a1), z0),
        ]
        pts_t = [(p[0], p[1], p[2] + step_h) for p in pts_b]
        vb = [bm.verts.new(p) for p in pts_b]
        vt = [bm.verts.new(p) for p in pts_t]
        # 6 faces
        bm.faces.new(vb)  # bottom
        bm.faces.new(list(reversed(vt)))  # top
        for j in range(4):
            bm.faces.new([vb[j], vb[(j + 1) % 4], vt[(j + 1) % 4], vt[j]])
    bm.to_mesh(obj.data)
    bm.free()
    obj["stair_height"] = steps * step_h
    # ponto de chegada (no topo, no angulo final)
    top_ang = (steps - 1) * angle_step
    obj["stair_top"] = (radius * math.cos(top_ang), radius * math.sin(top_ang), steps * step_h)
    return obj


def stair_L(steps_a=8, steps_b=8, step_d=0.35, step_w=1.2, step_h=0.22, name="StairL"):
    """Escada em L: sobe ao longo de +X depois vira pra +Y."""
    obj_a = stair_straight(steps_a, step_w, step_d, step_h, name=name + "_A")
    obj_b = stair_straight(steps_b, step_w, step_d, step_h, name=name + "_B")
    # mover B pro topo de A e rotacionar 90 graus
    z_a = steps_a * step_h
    x_a = steps_a * step_d
    obj_b.location = (x_a - step_w / 2, step_w / 2, z_a)
    obj_b.rotation_euler = (0, 0, math.pi / 2)
    # juntar
    bpy.ops.object.select_all(action='DESELECT')
    obj_a.select_set(True)
    obj_b.select_set(True)
    bpy.context.view_layer.objects.active = obj_a
    bpy.ops.object.join()
    obj_a.name = name
    obj_a["stair_height"] = (steps_a + steps_b) * step_h
    obj_a["stair_top"] = (x_a, steps_b * step_d, (steps_a + steps_b) * step_h)
    return obj_a


def stair_suspended(steps=14, step_w=1.2, step_d=0.4, step_h=0.25, gap=0.15, name="StairSuspended"):
    """Escada flutuante: degraus separados, sem laterais."""
    obj = _new_mesh_obj(name)
    bm = bmesh.new()
    for i in range(steps):
        x0 = i * (step_d + gap)
        z0 = i * step_h
        # cubo separado por degrau
        pts_b = [
            (x0, -step_w / 2, z0),
            (x0 + step_d, -step_w / 2, z0),
            (x0 + step_d, step_w / 2, z0),
            (x0, step_w / 2, z0),
        ]
        pts_t = [(p[0], p[1], p[2] + step_h * 0.5) for p in pts_b]
        vb = [bm.verts.new(p) for p in pts_b]
        vt = [bm.verts.new(p) for p in pts_t]
        bm.faces.new(vb)
        bm.faces.new(list(reversed(vt)))
        for j in range(4):
            bm.faces.new([vb[j], vb[(j + 1) % 4], vt[(j + 1) % 4], vt[j]])
    bm.to_mesh(obj.data)
    bm.free()
    obj["stair_height"] = steps * step_h
    obj["stair_top"] = (steps * (step_d + gap), 0, steps * step_h)
    return obj


def stair_archimesh(name="StairArchi"):
    """Escada via archimesh op (parametrica, gera handrails). Habilitar addon antes."""
    import addon_utils
    try:
        addon_utils.enable("bl_ext.blender_org.archimesh", default_set=True, persistent=True)
    except Exception:
        pass
    bpy.ops.mesh.archimesh_stairs()
    obj = bpy.context.active_object
    obj.name = name
    # archimesh stairs default: ~12 steps, ~3m altura
    obj["stair_height"] = 3.0
    obj["stair_top"] = (4.0, 0, 3.0)
    return obj


def step_pyramid(layers=6, base=8.0, step=0.7, name="StepPyramid"):
    """Pyramid (zigurat) via bmesh: piramide escalonada solida."""
    obj = _new_mesh_obj(name)
    bm = bmesh.new()
    for i in range(layers):
        s = base - i * step * 1.5
        if s <= 0.5:
            break
        z = i * step
        bmesh.ops.create_cube(bm, size=1.0)
        verts = bm.verts[-8:]
        for v in verts:
            v.co.x *= s
            v.co.y *= s
            v.co.z = v.co.z * step + z + step / 2
    bm.to_mesh(obj.data)
    bm.free()
    obj["stair_height"] = layers * step
    obj["stair_top"] = (0, 0, layers * step)
    return obj


if __name__ == "__main__":
    # teste rapido: gera 1 de cada
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    objs = [
        stair_straight(),
        stair_spiral(),
        stair_L(),
        stair_suspended(),
        step_pyramid(),
    ]
    for i, o in enumerate(objs):
        o.location.x += i * 6
    print("OK gerou", [o.name for o in objs])
