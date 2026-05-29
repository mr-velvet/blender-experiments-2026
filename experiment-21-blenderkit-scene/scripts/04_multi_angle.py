"""
04_multi_angle.py — abre a scene appendada e renderiza varios angulos:
  - N cameras orbitando o ponto de interesse (a cabana), azimutes diferentes
  - overviews "tecnicos" mostrando o layout completo da cena (diagonal amplo + top)

Cada camera nova e criada por codigo apontando pro alvo (track-to), provando
controle programatico de camera. Nao usa a camera original do asset (pra dar
angulos novos), mas mantem o world/luz do asset.

Roda via:
  blender --background <blend> --python 04_multi_angle.py -- <out_dir> <engine> <samples> <res>
"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:]
OUT = argv[0]
ENGINE = argv[1] if len(argv) > 1 else "CYCLES"
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
RES = int(argv[3]) if len(argv) > 3 else 1280
os.makedirs(OUT, exist_ok=True)


def log(*a):
    print("[multi]", *a, flush=True)


# --- pega a scene do asset ---
sc = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        sc = s
        break
if sc is None:
    sc = bpy.context.scene
bpy.context.window.scene = sc
log("scene:", sc.name, "objects:", len(sc.objects))

# A CASA sao os Cube.* (loc ~2,26,0). A Tree (27u) e o backdrop "Plane" inflam o
# enquadramento -> calcular o centro SO com os Cubes da casa (e Icosphere/hera).
HOUSE_PREFIXES = ("Cube", "Icosphere", "IvyLeaf")
mins = Vector((1e9, 1e9, 1e9))
maxs = Vector((-1e9, -1e9, -1e9))
house_objs = [o for o in sc.objects if o.type == "MESH"
              and any(o.name.startswith(p) for p in HOUSE_PREFIXES)]
for o in house_objs:
    for corner in o.bound_box:
        wc = o.matrix_world @ Vector(corner)
        for i in range(3):
            mins[i] = min(mins[i], wc[i])
            maxs[i] = max(maxs[i], wc[i])
center = (mins + maxs) * 0.5
size = maxs - mins
radius = max(size.x, size.y)  # raio horizontal da casa (ignora altura/arvore)
log("HOUSE (cubes) objs:", len(house_objs))
log("house center:", tuple(round(v, 2) for v in center))
log("house size:", tuple(round(v, 2) for v in size), "radius:", round(radius, 2))

# alvo: meio da casa, um pouco acima do meio (mira no corpo da cabana, nao na copa)
focus = center.copy()
focus.z = center.z + size.z * 0.1

# --- engine setup ---
sc.render.engine = ENGINE
if ENGINE == "CYCLES":
    sc.cycles.samples = SAMPLES
    try:
        cp = bpy.context.preferences.addons["cycles"].preferences
        cp.get_devices()
        for dt in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                cp.compute_device_type = dt
                break
            except Exception:
                continue
        for d in cp.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        log("gpu skip:", e)
else:
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass

sc.render.resolution_x = RES
sc.render.resolution_y = int(RES * 9 / 16)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"


def make_cam(name, location, look_at, lens=40):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam = bpy.data.objects.new(name, cam_data)
    sc.collection.objects.link(cam)
    # aim: aponta -Z pra look_at
    direction = (Vector(look_at) - Vector(location))
    rot = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.location = location
    cam.rotation_euler = rot
    return cam


def render_to(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    ok = os.path.exists(path)
    log("  ->", os.path.basename(path), "ok" if ok else "FAIL",
        os.path.getsize(path) if ok else "")


# --- angulos orbitando a casa ---
# casa tem ~9u de raio horizontal; cameras a ~4-5x isso, alturas acima do solo
# pra evitar o backdrop "Plane" que aparece quando se olha de baixo pro horizonte
base_z = center.z  # ~meio da casa
# (nome, azimute graus, altura ABSOLUTA acima do centro em unidades, lente)
angles = [
    ("a1_three_quarter", 215, 6,  50),   # 3/4 frontal, leve plonge
    ("a2_side_right",     300, 9,  55),   # lateral direita de cima
    ("a3_back",            40, 12, 45),   # por tras, alto (mostra telhado)
    ("a4_eye_level",      170, 3,  60),   # altura do olhar, lente longa
    ("a5_left",           120, 7,  55),   # esquerda
]
dist = radius * 4.5
for name, az_deg, height_abs, lens in angles:
    az = math.radians(az_deg)
    loc = Vector((
        center.x + dist * math.cos(az),
        center.y + dist * math.sin(az),
        base_z + height_abs,
    ))
    cam = make_cam("CAM_" + name, loc, focus, lens=lens)
    sc.camera = cam
    log(f"angle {name}: az={az_deg} h={height_abs} lens={lens} loc={tuple(round(v,1) for v in loc)}")
    render_to(os.path.join(OUT, f"angle_{name}.png"))

log("DONE")
