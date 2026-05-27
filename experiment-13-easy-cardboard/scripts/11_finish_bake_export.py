"""
Continua o bake a partir do .blend salvo via MCP.
Color ja foi bakeado (ec_color_long.png 11MB existe). Faz normal e roughness,
faz o swap pro material baked e exporta GLB.

Tudo numa unica execucao headless pra escapar do timeout do MCP.

Uso:
  blender --background bake_state.blend --python 11_finish_bake_export.py -- <preset_slug>

preset_slug fica no nome do GLB final.
"""
import bpy
import os
import sys
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(ROOT, "output", "mcp_bake")

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SLUG = argv[0] if argv else "used_box"

BAKE_W = 17408
BAKE_H = 1024

def log(m): print(f"[FINISH] {m}", flush=True)

obj = bpy.data.objects.get("Box")
assert obj is not None, "Box not found"
mat = obj.data.materials[0]
log(f"obj: {obj.name}  mat: {mat.name}  verts: {len(obj.data.vertices)}")

# Garante UV original ativa
for l in obj.data.uv_layers:
    if l.name == "UV_EC_original":
        l.active = True
        l.active_render = True
        break

nt = mat.node_tree
bake_node = nt.nodes.get("BAKE_TARGET")
if bake_node is None:
    bake_node = nt.nodes.new('ShaderNodeTexImage')
    bake_node.name = "BAKE_TARGET"
    bake_node.location = (-1000, -600)

# Garante color image carregada (do disco) — sem re-bakear
color_path = os.path.join(OUT_DIR, "ec_color_long.png")
if "ec_color_long" not in bpy.data.images:
    bpy.data.images.load(color_path, check_existing=True)
    bpy.data.images["ec_color_long.png" if "ec_color_long.png" in bpy.data.images else "ec_color_long"].name = "ec_color_long"
img_color = bpy.data.images.get("ec_color_long")
if img_color is None:
    # fallback nome com extensao
    for k, v in bpy.data.images.items():
        if "ec_color_long" in v.name:
            img_color = v; break
img_color.colorspace_settings.name = 'sRGB'
log(f"color image ready: {img_color.size[0]}x{img_color.size[1]}")

# Cycles
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
try: scene.cycles.device = 'GPU'
except: pass
scene.cycles.samples = 16
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
scene.render.bake.margin = 4

def make_img(name, colorspace):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, BAKE_W, BAKE_H, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img

def bake_to(image, btype, label, **extras):
    for n in nt.nodes: n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node
    bake_node.image = image
    for o in bpy.data.objects: o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    log(f"baking {label} ({btype})  {BAKE_W}x{BAKE_H}  samples=16")
    bpy.ops.object.bake(type=btype, use_clear=True, margin=4, **extras)
    p = os.path.join(OUT_DIR, f"ec_{label}_long.png")
    image.filepath_raw = p
    image.file_format = 'PNG'
    image.save()
    log(f"  saved {p}  size MB={os.path.getsize(p)/(1024*1024):.1f}")
    return image

img_normal = make_img("ec_normal_long", 'Non-Color')
bake_to(img_normal, 'NORMAL', 'normal', normal_space='TANGENT')

img_rough = make_img("ec_roughness_long", 'Non-Color')
bake_to(img_rough, 'ROUGHNESS', 'roughness')

# ============================================================
# Swap material por Principled BSDF baked
# ============================================================
log("Build Principled baked material")
baked = bpy.data.materials.new(f"EC_Baked_{SLUG}")
baked.use_nodes = True
bnt = baked.node_tree
for n in list(bnt.nodes): bnt.nodes.remove(n)
out = bnt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
bsdf = bnt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (100, 0)
bnt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

tc = bnt.nodes.new('ShaderNodeTexImage'); tc.image = img_color; tc.location = (-500, 250)
bnt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])

tr = bnt.nodes.new('ShaderNodeTexImage'); tr.image = img_rough; tr.location = (-500, -50)
bnt.links.new(tr.outputs['Color'], bsdf.inputs['Roughness'])

tn = bnt.nodes.new('ShaderNodeTexImage'); tn.image = img_normal; tn.location = (-500, -350)
nm = bnt.nodes.new('ShaderNodeNormalMap'); nm.location = (-150, -350)
bnt.links.new(tn.outputs['Color'], nm.inputs['Color'])
bnt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])

obj.data.materials.clear()
obj.data.materials.append(baked)
obj.data.uv_layers["UV_EC_original"].active = True
obj.data.uv_layers["UV_EC_original"].active_render = True

# ============================================================
# Export GLB com texturas embedded
# ============================================================
glb_path = os.path.join(OUT_DIR, f"cardboard_{SLUG}.glb")
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
log(f"Export GLB -> {glb_path}")
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True,
    export_image_format='AUTO',
)
size_mb = os.path.getsize(glb_path) / (1024*1024)
log(f"GLB done  size MB={size_mb:.2f}")

# Eevee 512 render single frame pra preview
log("Eevee preview render")
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(OUT_DIR, f"preview_{SLUG}.png")

cam_data = bpy.data.cameras.new("PreviewCam")
cam = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (2.6, -2.6, 1.9)
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
scene.camera = cam

if not any(o.type == 'LIGHT' for o in bpy.data.objects):
    sun_data = bpy.data.lights.new("Sun", 'SUN')
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (3, -2, 5)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

world = scene.world
if world is None:
    world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0)
    bg.inputs[1].default_value = 1.0

bpy.ops.render.render(write_still=True)
log(f"preview -> {scene.render.filepath}")
log("=== ALL DONE ===")
print("[FINISH] === SUCCESS ===", flush=True)
