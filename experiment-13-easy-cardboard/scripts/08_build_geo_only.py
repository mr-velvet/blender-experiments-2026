"""
Passo 3+4+5 — pipeline geo-only.

Objetivo: provar que o Easy Cardboard 3.0 produz GEOMETRIA real (solidify +
edge split 3D + displacement + hairs como mesh) headless via Python, exportando
GLB SEM bake, SEM textura, SEM Cycles.

Fluxo:
  1. Append node groups (Simple Box Creator, Easy Cardboard 3.0, Smooth by Angle)
     do .blend do asset. NAO importa o material complexo (e shader, irrelevante aqui).
  2. Mesh base: plane subdivided, Simple Box Creator (defaults) -> apply.
     Resultado: caixa de papelao parametrica com flaps abertos.
  3. UV: cube_project pra gerar UV seams em todas as quinas
     (necessario pro Edge Split do EC funcionar no modo 'UV Seam').
  4. Cardboard com preset MAXIMO de distorcao geometrica aprovado pelo user:
     Wear=1.0, Strength=1.0, Separation=5.0, Sep Noise=5.0, Displacement=1.0,
     Split Angle=5deg, Fibers Density=50, Fibers Size=0.1, Thickness=0.04, Seed=7.
  5. Snapshot verts/faces ANTES e DEPOIS do apply (passo 4 da task list).
  6. Kraft Principled BSDF chapado (sem textura) so pro GLB nao sair branco.
  7. Export GLB.
  8. Render Eevee 512x512 single-frame (passo 5 da task list) pra checagem visual.
"""
import bpy
import bmesh
import os
import sys
import json
import math
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "geo_only")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"

def log(m): print(f"[GEO] {m}", flush=True)

# ---- 1. Clean & append ----
log("Clean scene")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for blk in list(bpy.data.meshes): bpy.data.meshes.remove(blk)
for blk in list(bpy.data.materials): bpy.data.materials.remove(blk)
for blk in list(bpy.data.lights): bpy.data.lights.remove(blk)

log("Append node groups (NO material — geo only)")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = [n for n in (NG_BOX, NG_CARDBOARD, NG_SMOOTH) if n in data_from.node_groups]
for name in (NG_BOX, NG_CARDBOARD, NG_SMOOTH):
    assert name in bpy.data.node_groups, f"missing node group: {name}"
ng_box = bpy.data.node_groups[NG_BOX]
ng_cb = bpy.data.node_groups[NG_CARDBOARD]
ng_smooth = bpy.data.node_groups[NG_SMOOTH]

def set_input(mod, name, value):
    ng = mod.node_group
    target = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == target:
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"   FAIL set '{name}'={value}: {e}")
                return False
    log(f"   socket '{name}' not found in {ng.name}")
    return False

# ---- 2. Mesh base + Simple Box Creator ----
log("Building base mesh: plane 4-face grid")
mesh = bpy.data.meshes.new("Box")
obj = bpy.data.objects.new("Box", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
bm.to_mesh(mesh); bm.free()
log(f"   base: {len(mesh.vertices)}v / {len(mesh.polygons)}f")

log("Add Simple Box Creator modifier")
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
log(f"   post-SBC: {len(obj.data.vertices)}v / {len(obj.data.polygons)}f / uv layers={[l.name for l in obj.data.uv_layers]}")

# Snapshot for comparison ANTES do cardboard
verts_before = len(obj.data.vertices)
faces_before = len(obj.data.polygons)
bbox_before = [list(c) for c in obj.bound_box]

# ---- 3. UV cube_project ----
log("UV cube_project (so o Edge Split do EC tem seams em todas as quinas)")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=True)
# Marca seams nas edges com angulo agudo, pro modo 'UV Seam' tambem cair em quinas internas
bpy.ops.mesh.mark_seam(clear=False)
bpy.ops.object.mode_set(mode='OBJECT')
if obj.data.uv_layers:
    obj.data.uv_layers[0].name = 'UVMap'
    obj.data.uv_layers[0].active = True
    obj.data.uv_layers[0].active_render = True

# ---- 4. Easy Cardboard com preset MAXIMO ----
log("Add Easy Cardboard 3.0 modifier with MAX distortion preset")
m_cb = obj.modifiers.new("EasyCardboard", 'NODES')
m_cb.node_group = ng_cb

PRESET_MAX = {
    'Thickness': 0.04,
    'Global Scale': 1.0,
    'Wear ⏰': 1.0,
    'Seed 🎲': 7,
    # 'Edge Split' menu fica no default 'UV Seam'
    'Split Angle': math.radians(5.0),
    'Strength': 1.0,
    'Separation': 5.0,
    'Separation Noise Scale': 5.0,
    'Z Position': 1.0,
    ' Fibers Density': 50.0,   # nome tem espaco a esquerda no asset
    'Fibers Size': 0.1,
    'Displacement Strength': 1.0,
    'Normal Strength': 1.0,
    'UV Name': 'UVMap',
}
for k, v in PRESET_MAX.items():
    set_input(m_cb, k, v)

log("Add Smooth by Angle (apos o cardboard, pra suavizar normals)")
m_smooth = obj.modifiers.new("SmoothByAngle", 'NODES')
m_smooth.node_group = ng_smooth
set_input(m_smooth, 'Angle', math.radians(30.0))
set_input(m_smooth, 'Ignore Sharpness', False)

bpy.context.view_layer.update()

log("Apply Easy Cardboard")
bpy.ops.object.modifier_apply(modifier="EasyCardboard")
log("Apply Smooth by Angle")
bpy.ops.object.modifier_apply(modifier="SmoothByAngle")

verts_after = len(obj.data.vertices)
faces_after = len(obj.data.polygons)
bbox_after = [list(c) for c in obj.bound_box]

# ---- 5. Snapshot comparison ----
ratio_v = verts_after / max(verts_before, 1)
ratio_f = faces_after / max(faces_before, 1)
log("=" * 60)
log(f"BEFORE Easy Cardboard: {verts_before}v / {faces_before}f")
log(f"AFTER  Easy Cardboard: {verts_after}v / {faces_after}f")
log(f"Ratio: {ratio_v:.1f}x verts / {ratio_f:.1f}x faces")
log("=" * 60)

stats = {
    "preset": PRESET_MAX,
    "verts_before": verts_before, "faces_before": faces_before, "bbox_before": bbox_before,
    "verts_after": verts_after, "faces_after": faces_after, "bbox_after": bbox_after,
    "ratio_verts": ratio_v, "ratio_faces": ratio_f,
}
stats_path = os.path.join(OUTPUT_DIR, "stats.json")
with open(stats_path, "w") as f:
    json.dump(stats, f, indent=2, default=str)
log(f"stats -> {stats_path}")

# ---- 6. Kraft chapado pro GLB nao sair branco ----
log("Kraft Principled BSDF chapado (sem textura)")
mat = bpy.data.materials.new("KraftPlain")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (100, 0)
bsdf.inputs['Base Color'].default_value = (0.55, 0.38, 0.22, 1.0)  # kraft marrom
bsdf.inputs['Roughness'].default_value = 0.85
nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
obj.data.materials.clear()
obj.data.materials.append(mat)

# ---- 7. Export GLB ----
log("Export GLB (no bake, no texture)")
glb_path = os.path.join(OUTPUT_DIR, "cardboard_geo_only.glb")
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True,
    export_image_format='NONE',
)
glb_size_kb = os.path.getsize(glb_path) / 1024
log(f"   GLB -> {glb_path}  ({glb_size_kb:.1f} KB)")

# ---- 8. Render Eevee 512 single-frame ----
log("Eevee 512 single-frame render (sanity check)")
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(OUTPUT_DIR, "preview.png")

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (2.6, -2.6, 1.9)
cam.rotation_euler = (math.radians(65), 0, math.radians(45))
scene.camera = cam

# Sun light
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = (3, -2, 5)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

# World ambient cinza
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0)
    bg.inputs[1].default_value = 1.0

bpy.ops.render.render(write_still=True)
log(f"   render -> {scene.render.filepath}")

# Salva o .blend final pra debug
blend_path = os.path.join(OUTPUT_DIR, "cardboard_geo_only.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
log(f"   blend -> {blend_path}")

log("=== DONE ===")
print("[GEO] === SUCCESS ===", flush=True)
