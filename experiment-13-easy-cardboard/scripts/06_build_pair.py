"""
Gera 2 GLBs do mesmo modelo, um sem efeito e outro com Easy Cardboard 3.0 wear=0.9.

Pipeline:
- antes: Plane 9v + Simple Box Creator + Smooth by Angle -> apply -> GLB sem cardboard
- depois: Plane 9v + Simple Box Creator + Easy Cardboard 3.0 (wear=0.9) + Smooth by Angle
          -> apply -> bake 4K (color/normal/roughness) -> swap material -> GLB

Args (apos --): WEAR_VALUE OUTPUT_DIR_NAME BAKE_RES
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WEAR = float(argv[0]) if argv else 0.9
SUBDIR = argv[1] if len(argv) > 1 else 'pair'
BAKE_RES = int(argv[2]) if len(argv) > 2 else 4096

OUTPUT_DIR = os.path.join(ROOT, "output", SUBDIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MAT_NAME = "Easy Cardboard 3"

def log(m): print(f"[PAIR] {m}", flush=True)

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for blk in list(bpy.data.meshes):
        bpy.data.meshes.remove(blk)
    for blk in list(bpy.data.materials):
        bpy.data.materials.remove(blk)

def set_input(mod, name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and item.name.strip() == name.strip():
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"   FAIL {name}={value}: {e}"); return False
    return False

def append_assets():
    log(f"Appending from {ASSET_BLEND}")
    with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
        data_to.node_groups = [n for n in [NG_BOX, NG_CARDBOARD, NG_SMOOTH] if n in data_from.node_groups]
        if MAT_NAME in data_from.materials:
            data_to.materials = [MAT_NAME]
    return (
        bpy.data.node_groups[NG_BOX],
        bpy.data.node_groups[NG_CARDBOARD],
        bpy.data.node_groups[NG_SMOOTH],
        bpy.data.materials.get(MAT_NAME),
    )

def build_plane(name):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
    bm.to_mesh(mesh); bm.free()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def configure_box(mod):
    set_input(mod, 'Width', 1.0)
    set_input(mod, 'Length', 1.0)
    set_input(mod, 'Height', 1.0)
    set_input(mod, 'Gaps (Length)', 0.07)
    set_input(mod, 'Gap (Width)', 0.07)
    set_input(mod, 'Flap Length', 0.11)
    set_input(mod, 'Simple Sub-D Level', 3)
    set_input(mod, 'CC Sub-D Level', 0)
    set_input(mod, 'Edge Crease', 0.802)
    set_input(mod, 'Delete Bounds', False)

def configure_cardboard(mod, wear):
    set_input(mod, 'Thickness', 0.01)
    set_input(mod, 'Global Scale', 1.0)
    set_input(mod, 'Wear ⏰', wear)
    set_input(mod, 'Seed \U0001F3B2', 0)
    set_input(mod, 'Split Angle', 0.5236)
    set_input(mod, 'Strength', 0.2)
    set_input(mod, 'Separation', 1.0)
    set_input(mod, 'Separation Noise Scale', 0.0)
    set_input(mod, 'Z Position', 1.0)
    set_input(mod, ' Fibers Density', 2.0)
    set_input(mod, 'Fibers Size', 0.02)
    set_input(mod, 'Roughness ', 1.0)
    set_input(mod, 'Metallic', 0.0)
    set_input(mod, 'Clearcoat', 0.0)
    set_input(mod, 'Displacement Strength', 0.161)
    set_input(mod, 'Normal Strength', 1.0)
    set_input(mod, 'Print Roughness', 0.5)
    set_input(mod, 'Direction Mask Threshold', 2.0)
    set_input(mod, 'Invert', False)
    set_input(mod, 'UV Name', 'UVMap')

def export_glb(obj, glb_path):
    for o in bpy.data.objects: o.select_set(False)
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

# ---- BEFORE: only Simple Box Creator + plain material ----
log("=== STAGE 1: BEFORE (just Simple Box Creator, plain material) ===")
clean_scene()
ng_box, ng_cb, ng_smooth, mat_cardboard = append_assets()

obj_before = build_plane("Before")

# plain kraft-like material so the geometry is visible
mat_plain = bpy.data.materials.new("KraftPlain")
mat_plain.use_nodes = True
ntp = mat_plain.node_tree
for n in list(ntp.nodes): ntp.nodes.remove(n)
out = ntp.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
bsdf = ntp.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (100, 0)
bsdf.inputs['Base Color'].default_value = (0.62, 0.45, 0.30, 1.0)
bsdf.inputs['Roughness'].default_value = 0.85
ntp.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
obj_before.data.materials.clear()
obj_before.data.materials.append(mat_plain)

m_box_b = obj_before.modifiers.new(name="Simple Box Creator", type='NODES')
m_box_b.node_group = ng_box
configure_box(m_box_b)

m_smooth_b = obj_before.modifiers.new(name="Smooth by Angle", type='NODES')
m_smooth_b.node_group = ng_smooth
set_input(m_smooth_b, 'Angle', 0.5236)
set_input(m_smooth_b, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
bpy.ops.object.modifier_apply(modifier="Simple Box Creator")
bpy.ops.object.modifier_apply(modifier="Smooth by Angle")
log(f"   before: {len(obj_before.data.vertices)} verts, {len(obj_before.data.polygons)} faces")

glb_before = os.path.join(OUTPUT_DIR, "before.glb")
export_glb(obj_before, glb_before)
log(f"   exported -> {glb_before}")

# ---- AFTER: Simple Box Creator + Easy Cardboard 3.0 + Smooth by Angle, bake + GLB ----
log(f"=== STAGE 2: AFTER (wear={WEAR}, bake {BAKE_RES}^2) ===")
clean_scene()
ng_box, ng_cb, ng_smooth, mat_cardboard = append_assets()

obj_after = build_plane("After")
obj_after.data.materials.clear()
obj_after.data.materials.append(mat_cardboard)

m_box_a = obj_after.modifiers.new(name="Simple Box Creator", type='NODES')
m_box_a.node_group = ng_box
configure_box(m_box_a)

m_cb_a = obj_after.modifiers.new(name="GeometryNodes", type='NODES')
m_cb_a.node_group = ng_cb
configure_cardboard(m_cb_a, WEAR)

m_smooth_a = obj_after.modifiers.new(name="Smooth by Angle", type='NODES')
m_smooth_a.node_group = ng_smooth
set_input(m_smooth_a, 'Angle', 0.5236)
set_input(m_smooth_a, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
log("   applying Simple Box Creator")
bpy.ops.object.modifier_apply(modifier="Simple Box Creator")
log(f"   post-box: {len(obj_after.data.vertices)} verts, UV layers: {[l.name for l in obj_after.data.uv_layers]}, mats: {[m.name if m else None for m in obj_after.data.materials]}")

# Simple Box Creator strips material slots and UV layer — re-do both
obj_after.data.materials.clear()
obj_after.data.materials.append(mat_cardboard)

# UV unwrap the box-creator output
bpy.context.view_layer.objects.active = obj_after
for o in bpy.data.objects: o.select_set(False)
obj_after.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.005)
bpy.ops.object.mode_set(mode='OBJECT')
# ensure UV layer is named UVMap and active
if obj_after.data.uv_layers:
    uvl = obj_after.data.uv_layers[0]
    uvl.name = 'UVMap'
    uvl.active = True
    uvl.active_render = True
log(f"   after re-uv: UV layers: {[l.name for l in obj_after.data.uv_layers]}, mats: {[m.name for m in obj_after.data.materials]}")

log("   applying Easy Cardboard 3.0")
bpy.ops.object.modifier_apply(modifier="GeometryNodes")
log(f"   post-cb: UV layers: {[l.name for l in obj_after.data.uv_layers]}, mats: {[m.name if m else None for m in obj_after.data.materials]}")

# Cardboard may also strip — re-attach
if not obj_after.data.materials or obj_after.data.materials[0] is None:
    obj_after.data.materials.clear()
    obj_after.data.materials.append(mat_cardboard)
# ensure UV still active
if obj_after.data.uv_layers:
    obj_after.data.uv_layers[0].active = True
    obj_after.data.uv_layers[0].active_render = True

log("   applying Smooth by Angle")
bpy.ops.object.modifier_apply(modifier="Smooth by Angle")
if not obj_after.data.materials or obj_after.data.materials[0] is None:
    obj_after.data.materials.clear()
    obj_after.data.materials.append(mat_cardboard)
if obj_after.data.uv_layers:
    obj_after.data.uv_layers[0].active = True
    obj_after.data.uv_layers[0].active_render = True
log(f"   after-apply: {len(obj_after.data.vertices)} verts, {len(obj_after.data.polygons)} faces")
log(f"   UV layers (final): {[l.name for l in obj_after.data.uv_layers]}, active={obj_after.data.uv_layers.active.name if obj_after.data.uv_layers else None}")
log(f"   materials (final): {[m.name if m else None for m in obj_after.data.materials]}")

# UV stats — confirm UVs are non-trivial
if obj_after.data.uv_layers:
    uvl = obj_after.data.uv_layers.active
    us = [d.uv[0] for d in uvl.data]
    vs = [d.uv[1] for d in uvl.data]
    if us:
        log(f"   UV range: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}] ({len(us)} loops)")

# Also: re-unwrap on the FINAL geometry (post-cardboard) so UVs cover the full mesh
log("   final smart_project to ensure UVs on the baked geometry")
bpy.context.view_layer.objects.active = obj_after
for o in bpy.data.objects: o.select_set(False)
obj_after.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.005)
bpy.ops.object.mode_set(mode='OBJECT')
if obj_after.data.uv_layers:
    obj_after.data.uv_layers.active.name = 'UVMap'
    obj_after.data.uv_layers.active.active_render = True
    uvl = obj_after.data.uv_layers.active
    us = [d.uv[0] for d in uvl.data]
    vs = [d.uv[1] for d in uvl.data]
    log(f"   final UV range: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}]")

# bake setup
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64
bake_cfg = scene.render.bake
bake_cfg.use_pass_direct = False
bake_cfg.use_pass_indirect = False
bake_cfg.use_pass_color = True
bake_cfg.margin = 16

def make_img(name, colorspace='sRGB'):
    img = bpy.data.images.new(name, BAKE_RES, BAKE_RES, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img

img_color = make_img("after_color", 'sRGB')
img_normal = make_img("after_normal", 'Non-Color')
img_rough = make_img("after_roughness", 'Non-Color')

# IMPORTANT: this runs AFTER all modifier applies & material re-attachments.
# We inject the bake target node now so it survives into the bake.
mat = obj_after.data.materials[0]
log(f"   bake target material: '{mat.name}', has_nodes={mat.use_nodes}")
mat.use_nodes = True
nt = mat.node_tree
# remove any previous BAKE_TARGET (if reusing across stages)
for n in list(nt.nodes):
    if n.name == "BAKE_TARGET":
        nt.nodes.remove(n)
bake_node = nt.nodes.new('ShaderNodeTexImage')
bake_node.name = "BAKE_TARGET"
bake_node.location = (-600, -400)
log(f"   injected BAKE_TARGET into node tree (nodes={len(nt.nodes)})")

def bake_to(image, bake_type, label):
    log(f"   baking {label} ({bake_type}) @ {BAKE_RES}^2")
    bake_node.image = image
    for n in nt.nodes: n.select = False
    bake_node.select = True
    nt.nodes.active = bake_node
    extras = {}
    if bake_type == 'NORMAL':
        extras['normal_space'] = 'TANGENT'
    bpy.ops.object.bake(type=bake_type, use_clear=True, margin=16, **extras)
    p = os.path.join(OUTPUT_DIR, f"after_{label}.png")
    image.filepath_raw = p
    image.file_format = 'PNG'
    image.save()
    log(f"      saved -> {p}")

for o in bpy.data.objects: o.select_set(False)
obj_after.select_set(True)
bpy.context.view_layer.objects.active = obj_after

bake_to(img_color, 'DIFFUSE', 'color')
bake_to(img_normal, 'NORMAL', 'normal')
bake_to(img_rough, 'ROUGHNESS', 'roughness')

# simple PBR for export
log("   building baked PBR for export")
baked = bpy.data.materials.new("AfterBaked")
baked.use_nodes = True
bnt = baked.node_tree
for n in list(bnt.nodes): bnt.nodes.remove(n)
out = bnt.nodes.new('ShaderNodeOutputMaterial'); out.location=(400,0)
bsdf = bnt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(100,0)
bnt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
tc = bnt.nodes.new('ShaderNodeTexImage'); tc.image=img_color; tc.location=(-400,200)
bnt.links.new(tc.outputs['Color'], bsdf.inputs['Base Color'])
tr = bnt.nodes.new('ShaderNodeTexImage'); tr.image=img_rough; tr.image.colorspace_settings.name='Non-Color'; tr.location=(-400,-50)
bnt.links.new(tr.outputs['Color'], bsdf.inputs['Roughness'])
tn = bnt.nodes.new('ShaderNodeTexImage'); tn.image=img_normal; tn.image.colorspace_settings.name='Non-Color'; tn.location=(-400,-300)
nm = bnt.nodes.new('ShaderNodeNormalMap'); nm.location=(-100,-300)
bnt.links.new(tn.outputs['Color'], nm.inputs['Color'])
bnt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
obj_after.data.materials.clear()
obj_after.data.materials.append(baked)

glb_after = os.path.join(OUTPUT_DIR, "after.glb")
export_glb(obj_after, glb_after)
log(f"   exported -> {glb_after}")

log("=== DONE ===")
print("[PAIR] === SUCCESS ===", flush=True)
