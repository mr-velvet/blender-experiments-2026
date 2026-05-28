"""Biblioteca que dirige o Home Builder 5 via suas classes internas (headless).

Toda a geometria de parede/porta/janela vem do addon (Geometry Nodes GeoNodeWall /
GeoNodeCage). Nao recriamos nada a mao: chamamos as mesmas classes que os operadores
modais usam, so que sem GUI.

Receita (extraida de operators/walls.py e operators/doors_windows.py do addon):
  parede:  GeoNodeWall().create(name); set_input Length/Height/Thickness; posiciona obj
           + rotation_euler.z; conecta paredes via Left/Right Angle (mitra de canto)
  abertura: GeoNodeCage().create(name); set_input Dim X/Y/Z; parent na parede;
            location.x = offset ao longo da parede; location.z = altura do chao;
            modifier BOOLEAN DIFFERENCE na parede com o cage como cutter (o buraco real)
"""
import bpy
import math
import importlib
from mathutils import Vector

M = "bl_ext.blender_org.home_builder_5"
hb_types = importlib.import_module(f"{M}.hb_types")

# defaults reais do addon (metros)
WALL_THICKNESS = 0.1143
WALL_HEIGHT = 2.4384
DOOR_W = 0.9144
DOOR_H = 2.1336
WIN_W = 1.0
WIN_H = 1.0
WIN_FROM_FLOOR = 0.9144


def ensure_addon():
    """Garante o addon habilitado (registra as PropertyGroups home_builder)."""
    import addon_utils
    state = addon_utils.check(M)
    if not state[1]:
        addon_utils.enable(M, default_set=True, persistent=True)


def reset_scene():
    """Limpa a cena SEM resetar preferences (resetar prefs desregistra o addon)."""
    ensure_addon()
    # remove todos os objetos/dados da cena atual
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)
    # garante metros
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.length_unit = 'METERS'


def new_wall(name, length, location, angle_deg,
             thickness=WALL_THICKNESS, height=WALL_HEIGHT):
    """Cria uma parede do Home Builder com tamanho/posicao/rotacao dados."""
    w = hb_types.GeoNodeWall()
    w.create(name)
    w.set_input('Thickness', thickness)
    w.set_input('Height', height)
    w.set_input('Length', length)
    w.obj.location = Vector(location)
    w.obj.rotation_euler.z = math.radians(angle_deg)
    return w


def add_opening(wall, kind, offset_x, width=None, height=None, z=0.0):
    """Adiciona porta ('DOOR') ou janela ('WINDOW') na parede via cage + boolean cut.

    offset_x: distancia do inicio da parede (local X)
    z: altura do chao (0 pra porta, WIN_FROM_FLOOR pra janela default)
    """
    if kind == 'DOOR':
        width = width or DOOR_W
        height = height or DOOR_H
        tag = 'IS_ENTRY_DOOR_BP'
    else:
        width = width or WIN_W
        height = height or WIN_H
        tag = 'IS_WINDOW_BP'

    wall_thickness = wall.get_input('Thickness')
    folga = 0.02                       # overshoot p/ boolean limpo (sem face coplanar)
    cut_y = wall_thickness + folga

    cage = hb_types.GeoNodeCage()
    cage.create(kind.title())
    cage.obj[tag] = True
    cage.set_input('Dim X', width)
    cage.set_input('Dim Y', cut_y)
    cage.set_input('Dim Z', height)
    # Com Show Cage no default o node group ja gera um cubo solido de 8 verts (o cutter).
    # NAO setar Show Cage=True: aqui so precisamos do solido pro boolean.

    # FIX: a parede do Home Builder NAO e centrada em Y — ela cresce de y=0 ate y=+T.
    # O cage tambem cresce de (0,0,0) ate (Dim X, Dim Y, Dim Z). Para o cutter
    # atravessar a espessura inteira com folga simetrica, deslocamos so -folga/2 em Y
    # (assim o cubo vai de -folga/2 ate T+folga/2, cobrindo 0..T por completo).
    # (antes eu usava -cut_y/2 supondo parede centrada -> cutter so pegava metade -> marca rasa)
    cage.obj.parent = wall.obj
    cage.obj.location = (offset_x, -folga / 2.0, z)
    cage.obj.rotation_euler = (0, 0, 0)

    # boolean cut na parede (o buraco real)
    mod = wall.obj.modifiers.new(name=f"Boolean_{cage.obj.name}", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cage.obj
    mod.solver = 'EXACT'
    cage.obj.hide_render = True
    cage.obj.display_type = 'WIRE'
    return cage


def build_room_loop(points, height=WALL_HEIGHT, thickness=WALL_THICKNESS, name="Room"):
    """Constroi um anel fechado de paredes ligando os pontos (lista de (x,y)).
    Conecta paredes consecutivas e ajusta mitra de canto (Left/Right Angle).
    Retorna lista de GeoNodeWall.
    """
    walls = []
    n = len(points)
    for i in range(n):
        p0 = Vector((points[i][0], points[i][1], 0))
        p1 = Vector((points[(i + 1) % n][0], points[(i + 1) % n][1], 0))
        seg = p1 - p0
        length = seg.length
        angle = math.degrees(math.atan2(seg.y, seg.x))
        w = new_wall(f"{name}_W{i}", length, p0, angle, thickness, height)
        walls.append(w)

    # mitra de canto: angulo entre paredes consecutivas
    for i in range(n):
        cur = walls[i]
        nxt = walls[(i + 1) % n]
        prv = walls[(i - 1) % n]
        cur_rot = cur.obj.rotation_euler.z
        nxt_rot = nxt.obj.rotation_euler.z
        prv_rot = prv.obj.rotation_euler.z

        turn_r = nxt_rot - cur_rot
        while turn_r > math.pi: turn_r -= 2 * math.pi
        while turn_r < -math.pi: turn_r += 2 * math.pi
        cur.set_input('Right Angle', -turn_r / 2)

        turn_l = cur_rot - prv_rot
        while turn_l > math.pi: turn_l -= 2 * math.pi
        while turn_l < -math.pi: turn_l += 2 * math.pi
        cur.set_input('Left Angle', turn_l / 2)
    return walls


def add_floor(points, name="Floor"):
    """Cria um piso simples (ngon) pelos pontos do contorno externo, em z=0.
    Geometria primitiva so de contexto visual — nao e o objeto do experimento.
    """
    import bmesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    verts = [bm.verts.new((p[0], p[1], -0.001)) for p in points]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()
    return obj
