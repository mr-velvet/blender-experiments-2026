"""
Pipeline completa do experimento "geometria + textura":
SBC -> UV original -> EC preset -> apply -> bake (color+normal+rough alongado) ->
swap por Principled baked -> export GLB com texturas embedded -> preview render.

Tudo headless, 1 unica execucao. Argumento: preset name (used_box ou wear_10).

Uso:
  blender --background --python 12_full_pipeline.py -- <preset_name>
"""
import bpy, bmesh, os, sys, math, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUT_DIR = os.path.join(ROOT, "output", "mcp_bake")
os.makedirs(OUT_DIR, exist_ok=True)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PRESET_NAME = argv[0] if argv else "used_box"

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MAT_NAME = "Easy Cardboard 3"

PRESETS = {
    "used_box": {
        "Thickness": 0.025,
        "Global Scale": 1.0,
        "Wear ⏰": 0.4,
        "Seed \U0001F3B2": 0,
        "Split Angle": 0.5236,
        "Strength": 0.4,
        "Separation": 1.0,
        "Separation Noise Scale": 1.0,
        "Z Position": 1.0,
        " Fibers Density": 5.0,
        "Fibers Size": 0.02,
        "Displacement Strength": 0.4,
        "Normal Strength": 1.0,
        "UV Name": "UVMap",
    },
    "wear_10": {
        "Thickness": 0.01,
        "Global Scale": 1.0,
        "Wear ⏰": 1.0,
        "Seed \U0001F3B2": 0,
        "Split Angle": 0.5236,
        "Strength": 0.20,
        "Separation": 1.0,
        "Separation Noise Scale": 0.0,
        "Z Position": 1.0,
        " Fibers Density": 2.0,
        "Fibers Size": 0.02,
        "Displacement Strength": 0.161,
        "Normal Strength": 1.0,
        "UV Name": "UVMap",
    },
}
PRESET = PRESETS[PRESET_NAME]

def log(m): print(f"[FULL/{PRESET_NAME}] {m}", flush=True)

def set_input(mod, name, value):
    ng = mod.node_group
    target = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == target:
            mod[item.identifier] = value
            return True
    return False

# === 1. clean + append ===
log("Clean + append")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for blk in list(bpy.data.meshes): bpy.data.meshes.remove(blk)
for blk in list(bpy.data.materials): bpy.data.materials.remove(blk)
for blk in list(bpy.data.lights): bpy.data.lights.remove(blk)
for blk in list(bpy.data.cameras): bpy.data.cameras.remove(blk)

with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = [n for n in (NG_BOX, NG_CARDBOARD, NG_SMOOTH) if n in data_from.node_groups]
    data_to.materials = [MAT_NAME]
ng_box = bpy.data.node_groups[NG_BOX]
ng_cb = bpy.data.node_groups[NG_CARDBOARD]
ng_smooth = bpy.data.node_groups[NG_SMOOTH]
mat_ec = bpy.data.materials[MAT_NAME]

# === 2. SBC base ===
log("Build SBC base mesh")
mesh = bpy.data.meshes.new("Box")
obj = bpy.data.objects.new("Box", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
bm.to_mesh(mesh); bm.free()

m_box = obj.modifiers.new("SBC", 'NODES')
m_box.node_group = ng_box
for k, v in {
    'Width': 1.0, 'Length': 1.0, 'Height': 1.0,
    'Gaps (Length)': 0.07, 'Gap (Width)': 0.07, 'Flap Length': 0.11,
    'Simple Sub-D Level': 3, 'CC Sub-D Level': 0,
    'Edge Crease': 0.802, 'Delete Bounds': False,
}.items():
    set_input(m_box, k, v)
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="SBC")
log(f"  SBC: {len(obj.data.vertices)}v / {len(obj.data.polygons)}f")

# === 3. material EC + EC modifier + apply ===
obj.data.materials.clear()
obj.data.materials.append(mat_ec)

m_cb = obj.modifiers.new("EC", 'NODES')
m_cb.node_group = ng_cb
for k, v in PRESET.items():
    set_input(m_cb, k, v)

m_sm = obj.modifiers.new("Smooth", 'NODES')
m_sm.node_group = ng_smooth
set_input(m_sm, 'Angle', math.radians(30.0))
set_input(m_sm, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
bpy.ops.object.modifier_apply(modifier="EC")
if not obj.data.materials or obj.data.materials[0] is None:
    obj.data.materials.clear(); obj.data.materials.append(mat_ec)
bpy.ops.object.modifier_apply(modifier="Smooth")
if not obj.data.materials or obj.data.materials[0] is None:
    obj.data.materials.clear(); obj.data.materials.append(mat_ec)

# Rename UV original
obj.data.uv_layers[0].name = "UV_EC_original"
obj.data.uv_layers["UV_EC_original"].active = True
obj.data.uv_layers["UV_EC_original"].active_render = True
us = [d.uv[0] for d in obj.data.uv_layers["UV_EC_original"].data]
log(f"  after EC: {len(obj.data.vertices)}v / {len(obj.data.polygons)}f  UV u_max={max(us):.2f}")

# === 4. Bake setup ===
u_max = max(us)
BAKE_H = 1024
# largura proporcional ao u_max, multiplo de 256 pra alinhar
BAKE_W = int(math.ceil(u_max * 1024 / 256) * 256)
log(f"  bake size: {BAKE_W} x {BAKE_H}")

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
try: scene.cycles.device = 'GPU'
except: pass
scene.cycles.samples = 16
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
scene.render.bake.margin = 4

nt = mat_ec.node_tree
bake_node = nt.nodes.get("BAKE_TARGET")
if bake_node is None:
    bake_node = nt.nodes.new('ShaderNodeTexImage')
    bake_node.name = "BAKE_TARGET"
    bake_node.location = (-1000, -600)

def make_img(name, colorspace):
    if name in bpy.data.images: bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, BAKE_W, BAKE_H, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img

def bake_to(image, btype, label, **extras):
    for n in nt.nodes: n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node
    bake_node.image = image
    for o in bpy.data.objects: o.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    log(f"  bake {label} ({btype})")
    bpy.ops.object.bake(type=btype, use_clear=True, margin=4, **extras)
    p = os.path.join(OUT_DIR, f"ec_{label}_{PRESET_NAME}.png")
    image.filepath_raw = p; image.file_format = 'PNG'; image.save()
    log(f"    saved {os.path.basename(p)} {os.path.getsize(p)/(1024*1024):.1f} MB")
    return image

img_color = make_img(f"ec_color_{PRESET_NAME}", 'sRGB')
img_normal = make_img(f"ec_normal_{PRESET_NAME}", 'Non-Color')
img_rough = make_img(f"ec_rough_{PRESET_NAME}", 'Non-Color')

bake_to(img_color, 'DIFFUSE', 'color')
bake_to(img_normal, 'NORMAL', 'normal', normal_space='TANGENT')
bake_to(img_rough, 'ROUGHNESS', 'roughness')

# === 5. Swap por Principled baked ===
baked = bpy.data.materials.new(f"EC_Baked_{PRESET_NAME}")
baked.use_nodes = True
bnt = baked.node_tree
for n in list(bnt.nodes): bnt.nodes.remove(n)
out = bnt.nodes.new('ShaderNodeOutputMaterial'); out.location=(400,0)
bsdf = bnt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(100,0)
bnt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = bnt.nodes.new('ShaderNodeTexImage'); tc.image=img_color; tc.location=(-500,250)
bnt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
tr = bnt.nodes.new('ShaderNodeTexImage'); tr.image=img_rough; tr.location=(-500,-50)
bnt.links.new(tr.outputs['Color'], bsdf.inputs['Roughness'])
tn = bnt.nodes.new('ShaderNodeTexImage'); tn.image=img_normal; tn.location=(-500,-350)
nm = bnt.nodes.new('ShaderNodeNormalMap'); nm.location=(-150,-350)
bnt.links.new(tn.outputs['Color'], nm.inputs['Color'])
bnt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
obj.data.materials.clear()
obj.data.materials.append(baked)
obj.data.uv_layers["UV_EC_original"].active = True
obj.data.uv_layers["UV_EC_original"].active_render = True

# === 6. Export GLB ===
glb_path = os.path.join(OUT_DIR, f"cardboard_{PRESET_NAME}.glb")
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True); bpy.context.view_layer.objects.active = obj
log(f"Export GLB")
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True,
    export_image_format='AUTO',
)
size_mb = os.path.getsize(glb_path)/(1024*1024)
log(f"  GLB {os.path.basename(glb_path)}  {size_mb:.2f} MB")

# === 7. Eevee preview ===
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(OUT_DIR, f"preview_{PRESET_NAME}.png")
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (2.6, -2.6, 1.9)
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
scene.camera = cam
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (3, -2, 5); sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0); bg.inputs[1].default_value = 1.0
bpy.ops.render.render(write_still=True)
log(f"preview {os.path.basename(scene.render.filepath)}")

# === 8. Stats ===
stats = {
    "preset": PRESET_NAME,
    "bake_w": BAKE_W, "bake_h": BAKE_H,
    "verts": len(obj.data.vertices), "faces": len(obj.data.polygons),
    "u_max": u_max,
    "glb_mb": size_mb,
}
stats_path = os.path.join(OUT_DIR, f"stats_{PRESET_NAME}.json")
with open(stats_path, "w") as f: json.dump(stats, f, indent=2)
log(f"stats {os.path.basename(stats_path)}")
log("=== DONE ===")
print(f"[FULL/{PRESET_NAME}] === SUCCESS ===", flush=True)
