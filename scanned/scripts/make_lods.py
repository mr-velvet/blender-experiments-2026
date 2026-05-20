"""Generate LODs of the scanned GLB.
Outputs:
- lod0.glb (original, just re-exported)
- lod1.glb (50% decimate)
- lod2.glb (25%)
- lod3.glb (12.5%)
- lod_tex512.glb (LOD1 with texture downsized to 512)
Center mesh at origin, sit on Y=0 (so instancing places them on the floor).
"""
import bpy
import sys
import os
import json
import mathutils

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
src = argv[0]
out_dir = argv[1]
os.makedirs(out_dir, exist_ok=True)


def reset_and_import():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    return [o for o in bpy.data.objects if o.type == "MESH"]


def center_and_floor(objs):
    minv = [float("inf")] * 3
    maxv = [-float("inf")] * 3
    for obj in objs:
        for v in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(v)
            for i in range(3):
                minv[i] = min(minv[i], world[i])
                maxv[i] = max(maxv[i], world[i])
    cx = (minv[0] + maxv[0]) / 2
    cy = minv[1]  # sit on floor
    cz = (minv[2] + maxv[2]) / 2
    for obj in objs:
        obj.location.x -= cx
        obj.location.y -= cy
        obj.location.z -= cz
    return {"size": [maxv[i] - minv[i] for i in range(3)]}


def apply_decimate(objs, ratio):
    for obj in objs:
        if obj.type != "MESH":
            continue
        m = obj.modifiers.new("Decimate", "DECIMATE")
        m.ratio = ratio
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=m.name)


def downsize_textures(target):
    for img in bpy.data.images:
        if img.size[0] > target or img.size[1] > target:
            img.scale(target, target)


def export(path):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_apply=True,
        export_image_format="AUTO",
    )


def mesh_stats(objs):
    tris = 0
    verts = 0
    for obj in objs:
        if obj.type != "MESH":
            continue
        me = obj.data
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        verts += len(me.vertices)
    return {"tris": tris, "verts": verts}


report = {"src": src, "lods": []}

# LOD0 — original, just re-export to normalize and center
objs = reset_and_import()
size = center_and_floor(objs)
stats = mesh_stats(objs)
path = os.path.join(out_dir, "lod0.glb")
export(path)
report["lods"].append({"name": "lod0", "ratio": 1.0, "path": path, "size_bytes": os.path.getsize(path), **stats, "world_size": size["size"]})

# LOD1/2/3 — decimate
for name, ratio in [("lod1", 0.5), ("lod2", 0.25), ("lod3", 0.125)]:
    objs = reset_and_import()
    center_and_floor(objs)
    apply_decimate(objs, ratio)
    stats = mesh_stats(objs)
    path = os.path.join(out_dir, f"{name}.glb")
    export(path)
    report["lods"].append({"name": name, "ratio": ratio, "path": path, "size_bytes": os.path.getsize(path), **stats})

# LOD with downsized texture (for instancing many copies)
objs = reset_and_import()
center_and_floor(objs)
apply_decimate(objs, 0.5)
downsize_textures(512)
stats = mesh_stats(objs)
path = os.path.join(out_dir, "lod_tex512.glb")
export(path)
report["lods"].append({"name": "lod_tex512", "ratio": 0.5, "path": path, "size_bytes": os.path.getsize(path), **stats, "texture": "512x512"})

# Even lighter for max stress: LOD2 + 256 texture
objs = reset_and_import()
center_and_floor(objs)
apply_decimate(objs, 0.25)
downsize_textures(256)
stats = mesh_stats(objs)
path = os.path.join(out_dir, "lod_tiny.glb")
export(path)
report["lods"].append({"name": "lod_tiny", "ratio": 0.25, "path": path, "size_bytes": os.path.getsize(path), **stats, "texture": "256x256"})

with open(os.path.join(out_dir, "lods.json"), "w") as f:
    json.dump(report, f, indent=2)

for lod in report["lods"]:
    print(f"[lod] {lod['name']}: {lod['tris']} tris, {lod['size_bytes']/1024:.1f} KB")
