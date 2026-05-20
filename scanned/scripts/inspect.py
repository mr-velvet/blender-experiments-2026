"""Inspect mesh of a scanned GLB: tris, verts, materials, textures, bbox, draw calls."""
import bpy
import json
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
src = argv[0]
out_json = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

stats = {
    "file_path": src,
    "file_size_bytes": os.path.getsize(src),
    "objects": [],
    "totals": {
        "objects": 0,
        "meshes": 0,
        "triangles": 0,
        "vertices": 0,
        "edges": 0,
        "polygons": 0,
        "materials": 0,
        "images": 0,
        "image_bytes": 0,
    },
    "bbox_global": None,
    "materials": [],
    "images": [],
}

minv = [float("inf")] * 3
maxv = [-float("inf")] * 3

for obj in bpy.data.objects:
    info = {"name": obj.name, "type": obj.type}
    if obj.type == "MESH":
        me = obj.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        info.update(
            {
                "vertices": len(me.vertices),
                "edges": len(me.edges),
                "polygons": len(me.polygons),
                "triangles": tris,
                "materials": [s.material.name for s in obj.material_slots if s.material],
                "uv_layers": [u.name for u in me.uv_layers],
                "vertex_colors": [c.name for c in me.color_attributes],
            }
        )
        stats["totals"]["meshes"] += 1
        stats["totals"]["triangles"] += tris
        stats["totals"]["vertices"] += len(me.vertices)
        stats["totals"]["edges"] += len(me.edges)
        stats["totals"]["polygons"] += len(me.polygons)
        # bbox global
        for v in obj.bound_box:
            world = obj.matrix_world @ __import__("mathutils").Vector(v)
            for i in range(3):
                minv[i] = min(minv[i], world[i])
                maxv[i] = max(maxv[i], world[i])
    stats["objects"].append(info)
    stats["totals"]["objects"] += 1

stats["bbox_global"] = {
    "min": minv,
    "max": maxv,
    "size": [maxv[i] - minv[i] for i in range(3)],
}

for mat in bpy.data.materials:
    nodes_info = []
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            entry = {"type": n.type, "name": n.name}
            if n.type == "TEX_IMAGE" and n.image:
                entry["image"] = n.image.name
            nodes_info.append(entry)
    stats["materials"].append({"name": mat.name, "nodes": nodes_info})
stats["totals"]["materials"] = len(bpy.data.materials)

for img in bpy.data.images:
    if not img.name or img.name == "Render Result":
        continue
    px = img.size[0] * img.size[1]
    channels = img.channels or 4
    approx_bytes = px * channels  # uncompressed
    stats["images"].append(
        {
            "name": img.name,
            "size": list(img.size),
            "channels": channels,
            "approx_uncompressed_bytes": approx_bytes,
            "source": img.source,
            "file_format": img.file_format,
            "packed": bool(img.packed_file),
        }
    )
    stats["totals"]["images"] += 1
    stats["totals"]["image_bytes"] += approx_bytes

os.makedirs(os.path.dirname(out_json), exist_ok=True)
with open(out_json, "w") as f:
    json.dump(stats, f, indent=2, default=str)

print(f"[inspect] wrote {out_json}")
print(f"[inspect] tris={stats['totals']['triangles']} verts={stats['totals']['vertices']} mats={stats['totals']['materials']} imgs={stats['totals']['images']}")
