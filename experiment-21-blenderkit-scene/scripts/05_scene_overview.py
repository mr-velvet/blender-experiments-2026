"""
05_scene_overview.py — prints "tecnicos" de COMO a cena esta montada (Workbench, rapido).

A cena tem set-dressing gigante (clouds/mist/Landscape, raio 700+) que envolve tudo
como uma casca -> camera de overview ficava DENTRO dela (frame preto). Solucao:
esconder esses meshes-casca no render e enquadrar a parte construida (casa+arvore+terreno).

Saidas:
  - scene_solid_diag.png  : diagonal solid colorido por objeto (mostra os 55 objetos)
  - scene_top_ortho.png   : top ortografico (planta do layout)
  - scene_wireframe.png   : wireframe diagonal (mostra geometria/curvas da hera)

Roda via: blender --background <blend> --python 05_scene_overview.py -- <out_dir> <res>
"""
import bpy
import sys
import os
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:]
OUT = argv[0]
RES = int(argv[1]) if len(argv) > 1 else 1280
os.makedirs(OUT, exist_ok=True)


def log(*a):
    print("[ovw]", *a, flush=True)


sc = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        sc = s
        break
sc = sc or bpy.context.scene
bpy.context.window.scene = sc

# esconde os meshes-casca gigantes (sky/atmosfera/montanhas de fundo) no render
HIDE_PREFIXES = ("clouds", "mist", "Landscape")
hidden = []
for o in sc.objects:
    if any(o.name.startswith(p) for p in HIDE_PREFIXES):
        o.hide_render = True
        hidden.append(o.name)
log("hidden (set-dressing):", hidden)

# bbox do que SOBROU (casa + arvore + terreno proximo + vegetacao)
mins = Vector((1e9,)*3)
maxs = Vector((-1e9,)*3)
visible = [o for o in sc.objects if o.type in ("MESH", "CURVE") and not o.hide_render]
for o in visible:
    try:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], w[i])
                maxs[i] = max(maxs[i], w[i])
    except Exception:
        pass
center = (mins + maxs) * 0.5
size = maxs - mins
radius = max(size.x, size.y, size.z)
log("visible objs:", len(visible), "center", tuple(round(v,1) for v in center),
    "radius", round(radius,1))

sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x = RES
sc.render.resolution_y = int(RES * 9 / 16)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.film_transparent = True  # fundo transparente -> ve so a geometria
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_object_outline = True
sh.show_shadows = False


def make_cam(name, location, look_at, lens=50, ortho=False, ortho_scale=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    if ortho:
        cd.type = "ORTHO"
        if ortho_scale:
            cd.ortho_scale = ortho_scale
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    d = Vector(look_at) - Vector(location)
    cam.location = location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam


def render_to(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log("  ->", os.path.basename(path), os.path.getsize(path) if os.path.exists(path) else "FAIL")


d = radius * 2.2
# diagonal solid
c1 = make_cam("OVW_diag", Vector((center.x + d*0.7, center.y - d*0.7, center.z + d*0.6)), center, lens=50)
sc.camera = c1
render_to(os.path.join(OUT, "scene_solid_diag.png"))

# top ortho (planta)
c2 = make_cam("OVW_top", Vector((center.x, center.y, maxs.z + radius*2)), center,
              ortho=True, ortho_scale=radius*1.25)
sc.camera = c2
render_to(os.path.join(OUT, "scene_top_ortho.png"))

# wireframe diagonal
for o in sc.objects:
    if o.type in ("MESH", "CURVE"):
        o.display_type = 'WIRE'
        o.show_wire = True
c3 = make_cam("OVW_wire", Vector((center.x + d*0.7, center.y - d*0.7, center.z + d*0.5)), center, lens=50)
sc.camera = c3
render_to(os.path.join(OUT, "scene_wireframe.png"))

log("DONE")
