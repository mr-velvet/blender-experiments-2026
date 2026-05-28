"""Valida o fix do furo: cage posicionado como o addon (loc.y=0, Dim Y >= espessura),
boolean DIFFERENCE -> a parede avaliada deve ficar com buraco PASSANTE.

Teste de buraco passante: amostrar a mesh avaliada da parede e confirmar que existe
geometria atras E na frente do vao, mas vazio no meio (em Y) na altura do vao.
Mais simples: contar faces/verts antes e depois, e medir se o boolean criou loops
internos (verts com Y entre 0 e T dentro da regiao do vao).
"""
import bpy, sys, os, importlib
import mathutils
sys.path.append(os.path.dirname(__file__))
import hb_lib
importlib.reload(hb_lib)
hb_lib.reset_scene()

M = "bl_ext.blender_org.home_builder_5"
hb_types = importlib.import_module(f"{M}.hb_types")

T = 0.1143
w = hb_lib.new_wall("W", 6.0, (0,0,0), 0, thickness=T, height=2.4384)

# cage como o addon: parent na parede, loc.y=0, Dim Y = T (+ pequena folga p/ boolean limpo)
folga = 0.02
cage = hb_types.GeoNodeCage(); cage.create("Door")
cage.obj['IS_ENTRY_DOOR_BP'] = True
cage.set_input('Dim X', 0.9144)
cage.set_input('Dim Y', T + folga)
cage.set_input('Dim Z', 2.1336)
# Show Cage default (None) ja gera 8 verts solidos
cage.obj.parent = w.obj
# Dim Y cresce de 0 a Dim Y em +Y; a parede vai de 0 a T. Centralizar o overshoot:
cage.obj.location = (2.5, -folga/2, 0)

mod = w.obj.modifiers.new(name="Bool", type='BOOLEAN')
mod.operation = 'DIFFERENCE'; mod.object = cage.obj; mod.solver = 'EXACT'
cage.obj.hide_render = True

bpy.context.view_layer.update()

deps = bpy.context.evaluated_depsgraph_get()
ev = w.obj.evaluated_get(deps)
me = ev.to_mesh()
nv = len(me.vertices); nf = len(me.polygons)
print(f"[WALL pos-boolean] verts={nv} faces={nf}")

# teste de passante: numa linha vertical no centro do vao (x=2.96, z=1.0),
# varrer Y e ver se ha material. Em buraco passante, NENHUM vert da parede deve
# existir nessa coluna (vao vazio). Vamos checar se ha faces cruzando essa coluna.
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
# raycast em Y atravessando o centro do vao
mw = w.obj.matrix_world
hit_ys = []
# usar bvh
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromBMesh(bm)
origin = mathutils.Vector((2.96, -1.0, 1.0))
direction = mathutils.Vector((0,1,0))
loc = origin.copy()
for _ in range(8):
    hit = bvh.ray_cast(loc + direction*0.0001, direction)
    if hit[0] is None: break
    hit_ys.append(round(hit[0].y,4))
    loc = hit[0]
print(f"  raycast Y atravessando centro do vao (x=2.96,z=1.0): hits em Y={hit_ys}")
print(f"  -> {'PASSANTE OK (0 hits = vazio no centro do vao)' if len(hit_ys)==0 else 'NAO passante: '+str(len(hit_ys))+' faces no caminho'}")

# controle: coluna numa regiao SEM vao (x=5.0) deve ter 2 hits (entra e sai)
loc = mathutils.Vector((5.0, -1.0, 1.0))
hit_ys2 = []
for _ in range(8):
    hit = bvh.ray_cast(loc + direction*0.0001, direction)
    if hit[0] is None: break
    hit_ys2.append(round(hit[0].y,4)); loc = hit[0]
print(f"  controle (x=5.0, parede cheia): hits em Y={hit_ys2} (esperado ~2: parede solida)")
bm.free(); ev.to_mesh_clear()
