"""
Aplica o Easy Cardboard 3.0 (preset ENVELHECIDO / AGED) num modelo 3D
arbitrario baixado de fora (GLB CC0). Pipeline 100% headless.

Fluxo:
  importa GLB -> junta meshes -> normaliza -> smart UV -> append node group +
  material do asset -> seta preset AGED -> aplica modifier -> render Cycles
  em varios angulos orbitais + CLOSE-UPS nas bordas (onde a corrugacao aparece).

Uso:
  blender --background --python render_model.py -- <glb> <prefix> [res] [samples]

Saidas: ../output/model_renders/<prefix>_*.png
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
GLB = argv[0]
PREFIX = argv[1] if len(argv) > 1 else "model"
RES = int(argv[2]) if len(argv) > 2 else 800
SAMPLES = int(argv[3]) if len(argv) > 3 else 48

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(os.path.dirname(ROOT),
                           "experiment-13-easy-cardboard",
                           "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "model_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"
MATERIAL_NAME = "Easy Cardboard 3"

def log(m): print(f"[MODEL] {m}", flush=True)

# === preset ENVELHECIDO (AGED) — identico ao 16_aged_box do exp 13 ===
# Wear alto, edge split medio, separacao das abas, displacement e fibras
# fortes = papelao bem velho. Split Angle fica no default oficial (30deg).
# AGED "legivel": envelhecimento vem de Wear+Displacement+Fibras+Roughness.
# Separation fica no default (1.0) e Sep Noise em 0 — em malha de paredes finas
# o Separation alto do preset-caixa estilhaca a forma em cacos. Aqui ele fica
# contido pra preservar a casa e deixar a corrugacao legivel.
AGED = {
    "Thickness": 0.006,            # parede mais grossa (relativo a escala 0.3)
    "Global Scale": 0.5,
    "Wear ⏰": 0.7,                # desgaste/sujeira de papelao velho
    "Seed \U0001F3B2": 7,
    "Split Angle": math.radians(35),
    "Strength": 0.35,             # edge split contido (nao rasga paredes finas)
    "Separation": 1.0,            # default — NAO estilhaca
    "Separation Noise Scale": 0.0,
    "Z Position": 1.0,
    " Fibers Density": 8.0,
    "Fibers Size": 0.02,
    "Displacement Strength": 0.4, # corrugacao marcada mas sem explodir
    "Normal Strength": 1.0,
    "Roughness ": 0.9,
    "Metallic": 0.0,
    "UV Name": "UVMap",
}

# ---- clean ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for c in list(bpy.data.materials): bpy.data.materials.remove(c)

# ---- append cardboard ----
log(f"Append Easy Cardboard from {ASSET_BLEND}")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (src, dst):
    dst.node_groups = [NODE_GROUP_NAME]
    dst.materials = [MATERIAL_NAME]
cardboard_ng = bpy.data.node_groups.get(NODE_GROUP_NAME)
cardboard_mat = bpy.data.materials.get(MATERIAL_NAME)

# ---- import GLB ----
log(f"Import {GLB}")
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
log(f"  {len(meshes)} mesh objs, {sum(len(o.data.vertices) for o in meshes)} verts total")

# join
for o in bpy.data.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = f"model_{PREFIX}"

# zera rotacao do import gltf (vem +90 X as vezes) aplicando transform
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# normaliza escala/posicao
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.ops.object.transform_apply(location=True)
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
s = 0.3 / maxdim
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
log(f"  base mesh: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ---- smart UV (asset exige UVMap) ----
log("Smart UV project")
bpy.context.view_layer.objects.active = obj
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
if obj.data.uv_layers:
    obj.data.uv_layers[0].name = 'UVMap'
    obj.data.uv_layers[0].active_render = True

# ---- material + modifier com preset AGED ----
obj.data.materials.clear()
obj.data.materials.append(cardboard_mat)
mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
mod.node_group = cardboard_ng

def set_input(name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == name.strip():
            try:
                mod[item.identifier] = value
                log(f"  set '{name}' = {value}")
                return True
            except Exception as e:
                log(f"  FAIL '{name}': {e}"); return False
    log(f"  socket '{name}' nao encontrado")
    return False

log("Aplicando preset AGED (papelao envelhecido)")
for k, v in AGED.items():
    set_input(k, v)
bpy.context.view_layer.update()

# aplica modifier
log("Applying modifier")
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="EasyCardboard")
log(f"  apos apply: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ---- cena ----
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.render.resolution_x = RES
scn.render.resolution_y = RES

world = bpy.data.worlds[0] if bpy.data.worlds else bpy.data.worlds.new("W")
scn.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs[1].default_value = 1.0

def add_area(name, loc, energy, size):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = (-1*lo.location).to_track_quat('-Z', 'Y').to_euler()
    return lo

add_area("key", Vector((0.35, -0.3, 0.45)), 60, 0.5)
add_area("fill", Vector((-0.4, -0.2, 0.2)), 25, 0.6)
add_area("rim", Vector((0.0, 0.4, 0.35)), 45, 0.4)

# recentra
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 50
cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
scn.camera = cam

def shoot(name, cam_loc, lens=50, look_at=None):
    cam_d.lens = lens
    cam.location = cam_loc
    target = look_at if look_at is not None else Vector((0, 0, 0))
    cam.rotation_euler = (target - cam_loc).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    p = os.path.join(OUTPUT_DIR, f"{PREFIX}_{name}.png")
    scn.render.filepath = p
    log(f"Render {name} -> {p}")
    bpy.ops.render.render(write_still=True)

# --- 4 angulos orbitais (visao geral) ---
radius = maxdim * 1.9
elev = math.radians(20)
for i, az_deg in enumerate([20, 110, 200, 300]):
    az = math.radians(az_deg)
    c = Vector((radius*math.cos(az)*math.cos(elev),
                radius*math.sin(az)*math.cos(elev),
                radius*math.sin(elev)))
    shoot(f"orbit{i}", c, lens=50)

# --- 3 CLOSE-UPS nas bordas (corrugacao / ondinhas entre cortes) ---
# camera perto, lente longa, mirando em pontos da quina superior do volume
top_z = max(p[2] for p in bb) * 0.6
close_targets = [
    Vector((maxdim*0.18, -maxdim*0.18, top_z)),
    Vector((-maxdim*0.20, maxdim*0.05, maxdim*0.1)),
    Vector((maxdim*0.05, maxdim*0.22, -maxdim*0.05)),
]
cr = maxdim * 0.75
for i, tgt in enumerate(close_targets):
    az = math.radians(35 + i*120); el = math.radians(12)
    c = tgt + Vector((cr*math.cos(az)*math.cos(el),
                      cr*math.sin(az)*math.cos(el),
                      cr*math.sin(el)))
    shoot(f"close{i}", c, lens=85, look_at=tgt)

log(f"DONE model={PREFIX}")
print("[MODEL] === SUCCESS ===", flush=True)
