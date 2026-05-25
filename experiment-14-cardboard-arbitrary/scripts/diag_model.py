"""
Diagnostico do que o Easy Cardboard faz com a malha da casa: importa o GLB,
mede a malha crua (manifold? espessura? faces soltas?), aplica o preset AGED,
mede de novo. NAO renderiza. Objetivo: descobrir a causa do estilhacamento
pra escrever o relatorio de erro com numeros reais, nao so leitura visual.

Uso: blender --background --python diag_model.py -- <glb>
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
GLB = argv[0]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(os.path.dirname(ROOT),
                           "experiment-13-easy-cardboard",
                           "assets", "easy-cardboard-3.1.blend")
NODE_GROUP_NAME = "\U0001F4E6 Easy Cardboard 3.0"
MATERIAL_NAME = "Easy Cardboard 3"

def log(m): print(f"[DIAG] {m}", flush=True)

AGED = {
    "Thickness": 0.006, "Global Scale": 0.5, "Wear ⏰": 0.7,
    "Seed \U0001F3B2": 7, "Split Angle": math.radians(35), "Strength": 0.35,
    "Separation": 1.0, "Separation Noise Scale": 0.0, "Z Position": 1.0,
    " Fibers Density": 8.0, "Fibers Size": 0.02, "Displacement Strength": 0.4,
    "Normal Strength": 1.0, "Roughness ": 0.9, "Metallic": 0.0, "UV Name": "UVMap",
}

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for c in list(bpy.data.materials): bpy.data.materials.remove(c)

with bpy.data.libraries.load(ASSET_BLEND, link=False) as (src, dst):
    dst.node_groups = [NODE_GROUP_NAME]
    dst.materials = [MATERIAL_NAME]
cardboard_ng = bpy.data.node_groups.get(NODE_GROUP_NAME)
cardboard_mat = bpy.data.materials.get(MATERIAL_NAME)

bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects: o.select_set(False)
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.context.view_layer.update()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
center = sum(bb, Vector()) / 8.0
obj.location -= center
bpy.ops.object.transform_apply(location=True)
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
maxdim = max((max(p[i] for p in bb) - min(p[i] for p in bb)) for i in range(3))
s = 0.3 / maxdim
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)

# === medir a malha crua ===
me = obj.data
bm = bmesh.new(); bm.from_mesh(me)
n_verts = len(bm.verts); n_faces = len(bm.faces); n_edges = len(bm.edges)
# arestas de borda = pertencem a 1 face so (malha aberta / nao-manifold)
boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) > 2)
# faces soltas (vertices sem ligacao solida)
log(f"=== MALHA CRUA (casa, normalizada p/ 0.3 de bounding) ===")
log(f"  verts={n_verts}  edges={n_edges}  faces={n_faces}")
log(f"  arestas de BORDA (1 face)= {boundary}  ({100*boundary/max(n_edges,1):.1f}% das arestas)")
log(f"  arestas NAO-MANIFOLD (>2 faces)= {nonmanifold}")
log(f"  => malha {'ABERTA/casca fina' if boundary>0 else 'fechada/solida'}")
bm.free()

# smart uv
bpy.context.view_layer.objects.active = obj
for o in bpy.data.objects: o.select_set(False)
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
if obj.data.uv_layers:
    obj.data.uv_layers[0].name = 'UVMap'
    obj.data.uv_layers[0].active_render = True

obj.data.materials.clear()
obj.data.materials.append(cardboard_mat)
mod = obj.modifiers.new(name="EasyCardboard", type='NODES')
mod.node_group = cardboard_ng

def set_input(name, value):
    ng = mod.node_group
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == name.strip():
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"  FAIL '{name}': {e}"); return False
    log(f"  socket '{name}' NAO encontrado")
    return False

for k, v in AGED.items():
    set_input(k, v)
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier="EasyCardboard")
log(f"=== APOS APLICAR EASY CARDBOARD (AGED) ===")
log(f"  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
log(f"  fator de explosao: {len(obj.data.polygons)/max(n_faces,1):.1f}x faces")
print("[DIAG] === DONE ===", flush=True)
