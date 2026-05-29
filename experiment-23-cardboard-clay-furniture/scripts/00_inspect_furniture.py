"""Inspeciona os 4 .blend de moveis (BlenderKit) pra entender estrutura/escala/densidade.

Uso: blender --background --python 00_inspect_furniture.py -- <slug> <blend_path>
"""
import bpy, sys, json, os

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
slug, blend_path = argv[0], argv[1]

# append TUDO (objetos) do blend
with bpy.data.libraries.load(blend_path, link=False) as (df, dt):
    dt.objects = list(df.objects)
    dt.collections = list(df.collections)

info = {"slug": slug, "blend": blend_path, "objects": [], "total_verts": 0, "total_tris": 0}
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
# bbox global de todos os meshes
import mathutils
mins = [1e9]*3; maxs = [-1e9]*3
for o in mesh_objs:
    me = o.data
    me.calc_loop_triangles()
    v = len(me.vertices); t = len(me.loop_triangles)
    info["total_verts"] += v; info["total_tris"] += t
    mats = [m.name for m in o.data.materials if m]
    uvs = [uv.name for uv in me.uv_layers]
    info["objects"].append({
        "name": o.name, "verts": v, "tris": t,
        "materials": mats, "uv_layers": uvs,
        "modifiers": [m.type for m in o.modifiers],
        "dims": [round(x,3) for x in o.dimensions],
    })
    for corner in o.bound_box:
        wc = o.matrix_world @ mathutils.Vector(corner)
        for i in range(3):
            mins[i] = min(mins[i], wc[i]); maxs[i] = max(maxs[i], wc[i])

info["n_mesh_objs"] = len(mesh_objs)
info["bbox_min"] = [round(x,3) for x in mins]
info["bbox_max"] = [round(x,3) for x in maxs]
info["bbox_size"] = [round(maxs[i]-mins[i],3) for i in range(3)]

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", f"inspect_{slug}.json")
with open(out, "w") as f: json.dump(info, f, indent=2)
print(f"[INSPECT] {slug}: {len(mesh_objs)} meshes, {info['total_verts']}v / {info['total_tris']}tris, size={info['bbox_size']}")
print(f"[INSPECT] saved {out}")
