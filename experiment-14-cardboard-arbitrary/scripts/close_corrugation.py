"""
Close-up da corrugacao na casa de papelao, no nivel de Separation escolhido.
Mostra as 'ondinhas' do miolo corrugado entre os cortes/abas.

Uso:
  blender --background --python close_corrugation.py -- <glb> <sep> <tag> [res] [samples]
"""
import bpy, os, sys, math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
GLB = argv[0]
SEP = float(argv[1])
TAG = argv[2]
RES = int(argv[3]) if len(argv) > 3 else 700
SAMPLES = int(argv[4]) if len(argv) > 4 else 48

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(os.path.dirname(ROOT),
                           "experiment-13-easy-cardboard",
                           "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "model_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"
MATERIAL_NAME = "Easy Cardboard 3"

def log(m): print(f"[CLOSE] {m}", flush=True)

AGED = {
    "Thickness": 0.006, "Global Scale": 0.5, "Wear ⏰": 0.7,
    "Seed \U0001F3B2": 7, "Split Angle": math.radians(35), "Strength": 0.35,
    "Separation": SEP, "Separation Noise Scale": 0.0, "Z Position": 1.0,
    " Fibers Density": 8.0, "Fibers Size": 0.02, "Displacement Strength": 0.4,
    "Normal Strength": 1.0, "Roughness ": 0.9, "Metallic": 0.0, "UV Name": "UVMap",
}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for c in list(bpy.data.materials): bpy.data.materials.remove(c)

with bpy.data.libraries.load(ASSET_BLEND, link=False) as (src, dst):
    dst.node_groups = [NODE_GROUP_NAME]
    dst.materials = [MATERIAL_NAME]
cardboard_ng = bpy.data.node_groups.get(NODE_GROUP_NAME)
cardboard_mat = bpy.data.materials.get(MATERIAL_NAME)

bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = "house"
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.ops.object.transform_apply(location=True)
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
obj.scale = (0.3/maxdim,)*3
bpy.ops.object.transform_apply(scale=True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
if obj.data.uv_layers:
    obj.data.uv_layers[0].name = 'UVMap'
    obj.data.uv_layers[0].active_render = True

obj.data.materials.clear()
obj.data.materials.append(cardboard_mat)
mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
mod.node_group = cardboard_ng
def set_input(name, value):
    for item in mod.node_group.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == name.strip():
            try: mod[item.identifier] = value; return True
            except Exception as e: log(f"FAIL {name}: {e}"); return False
    log(f"socket '{name}' nao achado"); return False
for k, v in AGED.items(): set_input(k, v)
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="EasyCardboard")

scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.render.resolution_x = RES
scn.render.resolution_y = RES
world = bpy.data.worlds[0]; scn.world = world; world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05,0.05,0.06,1.0); bg.inputs[1].default_value = 1.0
def add_area(name, loc, energy, size):
    ld = bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.size=size
    lo = bpy.data.objects.new(name,ld); lo.location=loc
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler=(-1*lo.location).to_track_quat('-Z','Y').to_euler(); return lo
add_area("key", Vector((0.35,-0.3,0.45)),70,0.4)
add_area("fill", Vector((-0.4,-0.2,0.2)),20,0.6)
add_area("rim", Vector((0.0,0.4,0.35)),50,0.35)

bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
md = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
top_z = max(p[2] for p in bb)

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 70
cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
scn.camera = cam

# closes mirando na quina do telhado (onde a corrugacao aparece nos cortes).
# A corrugacao (ondinhas) so aparece nas BORDAS/quinas, onde o miolo fica
# exposto -- nao no meio de uma face lisa. Camera media (nao colada) pra
# pegar a aresta inteira do telhado com varias fileiras de ondinha.
targets = [
    Vector((0.0, -md*0.05, top_z*0.45)),   # cumeeira/aresta do telhado
    Vector((md*0.30, 0.0,  top_z*0.30)),   # quina parede-telhado lateral
]
cr = md * 1.1
for i, tgt in enumerate(targets):
    az = math.radians(40 + i*90); el = math.radians(22)
    c = tgt + Vector((cr*math.cos(az)*math.cos(el),
                      cr*math.sin(az)*math.cos(el),
                      cr*math.sin(el)))
    cam.location = c
    cam.rotation_euler = (tgt - c).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    p = os.path.join(OUTPUT_DIR, f"close_{TAG}_{i}.png")
    scn.render.filepath = p
    log(f"Render {TAG} close{i} -> {p}")
    bpy.ops.render.render(write_still=True)

log("DONE close")
print("[CLOSE] === SUCCESS ===", flush=True)
