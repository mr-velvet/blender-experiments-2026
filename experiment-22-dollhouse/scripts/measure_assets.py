"""mede o bbox nativo de cada asset baixado (dim X/Y/Z em metros) + n objetos.
Revela assets com escala estranha ou geometria fora do lugar.
  blender --background --python measure_assets.py
"""
import bpy, sys, os, json
from mathutils import Vector

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
manifest = json.load(open(os.path.join(OUT_DIR, "downloads.json"), encoding="utf-8"))


def bbox(objs):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3); f = False
    for o in objs:
        if o.type not in {'MESH','CURVE','SURFACE','FONT','META'}: continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
            f=True
    return (mn,mx) if f else (None,None)

results = {}
for abid, rec in manifest.items():
    # cena limpa
    bpy.ops.wm.read_homefile(use_empty=True)
    with bpy.data.libraries.load(rec["path"], link=False) as (df, dt):
        cname = df.collections[0] if df.collections else None
        dt.collections = [cname] if cname else []
    objs = []
    for c in dt.collections:
        if c:
            for o in c.objects:
                bpy.context.scene.collection.objects.link(o); objs.append(o)
    mn, mx = bbox(objs)
    if mn is None:
        sz = None
    else:
        sz = [round(mx[i]-mn[i],3) for i in range(3)]
    n_mesh = sum(1 for o in objs if o.type=='MESH')
    results[abid] = {"name": rec["name"], "dim_xyz": sz, "n_obj": len(objs), "n_mesh": n_mesh}
    print(f"[meas] {rec['name'][:34]:36s} dim={sz} objs={len(objs)}", flush=True)

with open(os.path.join(OUT_DIR, "asset_dims.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("[meas] DONE", flush=True)
