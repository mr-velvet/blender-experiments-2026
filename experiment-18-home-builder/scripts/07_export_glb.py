"""Exporta cada casa como GLB navegavel (1a pessoa fora do Blender).

O GLB precisa conter as paredes com os furos JA APLICADOS (boolean evaluated) e
NAO conter os objetos cage (cutters invisiveis). Estrategia:
  1. constroi a casa (hb_lib) -> paredes com modifier boolean + cages parentados
  2. aplica os booleans nas paredes (converte modifier -> geometria real na mesh)
  3. deleta os cages (cutters) e o floor fica opcional
  4. exporta SOMENTE as paredes (+ floor) selecionadas, com use_selection=True

GLB com paredes vazadas reais = navegavel em qualquer engine (three.js, Godot, Unity).
"""
import bpy, sys, os, math
sys.path.append(os.path.dirname(__file__))
import hb_lib
import importlib
importlib.reload(hb_lib)

# reusa as definicoes de casa do build_houses
build = importlib.import_module("03_build_houses") if "03_build_houses" in sys.modules else None
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bh", os.path.join(os.path.dirname(__file__), "03_build_houses.py"))
bh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bh)

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
GLB = os.path.join(OUT, "glb")
os.makedirs(GLB, exist_ok=True)


def apply_booleans_and_clean():
    """Aplica todos os boolean modifiers das paredes e remove os cages cutters."""
    deps = bpy.context.evaluated_depsgraph_get()
    walls = [o for o in bpy.data.objects if 'IS_WALL_BP' in o]
    cages = [o for o in bpy.data.objects
             if o.get('IS_ENTRY_DOOR_BP') or o.get('IS_WINDOW_BP')]

    # aplica os modifiers (boolean + o geo-node da parede) -> mesh real vazada
    for w in walls:
        bpy.context.view_layer.objects.active = w
        # converte o objeto inteiro (todos os modifiers, incl. o GeoNodeWall) em mesh
        bpy.ops.object.select_all(action='DESELECT')
        w.select_set(True)
        bpy.context.view_layer.objects.active = w
        bpy.ops.object.convert(target='MESH')   # aplica geo-nodes + boolean de uma vez

    # remove os cages (cutters) — nao devem ir pro GLB
    bpy.ops.object.select_all(action='DESELECT')
    for c in cages:
        c.select_set(True)
    if cages:
        bpy.ops.object.delete()


def export_house(key, fn):
    hb_lib.reset_scene()
    fn()
    apply_booleans_and_clean()

    # seleciona o que sobrou (paredes vazadas + floor) e exporta
    bpy.ops.object.select_all(action='SELECT')
    path = os.path.join(GLB, f"{key}.glb")
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,          # garante modifiers aplicados
        export_yup=True,            # convencao Y-up (three.js/Godot)
    )
    # stats
    nv = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
    sz = os.path.getsize(path)
    print(f"[{key}] GLB -> {path}  ({nv} verts, {sz//1024} KB)")


def main():
    only = None
    if "--house" in sys.argv:
        only = sys.argv[sys.argv.index("--house") + 1]
    for key, fn in bh.HOUSES.items():
        if only and key != only:
            continue
        print(f"\n##### EXPORT {key} #####")
        export_house(key, fn)


if __name__ == "__main__":
    main()
