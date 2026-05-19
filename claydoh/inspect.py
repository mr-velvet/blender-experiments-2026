"""Inspeciona o .blend do Clay Doh: lista materiais, node groups, objetos, asset marks.

Rodar:
    & "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" \
      --background "C:/Users/manu/Downloads/BLENDER-CLAY/Clay Doh 4.0.4 (Blender 4.4+)/Clay Doh 4.0.4 (Blender 4.4+).blend" \
      --python claydoh/inspect.py
"""
import bpy
import json
import sys
from pathlib import Path

OUT = Path(r"C:/Users/manu/ved/blender-experiments-2026/claydoh/blend_inventory.json")

def material_summary(mat):
    info = {
        "name": mat.name,
        "use_nodes": mat.use_nodes,
        "asset": bool(mat.asset_data),
        "users": mat.users,
    }
    if mat.asset_data:
        info["catalog"] = str(mat.asset_data.catalog_id)
        info["asset_tags"] = [t.name for t in mat.asset_data.tags]
    if mat.use_nodes and mat.node_tree:
        out = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out and out.inputs['Surface'].is_linked:
            src = out.inputs['Surface'].links[0].from_node
            info["surface_source_type"] = src.type
            info["surface_source_name"] = src.name
            if src.type == 'GROUP':
                info["group_node_tree"] = src.node_tree.name if src.node_tree else None
        if out and out.inputs['Displacement'].is_linked:
            info["uses_displacement"] = True
        # contar tipos de node
        types = {}
        for n in mat.node_tree.nodes:
            types[n.type] = types.get(n.type, 0) + 1
        info["node_types"] = types
    return info

inventory = {
    "blend_file": bpy.data.filepath,
    "materials_total": len(bpy.data.materials),
    "objects_total": len(bpy.data.objects),
    "node_groups_total": len(bpy.data.node_groups),
    "images_total": len(bpy.data.images),
    "materials": [material_summary(m) for m in bpy.data.materials],
    "objects": [
        {
            "name": o.name,
            "type": o.type,
            "asset": bool(o.asset_data),
            "materials": [s.material.name for s in o.material_slots if s.material],
        }
        for o in bpy.data.objects
    ],
    "node_groups": [
        {
            "name": ng.name,
            "type": ng.bl_idname,
            "asset": bool(ng.asset_data),
            "users": ng.users,
        }
        for ng in bpy.data.node_groups
    ],
    "images": [
        {"name": img.name, "filepath": img.filepath, "size": list(img.size)}
        for img in bpy.data.images
    ],
}

OUT.write_text(json.dumps(inventory, indent=2))
print(f"[inspect] inventario salvo em {OUT}")
print(f"  materiais: {inventory['materials_total']}")
print(f"  objetos: {inventory['objects_total']}")
print(f"  node groups: {inventory['node_groups_total']}")
print(f"  imagens: {inventory['images_total']}")
