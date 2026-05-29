"""inspect_scene.py — dump da geometria: objetos, nomes, bbox, e a camera original."""
import bpy, sys, json
from mathutils import Vector

sc = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        sc = s; break
sc = sc or bpy.context.scene

def bbox(o):
    mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    return mn, mx

objs = []
for o in sc.objects:
    mn, mx = bbox(o) if o.type in ("MESH","CURVE") else (Vector((0,0,0)),Vector((0,0,0)))
    sz = mx - mn
    objs.append({
        "name": o.name, "type": o.type,
        "loc": [round(v,1) for v in o.matrix_world.translation],
        "size": [round(v,1) for v in sz],
        "maxdim": round(max(sz),1),
    })

# camera original
cam = sc.camera
cam_info = None
if cam:
    cam_info = {
        "name": cam.name,
        "loc": [round(v,2) for v in cam.location],
        "rot_deg": [round(__import__("math").degrees(v),1) for v in cam.rotation_euler],
        "lens": round(cam.data.lens,1),
    }

print("[insp] === CAMERA ORIGINAL ===")
print("[insp]", json.dumps(cam_info))
print("[insp] === OBJETOS (por maxdim, maiores primeiro) ===")
for o in sorted(objs, key=lambda x: -x["maxdim"])[:60]:
    print("[insp]", f'{o["type"]:6} maxdim={o["maxdim"]:8} loc={o["loc"]} | {o["name"]}')
