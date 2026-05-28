"""Debug: o GeoNodeCage gera geometria solida (pra servir de boolean cutter)?
Testa com Show Cage True/False e mede o bbox da mesh avaliada."""
import bpy, sys, os, importlib
sys.path.append(os.path.dirname(__file__))
import hb_lib
hb_lib.ensure_addon()

importlib.reload(hb_lib)
hb_lib.ensure_addon()

M = "bl_ext.blender_org.home_builder_5"
hb_types = importlib.import_module(f"{M}.hb_types")


def eval_bbox(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    n = len(me.vertices)
    if n == 0:
        ev.to_mesh_clear()
        return n, None
    import mathutils
    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    for v in me.vertices:
        for i in range(3):
            mn[i] = min(mn[i], v.co[i]); mx[i] = max(mx[i], v.co[i])
    ev.to_mesh_clear()
    return n, (tuple(round(c,3) for c in mn), tuple(round(c,3) for c in mx))


for show in (True, False):
    cage = hb_types.GeoNodeCage()
    cage.create(f"Cage_show{show}")
    cage.set_input('Dim X', 1.0)
    cage.set_input('Dim Y', 0.2)
    cage.set_input('Dim Z', 2.0)
    cage.set_input('Show Cage', show)
    bpy.context.view_layer.update()
    n, bbox = eval_bbox(cage.obj)
    print(f"[cage Show={show}] verts={n} bbox={bbox}")

# inputs/outputs do node group cage
mod = cage.obj.modifiers[cage.obj.home_builder.mod_name]
ng = mod.node_group
print("\nNODES no GeoNodeCage:")
for nd in ng.nodes:
    print(f"  {nd.type:20s} {nd.name}")
