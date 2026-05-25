"""
SWEEP de agressividade do Easy Cardboard numa casa de parede fina.

Objetivo do experimento: o parametro que ARRANCA cada plano da posicao
original (estilhacando a casa em cacos) e o 'Separation' (+ 'Separation
Noise Scale'). Esta rodada varre 4 niveis de Separation mantendo TODO o
resto do envelhecimento ligado (Wear, Displacement, Fibras, Roughness),
pra achar o teto onde a casa AINDA parece casa mas ja tem look de papelao
velho.

Estrategia: importa/normaliza/UV a casa UMA vez, guarda a malha base limpa,
e pra cada nivel duplica a base, aplica o modifier com o Separation daquele
nivel e renderiza 1 vista geral. No nivel escolhido depois faz-se o close.

Uso:
  blender --background --python sweep_separation.py -- <glb> [res] [samples]

Saidas: ../output/model_renders/sweep_sepNN_*.png
"""
import bpy, os, sys, math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
GLB = argv[0]
RES = int(argv[1]) if len(argv) > 1 else 512
SAMPLES = int(argv[2]) if len(argv) > 2 else 32

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(os.path.dirname(ROOT),
                           "experiment-13-easy-cardboard",
                           "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "model_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"
MATERIAL_NAME = "Easy Cardboard 3"

def log(m): print(f"[SWEEP] {m}", flush=True)

# base de envelhecimento (igual ao AGED legivel) — tudo que NAO entorta:
BASE_AGED = {
    "Thickness": 0.006,
    "Global Scale": 0.5,
    "Wear ⏰": 0.7,
    "Seed \U0001F3B2": 7,
    "Split Angle": math.radians(35),
    "Strength": 0.35,
    "Z Position": 1.0,
    " Fibers Density": 8.0,
    "Fibers Size": 0.02,
    "Displacement Strength": 0.4,
    "Normal Strength": 1.0,
    "Roughness ": 0.9,
    "Metallic": 0.0,
    "UV Name": "UVMap",
}

# os 4 niveis variam SO o que arranca o plano:
LEVELS = [
    {"tag": "sep00", "Separation": 0.0, "Separation Noise Scale": 0.0},
    {"tag": "sep03", "Separation": 0.3, "Separation Noise Scale": 0.0},
    {"tag": "sep06", "Separation": 0.6, "Separation Noise Scale": 0.0},
    {"tag": "sep10", "Separation": 1.0, "Separation Noise Scale": 0.0},
]

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
for o in bpy.data.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
base = bpy.context.active_object
base.name = "house_base"

bpy.context.view_layer.objects.active = base
base.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.context.view_layer.update()
bb = [base.matrix_world @ Vector(c) for c in base.bound_box]
center = sum(bb, Vector()) / 8.0
base.location -= center
bpy.ops.object.transform_apply(location=True)
bb = [base.matrix_world @ Vector(c) for c in base.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
s = 0.3 / maxdim
base.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
log(f"  base mesh: {len(base.data.vertices)} verts, {len(base.data.polygons)} faces")

# ---- smart UV ----
log("Smart UV project")
bpy.context.view_layer.objects.active = base
for o in bpy.data.objects: o.select_set(False)
base.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
if base.data.uv_layers:
    base.data.uv_layers[0].name = 'UVMap'
    base.data.uv_layers[0].active_render = True

# ---- cena (uma vez) ----
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

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 50
cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
scn.camera = cam

def set_input(mod, name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == name.strip():
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"  FAIL '{name}': {e}"); return False
    log(f"  socket '{name}' nao encontrado")
    return False

# esconde a base do render
base.hide_render = True

for lvl in LEVELS:
    tag = lvl["tag"]
    log(f"=== nivel {tag}: Separation={lvl['Separation']} ===")
    # duplica base
    for o in bpy.data.objects: o.select_set(False)
    base.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.duplicate()
    obj = bpy.context.active_object
    obj.name = f"house_{tag}"
    obj.hide_render = False

    obj.data.materials.clear()
    obj.data.materials.append(cardboard_mat)
    mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
    mod.node_group = cardboard_ng

    params = dict(BASE_AGED)
    params["Separation"] = lvl["Separation"]
    params["Separation Noise Scale"] = lvl["Separation Noise Scale"]
    for k, v in params.items():
        set_input(mod, k, v)
    bpy.context.view_layer.update()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="EasyCardboard")
    log(f"  apos apply: {len(obj.data.polygons)} faces")

    # recentra + dimensiona camera neste obj
    bpy.context.view_layer.update()
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(bb, Vector()) / 8.0
    obj.location -= center
    bpy.context.view_layer.update()
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    md = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))

    # 1 vista geral (3/4 frontal)
    radius = md * 1.9
    elev = math.radians(18)
    az = math.radians(35)
    c = Vector((radius*math.cos(az)*math.cos(elev),
                radius*math.sin(az)*math.cos(elev),
                radius*math.sin(elev)))
    cam_d.lens = 50
    cam.location = c
    cam.rotation_euler = (Vector((0,0,0)) - c).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    p = os.path.join(OUTPUT_DIR, f"sweep_{tag}_a0.png")
    scn.render.filepath = p
    log(f"Render {tag} -> {p}")
    bpy.ops.render.render(write_still=True)

    # remove esse obj antes do proximo nivel
    obj.hide_render = True
    bpy.data.objects.remove(obj, do_unlink=True)

log("DONE sweep")
print("[SWEEP] === SUCCESS ===", flush=True)
