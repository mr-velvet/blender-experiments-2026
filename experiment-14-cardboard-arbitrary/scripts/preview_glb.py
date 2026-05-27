"""
Preview rapido de um GLB importado (SEM papelao) so pra ver a forma e decidir
qual modelo usar. Junta as meshes, normaliza escala, renderiza 2 angulos baixa-res.

Uso: blender --background --python preview_glb.py -- <glb_path> <out_prefix>
"""
import bpy, os, sys, math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
GLB = argv[0]
OUT = argv[1] if len(argv) > 1 else "preview"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
OUTDIR = os.path.join(ROOT, "output", "model_preview")
os.makedirs(OUTDIR, exist_ok=True)

def log(m): print(f"[PREV] {m}", flush=True)

# clean
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

log(f"Import {GLB}")
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
log(f"  {len(meshes)} mesh objects")
total_v = sum(len(o.data.vertices) for o in meshes)
log(f"  total verts: {total_v}")

# junta tudo
for o in bpy.data.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object

# normaliza: centra na origem, escala pra caber em ~0.3
bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
s = 0.3 / maxdim
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)

# render setup eevee rapido
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 480
scn.render.resolution_y = 480
world = scn.world or bpy.data.worlds.new("W")
scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 1.5

sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 4
sun = bpy.data.objects.new("Sun", sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(40))

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 45
cam = bpy.data.objects.new("Cam", cam_d); bpy.context.collection.objects.link(cam)
scn.camera = cam

bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
radius = maxdim * 2.0
for i, az_deg in enumerate([35, 135]):
    az = math.radians(az_deg); elev = math.radians(20)
    c = Vector((radius*math.cos(az)*math.cos(elev), radius*math.sin(az)*math.cos(elev), radius*math.sin(elev)))
    cam.location = c
    cam.rotation_euler = (-c).to_track_quat('-Z', 'Y').to_euler()
    p = os.path.join(OUTDIR, f"{OUT}_a{i}.png")
    scn.render.filepath = p
    bpy.ops.render.render(write_still=True)
    log(f"  -> {p}")
log("DONE")
