"""Exporta as casas estruturais (08) como GLB navegavel.

Mesma estrategia do 07_export_glb: aplica os booleans nas paredes (furos viram
geometria real), remove os cages cutters, e exporta paredes + teto + piso.
A casa longa cortada e a com teto sao as mais interessantes pra navegar em 1a pessoa.
"""
import bpy, sys, os
sys.path.append(os.path.dirname(__file__))
import hb_lib
import importlib
importlib.reload(hb_lib)

import importlib.util
spec = importlib.util.spec_from_file_location(
    "st", os.path.join(os.path.dirname(__file__), "08_structural.py"))
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
GLB = os.path.join(OUT, "glb")
os.makedirs(GLB, exist_ok=True)


def apply_booleans_and_clean():
    walls = [o for o in bpy.data.objects if 'IS_WALL_BP' in o]
    cages = [o for o in bpy.data.objects
             if o.get('IS_ENTRY_DOOR_BP') or o.get('IS_WINDOW_BP')]
    for w in walls:
        bpy.ops.object.select_all(action='DESELECT')
        w.select_set(True)
        bpy.context.view_layer.objects.active = w
        bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    for c in cages:
        c.select_set(True)
    if cages:
        bpy.ops.object.delete()


def export_house(key, fn):
    hb_lib.reset_scene()
    fn()
    apply_booleans_and_clean()
    bpy.ops.object.select_all(action='SELECT')
    path = os.path.join(GLB, f"{key}.glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB',
        use_selection=True, export_apply=True, export_yup=True)
    nv = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    sz = os.path.getsize(path)
    print(f"[{key}] GLB -> {path}  ({nv} verts, {sz//1024} KB)")


def main():
    only = None
    if "--house" in sys.argv:
        only = sys.argv[sys.argv.index("--house") + 1]
    for key, fn in st.HOUSES.items():
        if only and key != only:
            continue
        print(f"\n##### EXPORT {key} #####")
        export_house(key, fn)


if __name__ == "__main__":
    main()
