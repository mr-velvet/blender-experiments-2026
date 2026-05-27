"""
Pair pipeline — versao segura baseada no 02_build_box.py que ja provou bake funcionando.

ANTES: cubo bmesh com UV smart_project + Simple Box Creator (procedural) + apply -> GLB direto
  (geometria pura, mostra o "esqueleto" da caixa)

DEPOIS: cubo bmesh com UV smart_project + GeometryNodes (Easy Cardboard 3.0 wear=0.9) + apply
  -> bake (Cycles 4K) -> swap material -> GLB

Diferenca chave do 06: NAO uso Simple Box Creator no "depois" porque ele recria a malha e remove UV/material.
Uso o mesmo padrao do v1 — cubo manual com UV pre-feita, so o Easy Cardboard como modifier.
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
WEAR = float(argv[0]) if argv else 0.9
SUBDIR = argv[1] if len(argv) > 1 else 'pair_safe'
BAKE_RES = int(argv[2]) if len(argv) > 2 else 4096

OUTPUT_DIR = os.path.join(ROOT, "output", SUBDIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MAT_NAME = "Easy Cardboard 3"

def log(m): print(f"[PAIR2] {m}", flush=True)

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

# ---- 1. Clean & append ----
log("Cleaning + appending")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for blk in list(bpy.data.meshes): bpy.data.meshes.remove(blk)
for blk in list(bpy.data.materials): bpy.data.materials.remove(blk)
for blk in list(bpy.data.lights): bpy.data.lights.remove(blk)

with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = [n for n in [NG_BOX, NG_CARDBOARD, NG_SMOOTH] if n in data_from.node_groups]
    data_to.materials = [MAT_NAME]

ng_box = bpy.data.node_groups[NG_BOX]
ng_cb = bpy.data.node_groups[NG_CARDBOARD]
ng_smooth = bpy.data.node_groups[NG_SMOOTH]
mat_cardboard = bpy.data.materials[MAT_NAME]

# ---- 2. Build BEFORE: plane 9v + Simple Box Creator -> apply -> GLB ----
log("=== BEFORE: Simple Box Creator -> apply -> GLB (plain kraft material) ===")
mesh_b = bpy.data.meshes.new("BoxBefore")
obj_b = bpy.data.objects.new("BoxBefore", mesh_b)
bpy.context.collection.objects.link(obj_b)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
bm.to_mesh(mesh_b); bm.free()

# plain kraft material
mat_plain = bpy.data.materials.new("KraftPlain")
mat_plain.use_nodes = True
ntp = mat_plain.node_tree
for n in list(ntp.nodes): ntp.nodes.remove(n)
out_p = ntp.nodes.new('ShaderNodeOutputMaterial'); out_p.location=(400,0)
bsdf_p = ntp.nodes.new('ShaderNodeBsdfPrincipled'); bsdf_p.location=(100,0)
bsdf_p.inputs['Base Color'].default_value = (0.62, 0.45, 0.30, 1.0)
bsdf_p.inputs['Roughness'].default_value = 0.85
ntp.links.new(bsdf_p.outputs['BSDF'], out_p.inputs['Surface'])
obj_b.data.materials.append(mat_plain)

m_box = obj_b.modifiers.new("Simple Box Creator", 'NODES')
m_box.node_group = ng_box
for k, v in {
    'Width':1.0,'Length':1.0,'Height':1.0,
    'Gaps (Length)':0.07,'Gap (Width)':0.07,'Flap Length':0.11,
    'Simple Sub-D Level':3,'CC Sub-D Level':0,
    'Edge Crease':0.802,'Delete Bounds':False,
}.items(): set_input(m_box, k, v)

m_smooth_b = obj_b.modifiers.new("Smooth by Angle", 'NODES')
m_smooth_b.node_group = ng_smooth
set_input(m_smooth_b, 'Angle', 0.5236)
set_input(m_smooth_b, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = obj_b
bpy.ops.object.modifier_apply(modifier="Simple Box Creator")
# reattach kraft material if dropped
if not obj_b.data.materials or obj_b.data.materials[0] is None:
    obj_b.data.materials.clear()
    obj_b.data.materials.append(mat_plain)
bpy.ops.object.modifier_apply(modifier="Smooth by Angle")
log(f"   before mesh: {len(obj_b.data.vertices)} verts, mat={obj_b.data.materials[0].name if obj_b.data.materials else None}")

glb_before = os.path.join(OUTPUT_DIR, "before.glb")
for o in bpy.data.objects: o.select_set(False)
obj_b.select_set(True)
bpy.context.view_layer.objects.active = obj_b
bpy.ops.export_scene.gltf(filepath=glb_before, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
log(f"   exported -> {glb_before}")

# remove the before object so we don't bake it
bpy.data.objects.remove(obj_b, do_unlink=True)

# ---- 3. Build AFTER: same shape via Simple Box Creator, but APPLY box first, then
#         unwrap, then apply Cardboard. This way bake target is on a real mesh with UVs. ----
log(f"=== AFTER: SBC -> apply -> unwrap -> Easy Cardboard wear={WEAR} -> apply -> bake -> GLB ===")

mesh_a = bpy.data.meshes.new("BoxAfter")
obj_a = bpy.data.objects.new("BoxAfter", mesh_a)
bpy.context.collection.objects.link(obj_a)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
bm.to_mesh(mesh_a); bm.free()

# Apply Simple Box Creator FIRST (no material yet)
m_box_a = obj_a.modifiers.new("Simple Box Creator", 'NODES')
m_box_a.node_group = ng_box
for k, v in {
    'Width':1.0,'Length':1.0,'Height':1.0,
    'Gaps (Length)':0.07,'Gap (Width)':0.07,'Flap Length':0.11,
    'Simple Sub-D Level':3,'CC Sub-D Level':0,
    'Edge Crease':0.802,'Delete Bounds':False,
}.items(): set_input(m_box_a, k, v)

bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = obj_a
bpy.ops.object.modifier_apply(modifier="Simple Box Creator")
log(f"   post-SBC: {len(obj_a.data.vertices)} verts, {len(obj_a.data.polygons)} faces")
log(f"   post-SBC UV: {[l.name for l in obj_a.data.uv_layers]}")

# Now unwrap on the box shape
obj_a.select_set(True)
bpy.context.view_layer.objects.active = obj_a
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
# cube_project gives cleaner UV continuity per face vs smart_project's angle-based islands,
# which is what the cardboard shader expects for its UV-direction-mask logic.
bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
if obj_a.data.uv_layers:
    uvl = obj_a.data.uv_layers[0]
    uvl.name = 'UVMap'
    uvl.active = True
    uvl.active_render = True
us = [d.uv[0] for d in obj_a.data.uv_layers[0].data]
vs = [d.uv[1] for d in obj_a.data.uv_layers[0].data]
log(f"   UV after unwrap: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}] loops={len(us)}")

# Attach Easy Cardboard material
obj_a.data.materials.clear()
obj_a.data.materials.append(mat_cardboard)
log(f"   material attached: {mat_cardboard.name}")

# Add cardboard modifier
m_cb_a = obj_a.modifiers.new("GeometryNodes", 'NODES')
m_cb_a.node_group = ng_cb
for k, v in {
    'Thickness':0.01,'Global Scale':1.0,'Wear ⏰':WEAR,'Seed \U0001F3B2':0,
    'Split Angle':0.5236,'Strength':0.2,
    'Separation':1.0,'Separation Noise Scale':0.0,'Z Position':1.0,
    ' Fibers Density':2.0,'Fibers Size':0.02,
    'Roughness ':1.0,'Metallic':0.0,'Clearcoat':0.0,
    'Displacement Strength':0.161,'Normal Strength':1.0,
    'Print Roughness':0.5,'Direction Mask Threshold':2.0,'Invert':False,
    'UV Name':'UVMap',
}.items(): set_input(m_cb_a, k, v)

# Smooth by Angle
m_smooth_a = obj_a.modifiers.new("Smooth by Angle", 'NODES')
m_smooth_a.node_group = ng_smooth
set_input(m_smooth_a, 'Angle', 0.5236)
set_input(m_smooth_a, 'Ignore Sharpness', False)

bpy.context.view_layer.update()
log("   applying GeometryNodes (cardboard)")
bpy.ops.object.modifier_apply(modifier="GeometryNodes")
if not obj_a.data.materials or obj_a.data.materials[0] is None:
    obj_a.data.materials.clear()
    obj_a.data.materials.append(mat_cardboard)
    log("   re-attached material after Cardboard apply")

log("   applying Smooth by Angle")
bpy.ops.object.modifier_apply(modifier="Smooth by Angle")
if not obj_a.data.materials or obj_a.data.materials[0] is None:
    obj_a.data.materials.clear()
    obj_a.data.materials.append(mat_cardboard)

# IMPORTANT: keep the UV map that the cardboard plugin works with — do NOT re-unwrap.
# The shader uses UV-direction-mask logic; smart_project on the FINAL geometry
# destroys those islands and gives broken bakes.
# Just ensure the existing UV is active for bake target.
if obj_a.data.uv_layers:
    obj_a.data.uv_layers[0].active = True
    obj_a.data.uv_layers[0].active_render = True
    log(f"   keeping plugin UV layer: '{obj_a.data.uv_layers[0].name}'")

log(f"   final mesh: {len(obj_a.data.vertices)} verts, {len(obj_a.data.polygons)} faces")
log(f"   final UV layers: {[l.name for l in obj_a.data.uv_layers]}")
log(f"   final materials: {[m.name if m else None for m in obj_a.data.materials]}")

# Check UV range again (cardboard may have remapped)
us = [d.uv[0] for d in obj_a.data.uv_layers[0].data]
vs = [d.uv[1] for d in obj_a.data.uv_layers[0].data]
log(f"   final UV range: u=[{min(us):.3f},{max(us):.3f}] v=[{min(vs):.3f},{max(vs):.3f}] loops={len(us)}")

# ---- 4. Bake ----
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

mat = obj_a.data.materials[0]
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    if n.name == "BAKE_TARGET":
        nt.nodes.remove(n)
bake_node = nt.nodes.new('ShaderNodeTexImage')
bake_node.name = "BAKE_TARGET"
bake_node.location = (-600, -400)
log(f"   bake target injected. material '{mat.name}', node tree has {len(nt.nodes)} nodes")

def bake_to(image, bake_type, label):
    log(f"   baking {label} ({bake_type}) @ {BAKE_RES}^2 ...")
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
    log(f"      saved -> {p} ({image.size[0]}x{image.size[1]})")

for o in bpy.data.objects: o.select_set(False)
obj_a.select_set(True)
bpy.context.view_layer.objects.active = obj_a

bake_to(img_color, 'DIFFUSE', 'color')
bake_to(img_normal, 'NORMAL', 'normal')
bake_to(img_rough, 'ROUGHNESS', 'roughness')

# ---- 5. Swap to Principled BSDF baked, export GLB ----
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
tr = bnt.nodes.new('ShaderNodeTexImage'); tr.image=img_rough
tr.image.colorspace_settings.name='Non-Color'; tr.location=(-400,-50)
bnt.links.new(tr.outputs['Color'], bsdf.inputs['Roughness'])
tn = bnt.nodes.new('ShaderNodeTexImage'); tn.image=img_normal
tn.image.colorspace_settings.name='Non-Color'; tn.location=(-400,-300)
nm = bnt.nodes.new('ShaderNodeNormalMap'); nm.location=(-100,-300)
bnt.links.new(tn.outputs['Color'], nm.inputs['Color'])
bnt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
obj_a.data.materials.clear()
obj_a.data.materials.append(baked)

glb_after = os.path.join(OUTPUT_DIR, "after.glb")
for o in bpy.data.objects: o.select_set(False)
obj_a.select_set(True)
bpy.context.view_layer.objects.active = obj_a
bpy.ops.export_scene.gltf(filepath=glb_after, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
log(f"   exported -> {glb_after}")

log("=== DONE ===")
print("[PAIR2] === SUCCESS ===", flush=True)
