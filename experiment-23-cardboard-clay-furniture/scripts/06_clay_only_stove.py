"""SO MASSINHA no fogao — malha original, sem papelao nenhum.

Aplica o material Clay 4.Doh (mesmo asset do exp3/claydoh) com varios presets
de parametro, e renderiza varios angulos de cada preset. Objetivo: sentir se
da a sensacao real de massinha.

Material: 'Clay Doh' (node 'Clay 4.Doh Node') do pack Clay Doh 4.0.4 — exatamente
o que ja usamos em experimentos anteriores. Nada inventado.

Uso: blender --background --factory-startup --python 06_clay_only_stove.py -- [samples] [res]
"""
import bpy, sys, os, math, mathutils

argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
SAMPLES = int(argv[0]) if len(argv) > 0 else 140
RES = int(argv[1]) if len(argv) > 1 else 1300

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib_furniture as L

OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
RDIR = os.path.join(OUT, "clay_stove")
os.makedirs(RDIR, exist_ok=True)

STOVE = r"C:\Users\manu\blenderkit_data\models\old-rusty-stove_d0b8ec34-c43c-4df5-9c81-0b644dcf6286\old-rusty-stove_0_5K_ebe04362-f109-4921-a28a-8af0c65a766a.blend"
CLAY_BLEND = L.CLAY_BLEND
CLAY_MAT = "Clay Doh"   # node 'Clay 4.Doh Node' — material rico do pack

def log(m): print(f"[CLAY] {m}", flush=True)

# ----- presets de massinha (variando bastante os parametros) -----
# cores de massa de modelar vivas
# displacement/texture calibrados pra "massa de modelar" reconhecivel (sem ruido de alta freq).
# tscale ALTO = relevo grande e macio; g_disp moderado pra nao derreter a forma.
PRESETS = [
    {"slug": "p1_macia_rosa", "label": "Macia (rosa) — relevo macio, dedadas suaves, SSS",
     "color": (0.92, 0.42, 0.45), "g_disp": 0.18, "g_bump": 0.5, "tscale": 22.0,
     "voronoi": 0.6, "fingers": 0.5, "cracks": 0.1, "stones": 0.0,
     "rough": 0.42, "sss": 0.4, "finger_dents": 0.3},
    {"slug": "p2_amassada_amarela", "label": "Amassada a mao (amarela) — dedadas marcadas",
     "color": (0.96, 0.78, 0.22), "g_disp": 0.26, "g_bump": 0.7, "tscale": 16.0,
     "voronoi": 1.0, "fingers": 1.2, "cracks": 0.3, "stones": 0.0,
     "rough": 0.5, "sss": 0.28, "finger_dents": 0.5},
    {"slug": "p3_lisa_azul", "label": "Lisa nova (azul) — quase sem relevo, brilho de massa",
     "color": (0.32, 0.58, 0.85), "g_disp": 0.08, "g_bump": 0.3, "tscale": 26.0,
     "voronoi": 0.35, "fingers": 0.25, "cracks": 0.0, "stones": 0.0,
     "rough": 0.3, "sss": 0.5, "finger_dents": 0.15},
    {"slug": "p4_seca_verde", "label": "Seca/rachada (verde) — cracks visiveis, textura terrosa",
     "color": (0.5, 0.66, 0.36), "g_disp": 0.2, "g_bump": 0.6, "tscale": 18.0,
     "voronoi": 0.7, "fingers": 0.4, "cracks": 1.2, "stones": 0.6,
     "rough": 0.6, "sss": 0.12, "finger_dents": 0.35},
]

def set_in(mat, name, val):
    for n in mat.node_tree.nodes:
        if n.type == 'GROUP':
            for s in n.inputs:
                if s.name == name:
                    try:
                        s.default_value = val
                        return True
                    except Exception as e:
                        log(f"   set {name!r} fail: {e}")
                        return False
    return False


def make_clay_mat(p):
    """Cria material Clay Doh fresh por preset, configura parametros."""
    with bpy.data.libraries.load(CLAY_BLEND, link=False) as (df, dt):
        dt.materials = [CLAY_MAT]
    base = bpy.data.materials[CLAY_MAT]
    mat = base.copy()
    mat.name = f"Clay_{p['slug']}"
    mat.displacement_method = 'BOTH'
    c = p["color"]
    set_in(mat, "Clay Color", (*c, 1.0))
    set_in(mat, "Global Displacement", p["g_disp"])
    set_in(mat, "Global Bump", p["g_bump"])
    set_in(mat, "Global Texture Scale", p["tscale"])
    set_in(mat, "Roughness", p["rough"])
    set_in(mat, "Voronoi Factor", p["voronoi"])
    set_in(mat, "Fingerprints Factor", p["fingers"])
    set_in(mat, "Finger Dents (Displacement)", p["finger_dents"])
    set_in(mat, "Cracks Factor", p["cracks"])
    set_in(mat, "Stones Factor", p["stones"])
    # SSS pra dar sensacao de massa translucida (plastilina)
    set_in(mat, "SSS Color", (*[min(1.0, x*1.15) for x in c], 1.0))
    set_in(mat, "SSS Strength !", p["sss"])
    set_in(mat, "SSS Depth", 0.4)
    set_in(mat, "Random Per Object: No | Yes", 1.0)
    return mat


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_world_lights():
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.66, 0.74, 1)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = w
    sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.2; sun_d.angle = math.radians(4)
    sun = bpy.data.objects.new("Sun", sun_d); bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(40))
    a_d = bpy.data.lights.new("Fill", 'AREA'); a_d.energy = 220; a_d.size = 4
    a = bpy.data.objects.new("Fill", a_d); bpy.context.collection.objects.link(a)
    a.location = (-3, -3, 3.2); a.rotation_euler = (math.radians(55), 0, math.radians(-40))
    # chao
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
    pl = bpy.context.active_object; pl.name = "Floor"
    pm = bpy.data.materials.new("FloorMat"); pm.use_nodes = True
    b = pm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.22,0.22,0.25,1)
    b.inputs["Roughness"].default_value = 0.9
    pl.data.materials.append(pm)


def make_cam(name, loc, look, lens=55):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cam = bpy.data.objects.new(name, cd); bpy.context.collection.objects.link(cam)
    cam.location = loc
    d = mathutils.Vector(look) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return cam


def angles_for(obj):
    """Calcula bbox do obj e retorna lista de (nome, loc, look, lens)."""
    bpy.context.view_layer.update()
    cs = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    mn = mathutils.Vector((min(c[i] for c in cs) for i in range(3)))
    mx = mathutils.Vector((max(c[i] for c in cs) for i in range(3)))
    ctr = (mn+mx)/2; sz = mx-mn
    r = max(sz.x, sz.y, sz.z)
    D = r * 2.4   # bem afastado pra enquadrar o objeto inteiro com folga
    cx, cy, cz = ctr
    look = (cx, cy, cz)
    return [
        ("frente",   (cx, cy - D, cz + sz.z*0.25), look, 50),
        ("tresq_E",  (cx - D*0.85, cy - D*0.85, cz + sz.z*0.55), look, 50),
        ("tresq_D",  (cx + D*0.85, cy - D*0.85, cz + sz.z*0.55), look, 50),
        ("lateral",  (cx + D, cy - D*0.15, cz + sz.z*0.25), look, 50),
        ("topo",     (cx, cy - D*0.3, cz + D*1.5), look, 50),
        # macro: enquadra so a parte de cima (queimadores) mais de perto, mas sem entrar no objeto
        ("macro",    (cx - D*0.55, cy - D*0.7, cz + sz.z*0.85),
                     (cx, cy, cz + sz.z*0.35), 70),
    ]


# ----------- run -----------
manifest = []
for p in PRESETS:
    log(f"=== preset {p['slug']} ===")
    clear_scene()
    obj = L.import_furniture(STOVE, f"stove_{p['slug']}")
    L.normalize(obj, target_height=0.95)
    # SO massinha na malha original
    mat = make_clay_mat(p)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    L.ensure_uv(obj)
    msub = obj.modifiers.new("ClaySubsurf", 'SUBSURF')
    msub.subdivision_type = 'CATMULL_CLARK'
    msub.levels = 2
    msub.render_levels = 4
    try: msub.use_adaptive_subdivision = True
    except Exception as e: log(f"   adaptive fail: {e}")

    setup_world_lights()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try: sc.cycles.device = 'GPU'
    except: pass
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.dicing_rate = 1.0
    sc.render.resolution_x = RES
    sc.render.resolution_y = int(RES*0.72)
    sc.render.image_settings.file_format = 'PNG'

    for aname, loc, look, lens in angles_for(obj):
        cam = make_cam(f"Cam_{aname}", loc, look, lens)
        sc.camera = cam
        fn = f"{p['slug']}__{aname}.png"
        sc.render.filepath = os.path.join(RDIR, fn)
        log(f"   render {fn}")
        bpy.ops.render.render(write_still=True)
        manifest.append({"preset": p["slug"], "label": p["label"], "angle": aname, "file": fn})

import json
with open(os.path.join(RDIR, "manifest.json"), "w") as fp:
    json.dump(manifest, fp, indent=2)
log(f"=== DONE: {len(manifest)} renders ({len(PRESETS)} presets x 6 angulos) ===")
