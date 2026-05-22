"""
Pipeline v2: replica EXATAMENTE a setup do exemplo do asset.
- Plane 9 verts
- Modifier 1: Simple Box Creator (gera caixa procedural com flaps/tabs/gaps)
- Modifier 2: Easy Cardboard 3.0 (com defaults do exemplo do asset)
- Modifier 3: Smooth by Angle
Renderiza Cycles direto (sem bake) pra preview rapido.

Args via env:
  WEAR_VALUE  — float 0..1 (default 0.174)
  OUTPUT_NAME — png basename (default preview_v2)
  RENDER_ONLY — '1' renderiza so o preview Cycles; '0' bakeia + exporta GLB
"""
import bpy
import bmesh
import os
import sys
import math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# args after `--`: WEAR_VALUE OUTPUT_NAME RENDER_ONLY BAKE_RES
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WEAR_VALUE = float(argv[0]) if len(argv) > 0 else 0.174
OUTPUT_NAME = argv[1] if len(argv) > 1 else 'preview_v2'
RENDER_ONLY = (argv[2] if len(argv) > 2 else '1') == '1'
BAKE_RES = int(argv[3]) if len(argv) > 3 else 2048

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MATERIAL_NAME = "Easy Cardboard 3"

def log(msg):
    print(f"[CB2] {msg}", flush=True)

# ---- 1. clean scene ----
log("Cleaning scene")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.meshes):
    bpy.data.meshes.remove(block)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)
for block in list(bpy.data.lights):
    bpy.data.lights.remove(block)

# ---- 2. append node groups + material ----
log(f"Appending node groups + material from {ASSET_BLEND}")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    needed_groups = [NG_BOX, NG_CARDBOARD, NG_SMOOTH]
    data_to.node_groups = [n for n in needed_groups if n in data_from.node_groups]
    if MATERIAL_NAME in data_from.materials:
        data_to.materials = [MATERIAL_NAME]

ng_box = bpy.data.node_groups.get(NG_BOX)
ng_cardboard = bpy.data.node_groups.get(NG_CARDBOARD)
ng_smooth = bpy.data.node_groups.get(NG_SMOOTH)
mat_cardboard = bpy.data.materials.get(MATERIAL_NAME)
log(f"  ng_box={ng_box}, ng_cardboard={ng_cardboard}, ng_smooth={ng_smooth}, material={mat_cardboard}")

# ---- 3. create plane 9 verts (subdivided 2x2) — mesmo input do exemplo ----
log("Creating 2x2 subdivided plane (9 verts) — same as asset example")
mesh = bpy.data.meshes.new("Box")
obj = bpy.data.objects.new("Box", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
# UV unwrap — grid already has clean UVs from create_grid? Not always. Force.
bm.to_mesh(mesh)
bm.free()

# clean UV unwrap on the flat plane
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- 4. assign material ----
obj.data.materials.clear()
obj.data.materials.append(mat_cardboard)

# ---- 5. add modifiers in same order as the asset example ----

def set_input(mod, name, value):
    ng = mod.node_group
    name_clean = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name.strip() == name_clean:
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"   FAIL set '{name}'={value}: {e}")
                return False
    log(f"   socket '{name}' not found")
    return False

# Modifier 1: Simple Box Creator (defaults do exemplo do asset)
log("Mod 1: Simple Box Creator")
m1 = obj.modifiers.new(name="Simple Box Creator", type='NODES')
m1.node_group = ng_box
set_input(m1, 'Width', 1.0)
set_input(m1, 'Length', 1.0)
set_input(m1, 'Height', 1.0)
set_input(m1, 'Gaps (Length)', 0.07)
set_input(m1, 'Gap (Width)', 0.07)
set_input(m1, 'Flap Length', 0.11)
set_input(m1, 'Simple Sub-D Level', 3)
set_input(m1, 'CC Sub-D Level', 0)
set_input(m1, 'Edge Crease', 0.802)
set_input(m1, 'Delete Bounds', False)

# Modifier 2: Easy Cardboard 3.0 (defaults do exemplo do asset; WEAR_VALUE customizavel)
log(f"Mod 2: Easy Cardboard 3.0 (wear={WEAR_VALUE})")
m2 = obj.modifiers.new(name="GeometryNodes", type='NODES')
m2.node_group = ng_cardboard
set_input(m2, 'Thickness', 0.01)          # 10mm — asset default
set_input(m2, 'Global Scale', 1.0)
set_input(m2, 'Wear ⏰', WEAR_VALUE)
set_input(m2, 'Seed \U0001F3B2', 0)
set_input(m2, 'Split Angle', 0.5236)      # 30 graus
set_input(m2, 'Strength', 0.2)
set_input(m2, 'Separation', 1.0)
set_input(m2, 'Separation Noise Scale', 0.0)
set_input(m2, 'Z Position', 1.0)
set_input(m2, ' Fibers Density', 2.0)
set_input(m2, 'Fibers Size', 0.02)
set_input(m2, 'Roughness ', 1.0)
set_input(m2, 'Metallic', 0.0)
set_input(m2, 'Clearcoat', 0.0)
set_input(m2, 'Displacement Strength', 0.161)
set_input(m2, 'Normal Strength', 1.0)
set_input(m2, 'Print Roughness', 0.5)
set_input(m2, 'Direction Mask Threshold', 2.0)
set_input(m2, 'Invert', False)
set_input(m2, 'UV Name', 'UVMap')
# UV Scale stays at default (0,0) just like the asset example

# Modifier 3: Smooth by Angle
log("Mod 3: Smooth by Angle")
m3 = obj.modifiers.new(name="Smooth by Angle", type='NODES')
m3.node_group = ng_smooth
set_input(m3, 'Angle', 0.5236)
set_input(m3, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
log(f"Modifiers: {[m.name for m in obj.modifiers]}")

# ---- 6. scene setup: camera + light ----
log("Setting up camera + light")
# camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (1.6, -2.2, 1.4)
# point at box center
direction = Vector((0, 0, 0.4)) - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
bpy.context.scene.camera = cam_obj

# sun
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun_data.angle = 0.05
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.location = (3, -3, 5)
sun_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))

# world background dark
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("W")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0)
    bg.inputs[1].default_value = 0.6

# render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64
scene.render.resolution_x = 1024
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'

if RENDER_ONLY:
    out_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.png")
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'PNG'
    log(f"Rendering -> {out_path}")
    bpy.ops.render.render(write_still=True)
    log(f"DONE rendered: {out_path}")
    print(f"[CB2] === RENDER SUCCESS: {out_path} ===", flush=True)
else:
    # ---- BAKE + GLB EXPORT path ----
    # Apply modifier chain
    log("Applying modifier chain (box -> cardboard -> smooth)")
    bpy.context.view_layer.objects.active = obj
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    for mname in ["Simple Box Creator", "GeometryNodes", "Smooth by Angle"]:
        try:
            bpy.ops.object.modifier_apply(modifier=mname)
            log(f"  applied: {mname}")
        except Exception as e:
            log(f"  FAIL apply {mname}: {e}")

    log(f"  vertices after apply: {len(obj.data.vertices)}, faces: {len(obj.data.polygons)}")
    log(f"  UV layers: {[l.name for l in obj.data.uv_layers]}")

    # bake setup
    scene.cycles.samples = 32
    bake_cfg = scene.render.bake
    bake_cfg.use_pass_direct = False
    bake_cfg.use_pass_indirect = False
    bake_cfg.use_pass_color = True
    bake_cfg.margin = 8

    def make_img(name, colorspace='sRGB'):
        img = bpy.data.images.new(name, BAKE_RES, BAKE_RES, alpha=False, float_buffer=False)
        img.colorspace_settings.name = colorspace
        return img

    img_color = make_img("bake_color", 'sRGB')
    img_normal = make_img("bake_normal", 'Non-Color')
    img_rough = make_img("bake_roughness", 'Non-Color')

    mat = obj.data.materials[0]
    mat.use_nodes = True
    nt = mat.node_tree
    bake_node = nt.nodes.new('ShaderNodeTexImage')
    bake_node.name = "BAKE_TARGET"
    bake_node.location = (-600, -400)

    def bake_to(image, bake_type, label):
        log(f"  baking {label} -> {image.name} ({bake_type})")
        bake_node.image = image
        for n in nt.nodes:
            n.select = False
        bake_node.select = True
        nt.nodes.active = bake_node
        extras = {}
        if bake_type == 'NORMAL':
            extras['normal_space'] = 'TANGENT'
        bpy.ops.object.bake(type=bake_type, use_clear=True, margin=8, **extras)
        out_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}_{label}.png")
        image.filepath_raw = out_path
        image.file_format = 'PNG'
        image.save()
        log(f"    saved -> {out_path}")

    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bake_to(img_color, 'DIFFUSE', 'color')
    bake_to(img_normal, 'NORMAL', 'normal')
    bake_to(img_rough, 'ROUGHNESS', 'roughness')

    # simple PBR for export
    log("Building simple PBR for export")
    baked_mat = bpy.data.materials.new(f"{OUTPUT_NAME}_baked")
    baked_mat.use_nodes = True
    bnt = baked_mat.node_tree
    for n in list(bnt.nodes):
        bnt.nodes.remove(n)
    out = bnt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
    bsdf = bnt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (100, 0)
    bnt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    tc = bnt.nodes.new('ShaderNodeTexImage'); tc.image = img_color; tc.location = (-400, 200)
    bnt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
    tr = bnt.nodes.new('ShaderNodeTexImage'); tr.image = img_rough
    tr.image.colorspace_settings.name = 'Non-Color'; tr.location = (-400, -50)
    bnt.links.new(tr.outputs['Color'], bsdf.inputs['Roughness'])
    tn = bnt.nodes.new('ShaderNodeTexImage'); tn.image = img_normal
    tn.image.colorspace_settings.name = 'Non-Color'; tn.location = (-400, -300)
    nm = bnt.nodes.new('ShaderNodeNormalMap'); nm.location = (-100, -300)
    bnt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    bnt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])

    obj.data.materials.clear()
    obj.data.materials.append(baked_mat)

    glb_path = os.path.join(OUTPUT_DIR, f"{OUTPUT_NAME}.glb")
    log(f"Exporting GLB -> {glb_path}")
    for o in bpy.data.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_image_format='AUTO',
    )
    log(f"DONE: {glb_path}")
    print(f"[CB2] === BAKE+GLB SUCCESS: {glb_path} ===", flush=True)
