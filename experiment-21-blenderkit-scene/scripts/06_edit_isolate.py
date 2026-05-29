"""
06_edit_isolate.py — EDICAO 3D destrutiva da scene "The Lonely Outpost".

Mantem a casa, remove o campo gramado em volta, poe um plano liso.
Dois modos (o user autorizou mais de um experimento):

  MODE=A  (isolar total): remove campo (Plane + GS*) E fundo (Landscape*/clouds/mist).
          Casa sozinha num plano liso, ceu/world neutro limpo.
  MODE=B  (trocar so o chao): remove so o campo gramado (Plane + GS*), mantem as
          montanhas/ceu/world original ao fundo. Casa num plano liso dentro do vale.

Classificacao de objetos (descoberta via inspect_scene.py):
  CASA   = Cube* , Icosphere , IvyLeaf* , IVY_Curve* , Tree , Empty*  (+ Spot luz, Camera)
  CAMPO  = Plane , GS *        (terreno esculpido + scatter de grama)
  FUNDO  = Landscape* , clouds , mist

Roda via:
  blender --background <blend_in> --python 06_edit_isolate.py -- <mode A|B> <out_blend>
"""
import bpy
import sys
import os
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:]
MODE = argv[0].upper()
OUT_BLEND = argv[1]
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)


def log(*a):
    print("[edit]", *a, flush=True)


sc = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        sc = s
        break
sc = sc or bpy.context.scene
bpy.context.window.scene = sc
log("MODE:", MODE, "| scene:", sc.name, "| objs before:", len(sc.objects))

# --- classificacao ---
CAMPO_EXACT = {"Plane"}
def is_campo(n):
    return n in CAMPO_EXACT or n.startswith("GS ") or n.startswith("GS_")
def is_fundo(n):
    return n.startswith("Landscape") or n.startswith("clouds") or n.startswith("mist")

# o que deletar conforme o modo
to_delete = []
for o in list(sc.objects):
    n = o.name
    if is_campo(n):
        to_delete.append(o)
    elif MODE == "A" and is_fundo(n):
        to_delete.append(o)

log("deleting", len(to_delete), "objs:",
    sorted(set(o.name.split('.')[0] for o in to_delete)))

# --- bbox da CASA (Cube*) ANTES de deletar, pra dimensionar e posicionar o plano ---
house = [o for o in sc.objects if o.type == "MESH" and (
    o.name.startswith("Cube") or o.name.startswith("Icosphere") or o.name.startswith("IvyLeaf"))]
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in house:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
hc = (mn + mx) * 0.5
hsize = mx - mn
base_z = mn.z  # base da casa
log("house center", tuple(round(v,2) for v in hc), "base_z", round(base_z,2),
    "size", tuple(round(v,2) for v in hsize))

# --- deletar via data api (robusto: nao depende de View Layer / selecao;
# objetos-fonte de scatter ficam fora do view layer e quebram select_set) ---
for o in to_delete:
    try:
        bpy.data.objects.remove(o, do_unlink=True)
    except Exception as e:
        log("  warn removing", o.name, ":", e)
log("objs after delete:", len(sc.objects))

# --- criar plano liso na base da casa ---
plane_size = max(hsize.x, hsize.y) * 4.0  # bem maior que a casa, pra ela assentar
bpy.ops.mesh.primitive_plane_add(size=plane_size, location=(hc.x, hc.y, base_z))
plane = bpy.context.active_object
plane.name = "FlatGround"
# material liso neutro (terra clara / concreto suave)
mat = bpy.data.materials.new("FlatGround_Mat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.62, 0.58, 0.52, 1.0)  # terra clara
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 0.85
plane.data.materials.append(mat)
log("flat plane:", plane.name, "size", round(plane_size,1), "at z", round(base_z,2))

# --- world conforme o modo ---
if MODE == "A":
    # ceu limpo neutro: world cinza-azulado uniforme (sem o set-dressing)
    w = bpy.data.worlds.new("CleanSky") if "CleanSky" not in bpy.data.worlds else bpy.data.worlds["CleanSky"]
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1.0)  # ceu claro
        bg.inputs["Strength"].default_value = 1.0
    sc.world = w
    log("world -> CleanSky (neutro)")
else:
    log("world -> mantido (original do asset)")

# garante uma luz: se Spot foi mantido, ok; senao adiciona sol
has_light = any(o.type == "LIGHT" for o in sc.objects)
if not has_light:
    bpy.ops.object.light_add(type='SUN', location=(hc.x+10, hc.y-10, base_z+20))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    log("added SUN (no light remained)")
else:
    log("light kept:", [o.name for o in sc.objects if o.type=='LIGHT'])

# salva
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log("saved:", OUT_BLEND)
log("DONE")
