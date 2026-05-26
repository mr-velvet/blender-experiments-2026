"""01: inspeciona a estrutura de um VDM Face Brush asset no Blender 4.3.

Objetivo: entender exatamente o que precisa ser configurado pra aplicar o brush
de verdade no modo Sculpt — texture, displacement mode, stroke method, etc.
Tambem testa se da pra acessar a API de sculpt headless.
"""
import bpy
import sys

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"


def inspect_asset_blend(path):
    print(f"\n==== {path} ====")
    with bpy.data.libraries.load(path, link=False, assets_only=False) as (df, dt):
        print("  brushes:", list(df.brushes))
        print("  textures:", list(df.textures))
        print("  images:", list(df.images))
        dt.brushes = list(df.brushes)
        dt.textures = list(df.textures)
        dt.images = list(df.images)
    for b in dt.brushes:
        if b is None:
            continue
        print(f"  >> brush {b.name!r}")
        print(f"     sculpt_tool   = {getattr(b, 'sculpt_tool', '?')}")
        print(f"     stroke_method = {b.stroke_method}")
        print(f"     use_color_as_displacement = {getattr(b, 'use_color_as_displacement', '?')}")
        print(f"     strength      = {b.strength}")
        print(f"     texture       = {b.texture}")
        if b.texture:
            tex = b.texture
            print(f"        tex.type  = {tex.type}")
            if hasattr(tex, 'image') and tex.image:
                print(f"        tex.image = {tex.image.name} {tuple(tex.image.size)} src={tex.image.source}")
        ts = b.texture_slot
        print(f"     texture_slot.map_mode = {ts.map_mode}")
        print(f"     is_asset = {b.asset_data is not None}")


def main():
    import os
    files = sorted([f for f in os.listdir(BRUSH_DIR) if f.endswith(".asset.blend")])
    print(f"total asset.blend: {len(files)}")
    # inspeciona so os 3 primeiros pra entender a estrutura
    for f in files[:3]:
        inspect_asset_blend(os.path.join(BRUSH_DIR, f))

    # testa API de sculpt
    print("\n==== API sculpt check ====")
    print("  bpy.ops.sculpt.brush_stroke:", hasattr(bpy.ops.sculpt, "brush_stroke"))
    print("  bpy.app.version:", bpy.app.version)


main()
