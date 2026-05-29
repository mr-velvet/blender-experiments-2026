"""Renderiza a cena de varios angulos via cameras criadas por codigo.

Cameras orbitam o conjunto dos 8 moveis, enquadrando automaticamente pelo bbox.
Angulos: frente, 3/4 esquerda, 3/4 direita, lateral, top-down (planta), close papelao, close massinha.

Uso: blender --background --factory-startup --python 05_render_angles.py -- [samples] [res]
"""
import bpy, sys, os, math, mathutils

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SAMPLES = int(argv[0]) if len(argv) > 0 else 128
RES = int(argv[1]) if len(argv) > 1 else 1600

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
SCENE = os.path.join(OUT, "scene_furniture.blend")
RENDER_DIR = os.path.join(OUT, "renders")
os.makedirs(RENDER_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SCENE)
sc = bpy.context.scene

def log(m): print(f"[RENDER] {m}", flush=True)

# bbox global de todos os moveis (exclui Floor/luzes/cameras)
mins = mathutils.Vector((1e9,)*3); maxs = mathutils.Vector((-1e9,)*3)
furn = [o for o in sc.objects if o.type == 'MESH' and o.name != 'Floor']
for o in furn:
    for c in o.bound_box:
        wc = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mins[i] = min(mins[i], wc[i]); maxs[i] = max(maxs[i], wc[i])
center = (mins + maxs) / 2.0
size = maxs - mins
radius = max(size.x, size.y, size.z)
log(f"bbox center={[round(x,2) for x in center]} size={[round(x,2) for x in size]} radius={radius:.2f}")

def make_cam(name, loc, look_at, lens=50, ortho=False, ortho_scale=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    if ortho:
        cd.type = 'ORTHO'
        if ortho_scale: cd.ortho_scale = ortho_scale
    cam = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    direction = mathutils.Vector(look_at) - mathutils.Vector(loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return cam

D = radius * 1.5  # distancia base
cx, cy, cz = center
mid_z = cz

ANGLES = [
    # (nome, loc, look_at, lens, ortho, ortho_scale)
    # frente elevada: ve as DUAS fileiras (massinha na frente, papelao atras)
    ("01_frente_alta",  (cx, cy - D*1.3, mid_z + size.z*1.4), (cx, cy, mid_z), 50, False, None),
    ("02_tresquartos_E",(cx - D*1.0, cy - D*1.2, mid_z + size.z*1.1), (cx, cy, mid_z), 50, False, None),
    ("03_tresquartos_D",(cx + D*1.0, cy - D*1.2, mid_z + size.z*1.1), (cx, cy, mid_z), 50, False, None),
    ("04_lateral",      (cx + D*1.7, cy, mid_z + size.z*0.5), (cx, cy, mid_z), 55, False, None),
    ("05_planta_top",   (cx, cy, cz + D*2.0), (cx, cy, cz), 50, True, max(size.x, size.y)*1.2),
    ("06_olho_baixo",   (cx, cy - D*1.5, mid_z + size.z*0.1), (cx, cy, mid_z+size.z*0.2), 60, False, None),
]

# cycles settings
sc.render.engine = 'CYCLES'
try: sc.cycles.device = 'GPU'
except: pass
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.dicing_rate = 1.0
sc.render.resolution_x = RES
sc.render.resolution_y = int(RES * 0.62)
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = False

for name, loc, look, lens, ortho, oscale in ANGLES:
    cam = make_cam(f"Cam_{name}", loc, look, lens, ortho, oscale)
    sc.camera = cam
    sc.render.filepath = os.path.join(RENDER_DIR, f"{name}.png")
    log(f"render {name} ...")
    bpy.ops.render.render(write_still=True)
    log(f"  -> {name}.png")

log("=== ALL ANGLES RENDERED ===")
