"""
Pipeline D — a hipotese que segue o que o plugin PEDE.

Nota oficial do autor: "EASY CARDBOARD 3 CURRENTLY REQUIRES A UV MAP."
Interpretacao: o plugin espera uma UV BOA de entrada (em [0,1], faces sas),
e calcula o direction mask em cima dela. Tudo que tentamos antes deixava o
Simple Box Creator gerar a UV alongada (u ate 17) e bakeava nessa zoada.

Ordem correta (a diferenca-chave):
  1. SBC -> apply
  2. smart UV project AGORA (UVMap limpa [0,1])   <- ANTES do EC
  3. EC apply (le essa UV boa pro direction mask)
  4. bake na MESMA UVMap (sem 2a UV, sem re-unwrap)
  5. swap pro Principled mantendo a MESMA UVMap
  6. export

Uso:
  blender --background --python 15_pipeline_D.py -- <preset_name>
"""
import bpy, bmesh, os, sys, math, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUT_DIR = os.path.join(ROOT, "output", "mcp_bake")
os.makedirs(OUT_DIR, exist_ok=True)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PRESET_NAME = argv[0] if argv else "wear_10"

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MAT_NAME = "Easy Cardboard 3"

PRESETS = {
    "used_box": {
        "Thickness": 0.025, "Global Scale": 1.0, "Wear ⏰": 0.4, "Seed \U0001F3B2": 0,
        "Split Angle": 0.5236, "Strength": 0.4, "Separation": 1.0,
        "Separation Noise Scale": 1.0, "Z Position": 1.0,
        " Fibers Density": 5.0, "Fibers Size": 0.02,
        "Displacement Strength": 0.4, "Normal Strength": 1.0, "UV Name": "UVMap",
    },
    "wear_10": {
        "Thickness": 0.01, "Global Scale": 1.0, "Wear ⏰": 1.0, "Seed \U0001F3B2": 0,
        "Split Angle": 0.5236, "Strength": 0.20, "Separation": 1.0,
        "Separation Noise Scale": 0.0, "Z Position": 1.0,
        " Fibers Density": 2.0, "Fibers Size": 0.02,
        "Displacement Strength": 0.161, "Normal Strength": 1.0, "UV Name": "UVMap",
    },
}
PRESET = PRESETS[PRESET_NAME]
BAKE_SIZE = 2048
SLUG = PRESET_NAME + "_D"

def log(m): print(f"[D/{PRESET_NAME}] {m}", flush=True)

def set_input(mod, name, value):
    ng = mod.node_group
    target = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == target:
            mod[item.identifier] = value
            return True
    return False

log("clean + append")
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

log("SBC base")
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
log(f"  post-SBC: {len(obj.data.vertices)}v / {len(obj.data.polygons)}f")

# ============================================================
# DIFERENCA-CHAVE: smart UV project AGORA, antes do EC
# Apaga a UV alongada do SBC e cria uma limpa em [0,1]
# ============================================================
log("Smart UV project (UV boa ANTES do EC)")
# remove qualquer UV existente
while len(obj.data.uv_layers) > 0:
    obj.data.uv_layers.remove(obj.data.uv_layers[0])
obj.data.uv_layers.new(name="UVMap")
obj.data.uv_layers["UVMap"].active = True
obj.data.uv_layers["UVMap"].active_render = True

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, area_weight=0.0)
bpy.ops.object.mode_set(mode='OBJECT')
us = [d.uv[0] for d in obj.data.uv_layers["UVMap"].data]
vs = [d.uv[1] for d in obj.data.uv_layers["UVMap"].data]
log(f"  UVMap (pre-EC) range: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}]")

# ============================================================
# EC apply — agora le a UVMap boa pro direction mask
# ============================================================
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
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="EC")
if not obj.data.materials or obj.data.materials[0] is None:
    obj.data.materials.clear(); obj.data.materials.append(mat_ec)
bpy.ops.object.modifier_apply(modifier="Smooth")
if not obj.data.materials or obj.data.materials[0] is None:
    obj.data.materials.clear(); obj.data.materials.append(mat_ec)

# Confere UV apos EC (o EC pode ter recriado/expandido?)
uv0 = obj.data.uv_layers[0]
uv0.name = "UVMap"
uv0.active = True
uv0.active_render = True
us = [d.uv[0] for d in uv0.data]
vs = [d.uv[1] for d in uv0.data]
log(f"  UVMap (pos-EC) range: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}]  layers={[l.name for l in obj.data.uv_layers]}")

# ============================================================
# Bake na MESMA UVMap (sem 2a UV)
# ============================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
try: scene.cycles.device = 'GPU'
except: pass
scene.cycles.samples = 16
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
scene.render.bake.margin = 8

nt = mat_ec.node_tree
bake_node = nt.nodes.get("BAKE_TARGET")
if bake_node is None:
    bake_node = nt.nodes.new('ShaderNodeTexImage')
    bake_node.name = "BAKE_TARGET"
    bake_node.location = (-1000, -600)

def make_img(name, colorspace):
    if name in bpy.data.images: bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, BAKE_SIZE, BAKE_SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img

def bake_to(image, btype, label, **extras):
    for n in nt.nodes: n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node
    bake_node.image = image
    for o in bpy.data.objects: o.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    log(f"  bake {label}")
    bpy.ops.object.bake(type=btype, use_clear=True, margin=8, **extras)
    p = os.path.join(OUT_DIR, f"ec_{label}_{SLUG}.png")
    image.filepath_raw = p; image.file_format = 'PNG'; image.save()
    log(f"    saved {os.path.basename(p)} {os.path.getsize(p)/(1024*1024):.1f} MB")
    return image

img_color = make_img(f"ec_color_{SLUG}", 'sRGB')
img_normal = make_img(f"ec_normal_{SLUG}", 'Non-Color')
img_rough = make_img(f"ec_rough_{SLUG}", 'Non-Color')

bake_to(img_color, 'DIFFUSE', 'color')
bake_to(img_normal, 'NORMAL', 'normal', normal_space='TANGENT')
bake_to(img_rough, 'ROUGHNESS', 'roughness')

# Swap — MESMA UVMap, so troca material
baked = bpy.data.materials.new(f"EC_Baked_{SLUG}")
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

while len(obj.data.color_attributes) > 0:
    obj.data.color_attributes.remove(obj.data.color_attributes[0])

glb_path = os.path.join(OUT_DIR, f"cardboard_{SLUG}.glb")
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True,
    export_image_format='AUTO',
)
size_mb = os.path.getsize(glb_path)/(1024*1024)
log(f"GLB {os.path.basename(glb_path)} {size_mb:.2f} MB")

# Preview
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800; scene.render.resolution_y = 600
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(OUT_DIR, f"preview_{SLUG}.png")
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data); bpy.context.collection.objects.link(cam)
cam.location = (2.6, -2.6, 1.9); cam.rotation_euler = (math.radians(65), 0, math.radians(45))
scene.camera = cam
sun_data = bpy.data.lights.new("Sun", 'SUN'); sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data); bpy.context.collection.objects.link(sun)
sun.location = (3, -2, 5); sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
world = scene.world or bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0); bg.inputs[1].default_value = 1.0
bpy.ops.render.render(write_still=True)
log(f"preview {os.path.basename(scene.render.filepath)}")

log("=== DONE ===")
print(f"[D/{PRESET_NAME}] === SUCCESS ===", flush=True)
