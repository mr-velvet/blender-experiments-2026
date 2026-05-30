# -*- coding: utf-8 -*-
"""
experiment-28 / 01_inspect.py
Inspeciona a casa "The Lonely Outpost" (variante B, chao liso) pra montar
um tour de camera entrando/saindo. Faz:
  - acha a scene certa
  - mede o bbox da casa (Cube.*) em world space
  - dump de todos os objetos relevantes com loc/bbox
  - salva um JSON com a geometria pra etapas seguintes
Roda headless: blender --background <blend> --python 01_inspect.py -- <out_json>
"""
import bpy, sys, os, json, mathutils

SCENE_NAME = "The Lonely Outpost"

def get_scene():
    for s in bpy.data.scenes:
        if s.name == SCENE_NAME:
            return s
    return max(bpy.data.scenes, key=lambda s: len(s.objects))

def world_bbox(o):
    cs = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    xs = [c.x for c in cs]; ys = [c.y for c in cs]; zs = [c.z for c in cs]
    return [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]

def main():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out_json = argv[0] if argv else "inspect.json"

    sc = get_scene()
    bpy.context.window.scene = sc
    print("ACTIVE SCENE:", sc.name, "objs:", len(sc.objects))

    data = {"scene": sc.name, "objects": [], "house_bbox": None}
    house_min = [1e9]*3; house_max = [-1e9]*3
    house_meshes = []

    for o in sc.objects:
        rec = {
            "name": o.name,
            "type": o.type,
            "loc": [round(v, 3) for v in o.location],
        }
        if o.type == 'MESH':
            mn, mx = world_bbox(o)
            rec["bbox_min"] = [round(v, 3) for v in mn]
            rec["bbox_max"] = [round(v, 3) for v in mx]
            nl = o.name.lower()
            if nl.startswith("cube"):
                house_meshes.append(o.name)
                for i in range(3):
                    house_min[i] = min(house_min[i], mn[i])
                    house_max[i] = max(house_max[i], mx[i])
        data["objects"].append(rec)

    data["house_meshes"] = house_meshes
    data["house_bbox"] = {
        "min": [round(v, 3) for v in house_min],
        "max": [round(v, 3) for v in house_max],
        "center": [round((house_min[i]+house_max[i])/2, 3) for i in range(3)],
        "size": [round(house_max[i]-house_min[i], 3) for i in range(3)],
    }

    # cameras existentes
    data["cameras"] = [o.name for o in sc.objects if o.type == 'CAMERA']

    print("HOUSE MESHES:", house_meshes)
    print("HOUSE BBOX:", data["house_bbox"])
    print("CAMERAS:", data["cameras"])

    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("WROTE:", out_json)

main()
