"""Lista node_groups e materials disponiveis nos dois assets de efeito."""
import bpy, sys, json, os

CARDBOARD = r"C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\assets\easy-cardboard-3.1.blend"
CLAY = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"

def peek(path, label):
    print(f"=== {label} ===")
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        ngs = list(df.node_groups)
        mats = list(df.materials)
    print(f"  node_groups ({len(ngs)}):")
    for n in ngs:
        if 'Cardboard' in n or 'Box' in n or 'Smooth' in n or 'Clay' in n:
            print(f"    * {n!r}")
    print(f"  materials ({len(mats)}):")
    for m in mats[:30]:
        print(f"    - {m!r}")

peek(CARDBOARD, "EASY CARDBOARD 3.1")
peek(CLAY, "CLAY DOH 4.0.4")
