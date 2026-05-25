"""
Testa o Easy Cardboard 3.0 em geometrias ARBITRARIAS (improvaveis de serem
papelao). Para cada forma: gera mesh -> smart UV -> append node group +
material -> aplica modifier -> renderiza N angulos em Cycles baixa-res.

Uso:
    blender --background --python render_shape.py -- <shape> [res] [samples]

<shape>: torus | knot | sphere | monkey | cone | spiral
Render direto com o shader nativo do asset (sem bake, sem GLB).

Saidas em ../output/renders/<shape>_a{0..N}.png
"""
import bpy
import bmesh
import math
import os
import sys

# ---- args ----
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
SHAPE = argv[0] if len(argv) > 0 else "torus"
RES = int(argv[1]) if len(argv) > 1 else 640
SAMPLES = int(argv[2]) if len(argv) > 2 else 24

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
# o asset comercial vive no experimento 13
ASSET_BLEND = os.path.join(os.path.dirname(ROOT),
                           "experiment-13-easy-cardboard",
                           "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"  # 📦 Easy Cardboard 3.0
MATERIAL_NAME = "Easy Cardboard 3"

def log(m):
    print(f"[ARB] {m}", flush=True)

# ---- 1. clean ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for c in list(bpy.data.materials): bpy.data.materials.remove(c)

# ---- 2. append node group + material ----
log(f"Appending Easy Cardboard from {ASSET_BLEND}")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (src, dst):
    if NODE_GROUP_NAME not in src.node_groups:
        raise RuntimeError(f"node group nao encontrado. disponiveis: {list(src.node_groups)[:10]}")
    dst.node_groups = [NODE_GROUP_NAME]
    dst.materials = [MATERIAL_NAME]
cardboard_ng = bpy.data.node_groups.get(NODE_GROUP_NAME)
cardboard_mat = bpy.data.materials.get(MATERIAL_NAME)
log(f"  node group: {cardboard_ng}  material: {cardboard_mat}")

# ---- 3. build the arbitrary mesh ----
log(f"Building shape: {SHAPE}")

def new_obj_from_bm(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o

if SHAPE == "torus":
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.045,
                                     major_segments=64, minor_segments=24)
    obj = bpy.context.active_object
elif SHAPE == "knot":
    # toro com no (trefoil-ish) via curva -> mesh
    bm = bmesh.new()
    N = 220
    verts = []
    for i in range(N):
        t = (i / N) * 2 * math.pi
        x = math.sin(t) + 2 * math.sin(2 * t)
        y = math.cos(t) - 2 * math.cos(2 * t)
        z = -math.sin(3 * t)
        verts.append(bm.verts.new((x * 0.04, y * 0.04, z * 0.04)))
    for i in range(N):
        bm.edges.new((verts[i], verts[(i + 1) % N]))
    tmp = new_obj_from_bm(bm, "knot_curve")
    # skin + subsurf pra dar volume tubular
    sk = tmp.modifiers.new("skin", 'SKIN')
    bpy.context.view_layer.objects.active = tmp
    tmp.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.skin_resize(value=(0.6, 0.6, 0.6))
    bpy.ops.object.mode_set(mode='OBJECT')
    ss = tmp.modifiers.new("ss", 'SUBSURF'); ss.levels = 2; ss.render_levels = 2
    bpy.ops.object.modifier_apply(modifier="skin")
    bpy.ops.object.modifier_apply(modifier="ss")
    obj = tmp
elif SHAPE == "sphere":
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=48, ring_count=32)
    obj = bpy.context.active_object
elif SHAPE == "monkey":
    bpy.ops.mesh.primitive_monkey_add(size=0.2)
    obj = bpy.context.active_object
    ss = obj.modifiers.new("ss", 'SUBSURF'); ss.levels = 2
    bpy.ops.object.modifier_apply(modifier="ss")
elif SHAPE == "cone":
    bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0.0, depth=0.22,
                                    vertices=48)
    obj = bpy.context.active_object
    # subdividir pra dar verts ao solidify
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode='OBJECT')
elif SHAPE == "spiral":
    # espiral/mola
    bm = bmesh.new()
    N = 260
    verts = []
    for i in range(N):
        t = (i / N) * 2 * math.pi * 4
        r = 0.08
        x = r * math.cos(t)
        y = r * math.sin(t)
        z = (i / N) * 0.18 - 0.09
        verts.append(bm.verts.new((x, y, z)))
    for i in range(N - 1):
        bm.edges.new((verts[i], verts[i + 1]))
    tmp = new_obj_from_bm(bm, "spiral_curve")
    sk = tmp.modifiers.new("skin", 'SKIN')
    bpy.context.view_layer.objects.active = tmp
    tmp.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.skin_resize(value=(0.35, 0.35, 0.35))
    bpy.ops.object.mode_set(mode='OBJECT')
    ss = tmp.modifiers.new("ss", 'SUBSURF'); ss.levels = 2
    bpy.ops.object.modifier_apply(modifier="skin")
    bpy.ops.object.modifier_apply(modifier="ss")
    obj = tmp
else:
    raise RuntimeError(f"shape desconhecida: {SHAPE}")

obj.name = f"shape_{SHAPE}"
# zera rotacao herdada
obj.rotation_euler = (0, 0, 0)
log(f"  base mesh: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ---- 4. UV smart project (asset exige UV map) ----
log("Smart UV project")
bpy.context.view_layer.objects.active = obj
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- 5. material + modifier ----
obj.data.materials.clear()
obj.data.materials.append(cardboard_mat)

mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
mod.node_group = cardboard_ng

def set_input(socket_name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name.strip() == socket_name.strip():
            try:
                mod[item.identifier] = value
                log(f"  set '{socket_name}' = {value}")
                return True
            except Exception as e:
                log(f"  FAIL set '{socket_name}': {e}")
                return False
    log(f"  socket '{socket_name}' nao encontrado")
    return False

set_input('Thickness', 0.003)
set_input('Global Scale', 0.5)
set_input('Wear ⏰', 0.08)
set_input('Seed \U0001F3B2', 7)
set_input('Strength', 0.3)
set_input('Roughness ', 0.75)
set_input('Metallic', 0.0)
set_input('Normal Strength', 0.8)
set_input('Displacement Strength', 0.15)
set_input(' Fibers Density', 1.0)
set_input('Fibers Size', 0.4)

bpy.context.view_layer.update()

# ---- 6. aplica o modifier (congela geometria) ----
log("Applying modifier")
bpy.context.view_layer.objects.active = obj
try:
    bpy.ops.object.modifier_apply(modifier="EasyCardboard")
    log(f"  apos apply: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")
except Exception as e:
    log(f"  APPLY FALHOU: {e}")
    raise

# ---- 7. cena: luz, mundo, camera, render settings ----
log("Setting up scene / lighting / camera")
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.render.resolution_x = RES
scene.render.resolution_y = RES
scene.render.film_transparent = False

# world: cinza claro com leve gradiente via background
world = bpy.data.worlds.new("W") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs[1].default_value = 1.0

# tres luzes (key/fill/rim) - area lights
def add_area(name, loc, energy, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    bpy.context.collection.objects.link(lo)
    # apontar para origem
    direction = -1 * (lo.location)
    lo.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return lo

from mathutils import Vector
add_area("key", Vector((0.35, -0.3, 0.45)), 60, 0.5)
add_area("fill", Vector((-0.4, -0.2, 0.2)), 25, 0.6)
add_area("rim", Vector((0.0, 0.4, 0.35)), 40, 0.4)

# centraliza objeto na origem (usa bound box)
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.context.view_layer.update()

# raio aproximado pra enquadrar
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
radius = maxdim * 1.9

# camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam
cam_data.lens = 50

# ---- 8. renderiza N angulos orbitando ----
angles = [0, 60, 130, 220]  # graus em azimute
elev = math.radians(22)
n = 0
for az_deg in angles:
    az = math.radians(az_deg)
    cx = radius * math.cos(az) * math.cos(elev)
    cy = radius * math.sin(az) * math.cos(elev)
    cz = radius * math.sin(elev)
    cam.location = Vector((cx, cy, cz))
    # mira na origem
    look = -Vector((cx, cy, cz))
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    out = os.path.join(OUTPUT_DIR, f"{SHAPE}_a{n}.png")
    scene.render.filepath = out
    log(f"Render angle {az_deg}deg -> {out}")
    bpy.ops.render.render(write_still=True)
    n += 1

log(f"DONE shape={SHAPE} ({n} renders)")
print("[ARB] === SUCCESS ===", flush=True)
