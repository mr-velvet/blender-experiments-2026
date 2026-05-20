"""Mapeia hierarquia completa: BUILDINGS/ANIMALS > categorias > assets > meshes.
Uso: blender --background --python inspect_hierarchy.py -- --src <blend>
"""
import bpy, sys, json
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

bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(src, link=False) as (df, dt):
    dt.objects = df.objects

for o in dt.objects:
    if o is not None:
        bpy.context.scene.collection.objects.link(o)

roots = [o for o in bpy.data.objects if o.parent is None and o.type == 'EMPTY']

def walk(obj, depth=0, info=None):
    if info is None:
        info = {"levels": {}, "leaves": [], "categories": {}}
    info["levels"].setdefault(depth, 0)
    info["levels"][depth] += 1
    if obj.type == 'MESH' or len(obj.children) == 0:
        info["leaves"].append(obj.name)
    for c in obj.children:
        walk(c, depth+1, info)
    return info

for r in roots:
    print(f"\n=== ROOT: {r.name} (type={r.type}, n_children={len(r.children)}) ===")
    for cat in r.children:
        sub_info = walk(cat)
        n_descendants = sum(sub_info["levels"].values())
        n_meshes = sum(1 for n in sub_info["leaves"] if bpy.data.objects.get(n) and bpy.data.objects[n].type == 'MESH')
        print(f"  CAT {cat.name} (type={cat.type}) -> {len(cat.children)} filhos diretos, {n_descendants} descendentes, levels={sub_info['levels']}")
        # mostra primeiros filhos diretos (que devem ser os assets individuais)
        for asset in cat.children[:5]:
            asset_info = walk(asset)
            n_mesh_in_asset = sum(1 for n in asset_info["leaves"] if bpy.data.objects.get(n) and bpy.data.objects[n].type == 'MESH')
            print(f"    ASSET {asset.name} (type={asset.type}) -> {len(asset.children)} filhos, {sum(asset_info['levels'].values())} descendentes, {n_mesh_in_asset} meshes")
        if len(cat.children) > 5:
            print(f"    ... e mais {len(cat.children)-5}")
