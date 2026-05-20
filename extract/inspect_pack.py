"""Inspeciona um .blend ou .fbx e lista meshes/objetos/collections.
Uso:
  blender --background --python inspect_pack.py -- --src <arquivo>
"""
import bpy, sys, json, os
from pathlib import Path

def parse_args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"src": None}
    i = 0
    while i < len(a):
        if a[i] == "--src":
            out["src"] = a[i+1]; i += 2
        else:
            i += 1
    return out

args = parse_args()
src = args["src"]
ext = Path(src).suffix.lower()

bpy.ops.wm.read_factory_settings(use_empty=True)
if ext == ".blend":
    with bpy.data.libraries.load(src, link=False) as (df, dt):
        dt.objects = df.objects
        dt.collections = df.collections
    # vincula a cena
    for o in dt.objects:
        if o is not None:
            bpy.context.scene.collection.objects.link(o)
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=src)
else:
    raise SystemExit(f"ext nao suportada: {ext}")

objs = [o for o in bpy.data.objects]
meshes = [o for o in objs if o.type == 'MESH']
collections = [c.name for c in bpy.data.collections]

# tenta agrupar por collection
by_coll = {}
for o in meshes:
    cols = [c.name for c in o.users_collection]
    key = cols[0] if cols else "(no_collection)"
    by_coll.setdefault(key, []).append(o.name)

report = {
    "src": src,
    "total_objects": len(objs),
    "total_meshes": len(meshes),
    "total_collections": len(collections),
    "collections": collections[:30],
    "by_collection_sample": {k: v[:5] for k, v in list(by_coll.items())[:20]},
    "mesh_names_sample": [o.name for o in meshes[:30]],
    "parented_meshes": sum(1 for o in meshes if o.parent is not None),
    "root_meshes": sum(1 for o in meshes if o.parent is None),
}

out_path = Path(src).with_suffix(".inventory.json")
out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print("WROTE", out_path)
print(json.dumps(report, indent=2, ensure_ascii=False))
