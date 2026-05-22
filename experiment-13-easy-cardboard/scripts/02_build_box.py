"""
Pipeline: blank Blender -> append Easy Cardboard node group + material ->
create box mesh with UVs -> apply Geometry Nodes modifier -> bake PBR maps ->
swap to baked material -> export GLB.

Output files end up in ../output/.
"""
import bpy
import bmesh
import os
import sys
from mathutils import Vector

# ---- paths ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BAKE_RES = 2048
NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"  # 📦 Easy Cardboard 3.0
MATERIAL_NAME = "Easy Cardboard 3"

def log(msg):
    print(f"[CARDBOARD] {msg}", flush=True)

# ---- 1. clean scene ----
log("Cleaning default scene")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in list(bpy.data.meshes):
    bpy.data.meshes.remove(block)
for block in list(bpy.data.materials):
    bpy.data.materials.remove(block)

# ---- 2. append node group + material from asset blend ----
log(f"Appending '{NODE_GROUP_NAME}' from {ASSET_BLEND}")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    if NODE_GROUP_NAME in data_from.node_groups:
        data_to.node_groups = [NODE_GROUP_NAME]
    else:
        log(f"AVAILABLE node groups in source:")
        for n in data_from.node_groups:
            log(f"   {repr(n)}")
        raise RuntimeError(f"Node group '{NODE_GROUP_NAME}' not found")
    if MATERIAL_NAME in data_from.materials:
        data_to.materials = [MATERIAL_NAME]
    else:
        log(f"AVAILABLE materials in source: {list(data_from.materials)}")
        raise RuntimeError(f"Material '{MATERIAL_NAME}' not found")

cardboard_ng = bpy.data.node_groups.get(NODE_GROUP_NAME)
cardboard_mat = bpy.data.materials.get(MATERIAL_NAME)
log(f"  Got node group: {cardboard_ng}")
log(f"  Got material:   {cardboard_mat}")

# ---- 3. create box mesh ----
log("Creating box mesh (30x20x15 cm)")
# units are meters in Blender; use centimeter-scale values
W, D, H = 0.30, 0.20, 0.15

mesh = bpy.data.meshes.new("CardboardBox")
obj = bpy.data.objects.new("CardboardBox", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
# subdivide each face so smart-solidify has more verts to work with for fibers/displacement
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
# scale the unit cube to box dimensions
for v in bm.verts:
    v.co.x *= W
    v.co.y *= D
    v.co.z *= H
# move so bottom sits on z=0
for v in bm.verts:
    v.co.z += H / 2

bm.to_mesh(mesh)
bm.free()

# ---- 4. UV unwrap (smart project) ----
log("UV unwrapping (smart project)")
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# ---- 5. apply material (Easy Cardboard 3) ----
log("Assigning Easy Cardboard 3 material")
obj.data.materials.clear()
obj.data.materials.append(cardboard_mat)

# ---- 6. add Geometry Nodes modifier with Easy Cardboard 3.0 node group ----
log("Adding GeometryNodes modifier")
mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
mod.node_group = cardboard_ng

# Tweak a few inputs to push the corrugation/wear look. Use the socket
# identifiers from the interface (Blender 4.x uses Input_N internally, but
# we can address by index via mod[item.identifier]).
def set_input(mod, socket_name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name.strip() == socket_name.strip():
            try:
                mod[item.identifier] = value
                log(f"  set '{socket_name}' = {value}")
                return True
            except Exception as e:
                log(f"  FAILED set '{socket_name}' = {value}: {e}")
                return False
    log(f"  socket '{socket_name}' not found")
    return False

# Conservative settings: cardboard look but keep the box shape recognizable.
# Easy Cardboard 3.x "Wear" + "Displacement Strength" deform geometry aggressively;
# we want the corrugation TEXTURE visible but the BOX form intact.
set_input(mod, 'Thickness', 0.003)        # 3mm wall
set_input(mod, 'Global Scale', 0.5)       # smaller corrugation cells
set_input(mod, 'Wear ⏰', 0.05)            # near-new box
set_input(mod, 'Seed \U0001F3B2', 7)
set_input(mod, 'Strength', 0.3)           # subtle displacement on faces
set_input(mod, 'Roughness ', 0.75)
set_input(mod, 'Metallic', 0.0)
set_input(mod, 'Normal Strength', 0.8)
set_input(mod, 'Displacement Strength', 0.15)  # geometry barely deformed
set_input(mod, ' Fibers Density', 1.0)
set_input(mod, 'Fibers Size', 0.4)

# force depsgraph eval
bpy.context.view_layer.update()
log(f"Modifier set up. Object now has {len(obj.modifiers)} modifier(s).")

# ---- 7. apply modifier (freeze geometry) ----
log("Applying GeometryNodes modifier to freeze geometry")
bpy.context.view_layer.objects.active = obj
try:
    bpy.ops.object.modifier_apply(modifier="EasyCardboard")
    log(f"  Applied. Vertices: {len(obj.data.vertices)}, Faces: {len(obj.data.polygons)}")
except Exception as e:
    log(f"  Failed to apply modifier: {e}")
    raise

# After apply, the geometry has UVs (the modifier preserves/creates them).
# Verify UV map exists.
if obj.data.uv_layers:
    log(f"  UV layers after apply: {[l.name for l in obj.data.uv_layers]}")
else:
    log("  WARNING: no UV layer after apply, baking will fail")

# ---- 8. set up bake images & bake basecolor, normal, roughness ----
log("Configuring bake")
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'GPU' if bpy.context.preferences.addons.get('cycles') else 'CPU'
bpy.context.scene.cycles.samples = 32
# bake settings live on scene.render.bake in Blender 4.x/5.x
bake_cfg = bpy.context.scene.render.bake
bake_cfg.use_pass_direct = False
bake_cfg.use_pass_indirect = False
bake_cfg.use_pass_color = True
bake_cfg.margin = 8

# create three target images
def make_bake_image(name, colorspace='sRGB'):
    img = bpy.data.images.new(name, BAKE_RES, BAKE_RES, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img

img_color = make_bake_image("bake_color", colorspace='sRGB')
img_normal = make_bake_image("bake_normal", colorspace='Non-Color')
img_rough = make_bake_image("bake_roughness", colorspace='Non-Color')

# Need a bake target image node in the material. Inject one and select it before each bake.
mat = obj.data.materials[0]
mat.use_nodes = True
nt = mat.node_tree

# add a single TEX_IMAGE node we'll reuse, selecting & assigning the right image per bake
bake_node = nt.nodes.new('ShaderNodeTexImage')
bake_node.name = "BAKE_TARGET"
bake_node.location = (-600, -400)

def bake_to(image, bake_type, label):
    log(f"  Baking {label} -> {image.name} ({bake_type})")
    bake_node.image = image
    for n in nt.nodes:
        n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node
    extras = {}
    if bake_type == 'NORMAL':
        extras['normal_space'] = 'TANGENT'
    try:
        bpy.ops.object.bake(type=bake_type, use_clear=True, margin=8, **extras)
    except Exception as e:
        log(f"    bake FAILED: {e}")
        raise
    out_path = os.path.join(OUTPUT_DIR, f"{label}.png")
    image.filepath_raw = out_path
    image.file_format = 'PNG'
    image.save()
    log(f"    saved -> {out_path}")

# select & make active
for o in bpy.data.objects:
    o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bake_to(img_color, 'DIFFUSE', 'cardboard_color')
bake_to(img_normal, 'NORMAL', 'cardboard_normal')
bake_to(img_rough, 'ROUGHNESS', 'cardboard_roughness')

# ---- 9. swap material for a simple PBR using the baked maps ----
log("Building simple baked PBR material for export")
baked_mat = bpy.data.materials.new("CardboardBaked")
baked_mat.use_nodes = True
bnt = baked_mat.node_tree
for n in list(bnt.nodes):
    bnt.nodes.remove(n)

out = bnt.nodes.new('ShaderNodeOutputMaterial')
out.location = (400, 0)
bsdf = bnt.nodes.new('ShaderNodeBsdfPrincipled')
bsdf.location = (100, 0)
bnt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

tex_color = bnt.nodes.new('ShaderNodeTexImage')
tex_color.image = img_color
tex_color.location = (-400, 200)
bnt.links.new(tex_color.outputs['Color'], bsdf.inputs['Base Color'])

tex_rough = bnt.nodes.new('ShaderNodeTexImage')
tex_rough.image = img_rough
tex_rough.image.colorspace_settings.name = 'Non-Color'
tex_rough.location = (-400, -50)
bnt.links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])

tex_norm = bnt.nodes.new('ShaderNodeTexImage')
tex_norm.image = img_normal
tex_norm.image.colorspace_settings.name = 'Non-Color'
tex_norm.location = (-400, -300)
normal_map = bnt.nodes.new('ShaderNodeNormalMap')
normal_map.location = (-100, -300)
bnt.links.new(tex_norm.outputs['Color'], normal_map.inputs['Color'])
bnt.links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])

obj.data.materials.clear()
obj.data.materials.append(baked_mat)

# ---- 10. export GLB ----
glb_path = os.path.join(OUTPUT_DIR, "cardboard_box.glb")
log(f"Exporting GLB -> {glb_path}")
for o in bpy.data.objects:
    o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=True,
    export_apply=True,        # apply remaining modifiers (none, but safe)
    export_yup=True,
    export_image_format='AUTO',
)

# also save the working blend for inspection
work_blend = os.path.join(OUTPUT_DIR, "cardboard_box.blend")
bpy.ops.wm.save_as_mainfile(filepath=work_blend)
log(f"Saved working blend -> {work_blend}")

log("DONE.")
print("[CARDBOARD] === SUCCESS ===", flush=True)
