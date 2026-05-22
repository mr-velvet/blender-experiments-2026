"""
Renderiza N variacoes do Easy Cardboard 3.x num so processo Blender (1x asset load).
TUDO via os 2 node groups do asset (Simple Box Creator + Easy Cardboard 3.0) — zero
codigo manual de geometria.

Cada variacao eh um dict com:
  name: str  (vai virar arquivo PNG)
  box: dict de overrides do Simple Box Creator
  cb:  dict de overrides do Easy Cardboard 3.0

Args:
  matrix_json_path  — path pra json com a lista de variacoes
"""
import bpy, bmesh, json, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MATERIAL_NAME = "Easy Cardboard 3"

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MATRIX_PATH = argv[0] if argv else os.path.join(ROOT, "matrix.json")
SUBDIR = argv[1] if len(argv) > 1 else ''

def log(m):
    print(f"[MATRIX] {m}", flush=True)

with open(MATRIX_PATH) as f:
    matrix = json.load(f)

log(f"Loaded matrix: {len(matrix)} variations")
log(f"Output subdir: '{SUBDIR}'")

# ---- 1. one-time setup: append node groups + material + setup scene ----
log(f"Appending from {ASSET_BLEND}")
# clean
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.meshes):
    bpy.data.meshes.remove(block)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)
for block in list(bpy.data.lights):
    bpy.data.lights.remove(block)

with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = [n for n in [NG_BOX, NG_CARDBOARD, NG_SMOOTH] if n in data_from.node_groups]
    if MATERIAL_NAME in data_from.materials:
        data_to.materials = [MATERIAL_NAME]

ng_box = bpy.data.node_groups[NG_BOX]
ng_cb = bpy.data.node_groups[NG_CARDBOARD]
ng_smooth = bpy.data.node_groups[NG_SMOOTH]
mat = bpy.data.materials[MATERIAL_NAME]

# camera + light + world (reuse across renders)
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (1.7, -2.3, 1.5)
target = Vector((0, 0, 0.4))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam_obj

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.angle = 0.05
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.location = (3, -3, 5)
sun_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))

world = bpy.context.scene.world or bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0)
    bg.inputs[1].default_value = 0.6

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 32
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.view_settings.view_transform = 'AgX'

# ---- 2. helper to build the object with current params ----
def set_input(mod, name, value):
    ng = mod.node_group
    name_clean = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name.strip() == name_clean:
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"     FAIL set '{name}'={value}: {e}")
                return False
    return False

BOX_DEFAULTS = {
    'Width': 1.0, 'Length': 1.0, 'Height': 1.0,
    'Gaps (Length)': 0.07, 'Gap (Width)': 0.07,
    'Flap Length': 0.11,
    'Simple Sub-D Level': 3, 'CC Sub-D Level': 0,
    'Edge Crease': 0.802, 'Delete Bounds': False,
}

CB_DEFAULTS = {
    'Thickness': 0.01, 'Global Scale': 1.0,
    'Wear ⏰': 0.174, 'Seed \U0001F3B2': 0,
    'Split Angle': 0.5236, 'Strength': 0.2,
    'Separation': 1.0, 'Separation Noise Scale': 0.0, 'Z Position': 1.0,
    ' Fibers Density': 2.0, 'Fibers Size': 0.02,
    'Roughness ': 1.0, 'Metallic': 0.0, 'Clearcoat': 0.0,
    'Displacement Strength': 0.161, 'Normal Strength': 1.0,
    'Print Roughness': 0.5,
    'Direction Mask Threshold': 2.0, 'Invert': False,
    'UV Name': 'UVMap',
}

def build_box(box_overrides, cb_overrides):
    # remove previous Box object if any
    for o in list(bpy.data.objects):
        if o.name.startswith('Box'):
            bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.name.startswith('Box'):
            bpy.data.meshes.remove(m)

    mesh = bpy.data.meshes.new("Box")
    obj = bpy.data.objects.new("Box", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
    bm.to_mesh(mesh)
    bm.free()

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.data.materials.clear()
    obj.data.materials.append(mat)

    m1 = obj.modifiers.new(name="Simple Box Creator", type='NODES')
    m1.node_group = ng_box
    for k, v in {**BOX_DEFAULTS, **box_overrides}.items():
        set_input(m1, k, v)

    m2 = obj.modifiers.new(name="GeometryNodes", type='NODES')
    m2.node_group = ng_cb
    for k, v in {**CB_DEFAULTS, **cb_overrides}.items():
        set_input(m2, k, v)

    m3 = obj.modifiers.new(name="Smooth by Angle", type='NODES')
    m3.node_group = ng_smooth
    set_input(m3, 'Angle', 0.5236)
    set_input(m3, 'Ignore Sharpness', False)

    bpy.context.view_layer.update()
    return obj

# ---- 3. render each variation ----
sub_dir = os.path.join(OUTPUT_DIR, SUBDIR) if SUBDIR else OUTPUT_DIR
os.makedirs(sub_dir, exist_ok=True)

for i, variation in enumerate(matrix):
    name = variation['name']
    log(f"[{i+1}/{len(matrix)}] {name}")
    obj = build_box(variation.get('box', {}), variation.get('cb', {}))

    out_path = os.path.join(sub_dir, f"{name}.png")
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    log(f"   saved -> {out_path}")

log(f"=== ALL {len(matrix)} RENDERS DONE ===")
print("[MATRIX] === SUCCESS ===", flush=True)
