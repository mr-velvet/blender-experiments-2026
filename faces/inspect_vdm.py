"""Inspeciona o pack VDM Faces: listar brushes asset, ver mapeamento de EXRs."""
import bpy
import json
from pathlib import Path

OUT = Path(r"C:/Users/manu/ved/blender-experiments-2026/faces/vdm_inventory.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def brush_summary(b):
    info = {
        "name": b.name,
        "asset": bool(b.asset_data),
        "users": b.users,
    }
    if b.asset_data:
        info["catalog"] = str(b.asset_data.catalog_id)
        info["asset_tags"] = [t.name for t in b.asset_data.tags]
    # tentar pegar atributos sculpt
    if hasattr(b, "sculpt_tool"):
        info["sculpt_tool"] = b.sculpt_tool
    if hasattr(b, "stroke_method"):
        info["stroke_method"] = b.stroke_method
    if hasattr(b, "use_color_as_displacement"):
        info["use_color_as_displacement"] = b.use_color_as_displacement
    # texture associada (provavel campo do brush VDM)
    if hasattr(b, "texture") and b.texture:
        info["texture"] = b.texture.name
    if hasattr(b, "mask_texture") and b.mask_texture:
        info["mask_texture"] = b.mask_texture.name
    return info


inventory = {
    "blend_file": bpy.data.filepath,
    "brushes_total": len(bpy.data.brushes),
    "textures_total": len(bpy.data.textures),
    "images_total": len(bpy.data.images),
    "brushes": [brush_summary(b) for b in bpy.data.brushes],
    "textures": [
        {"name": t.name, "type": t.type, "asset": bool(t.asset_data)}
        for t in bpy.data.textures
    ],
    "images": [
        {"name": img.name, "filepath": img.filepath, "size": list(img.size),
         "file_format": img.file_format, "is_float": img.is_float,
         "colorspace": img.colorspace_settings.name}
        for img in bpy.data.images
    ],
}

OUT.write_text(json.dumps(inventory, indent=2))
print(f"[inspect-vdm] inventario salvo em {OUT}")
print(f"  brushes: {inventory['brushes_total']}")
print(f"  textures: {inventory['textures_total']}")
print(f"  images: {inventory['images_total']}")
