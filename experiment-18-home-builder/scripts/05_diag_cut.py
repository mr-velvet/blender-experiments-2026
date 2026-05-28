"""Diagnostico do furo: por que o boolean so marca raso em vez de vazar a parede.

Mede, em coordenadas LOCAIS da parede:
  - bbox da parede avaliada (sem o cut) -> onde estao as faces e qual a espessura real em Y
  - bbox do cage avaliado (em world e em local-da-parede) -> ele atravessa toda a espessura?
Testa o posicionamento que o ADDON usa (location.y=0, Dim Y=wall_thickness) vs o nosso.
"""
import bpy, sys, os, importlib
import mathutils
sys.path.append(os.path.dirname(__file__))
import hb_lib
importlib.reload(hb_lib)
hb_lib.reset_scene()

M = "bl_ext.blender_org.home_builder_5"
hb_types = importlib.import_module(f"{M}.hb_types")


def eval_mesh_bbox(obj, matrix=None):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    n = len(me.vertices)
    if n == 0:
        ev.to_mesh_clear()
        return n, None
    mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
    mw = obj.matrix_world
    for v in me.vertices:
        co = mw @ v.co if matrix is None else matrix @ (mw @ v.co)
        for i in range(3):
            mn[i] = min(mn[i], co[i]); mx[i] = max(mx[i], co[i])
    ev.to_mesh_clear()
    return n, (tuple(round(c,4) for c in mn), tuple(round(c,4) for c in mx))


# parede simples
T = 0.1143
w = hb_lib.new_wall("DiagWall", 6.0, (0,0,0), 0, thickness=T, height=2.4384)
bpy.context.view_layer.update()
n, bb = eval_mesh_bbox(w.obj)
print(f"\n[WALL] verts={n} world_bbox={bb}")
print(f"  -> espessura real em Y = {round(bb[1][1]-bb[0][1],4)} (Thickness setado={T})")

# cage do jeito ADDON: location.y=0, Dim Y = wall_thickness, sem Show Cage
print("\n--- CAGE estilo ADDON (loc.y=0, Dim Y=T, Show Cage default) ---")
for show in (None, True, False):
    cage = hb_types.GeoNodeCage()
    cage.create(f"AddonCage_{show}")
    cage.set_input('Dim X', 0.9144)
    cage.set_input('Dim Y', T)
    cage.set_input('Dim Z', 2.1336)
    if show is not None:
        cage.set_input('Show Cage', show)
    cage.obj.parent = w.obj
    cage.obj.location = (2.5, 0, 0)
    bpy.context.view_layer.update()
    n, bb = eval_mesh_bbox(cage.obj)
    print(f"  Show={show}: verts={n} world_bbox={bb}")

# inspeciona o node group do cage: ha um Switch (Show Cage) que zera a geometria?
cage = hb_types.GeoNodeCage(); cage.create("InspectCage2")
mod = cage.obj.modifiers[cage.obj.home_builder.mod_name]
ng = mod.node_group
print(f"\n[CAGE node_group={ng.name}] nodes:")
for nd in ng.nodes:
    extra = ""
    if nd.type == 'GROUP' and nd.node_tree:
        extra = f" -> {nd.node_tree.name}"
    print(f"  {nd.type:22s} {nd.name}{extra}")
