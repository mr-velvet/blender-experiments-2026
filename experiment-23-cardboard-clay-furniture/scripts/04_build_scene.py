"""Monta a cena completa: 4 moveis x 2 efeitos = 8 pecas lado a lado.

Layout grid: 4 colunas (1 movel por coluna), 2 fileiras.
  Fileira de tras (Y+) = PAPELAO
  Fileira da frente (Y-) = MASSINHA
Cada peca normalizada por altura coerente; massinha com cor caracteristica por movel.

Salva out/scene_furniture.blend pros scripts de render multi-angulo consumirem.

Uso: blender --background --factory-startup --python 04_build_scene.py
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_furniture as L

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out"))
os.makedirs(OUT, exist_ok=True)

MODELS = r"C:\Users\manu\blenderkit_data\models"
FURNITURE = [
    {"slug": "sofa",  "label": "Sofa",
     "blend": os.path.join(MODELS, r"taipei-sofa_48fa33e0-8cba-4fac-8898-8f9bfa3a2f41\taipei-sofa_0_5K_6a8135a3-36ca-41a2-9057-822a78dce8c7.blend"),
     "height": 0.85, "clay_color": (0.86, 0.34, 0.30), "clay_disp": 0.07, "clay_tscale": 26.0},  # coral
    {"slug": "tv",    "label": "TV CRT",
     "blend": os.path.join(MODELS, r"old-style-crt-tv_896ab0b1-20fc-4ae9-8619-b5b0e9e8b0c4\old-style-crt-tv_0_5K_32a7e8b2-5f37-4d11-ab6b-e11726058f4e.blend"),
     "height": 0.70, "clay_color": (0.30, 0.55, 0.78), "clay_disp": 0.08, "clay_tscale": 22.0},  # azul
    {"slug": "stove", "label": "Fogao",
     "blend": os.path.join(MODELS, r"old-rusty-stove_d0b8ec34-c43c-4df5-9c81-0b644dcf6286\old-rusty-stove_0_5K_ebe04362-f109-4921-a28a-8af0c65a766a.blend"),
     "height": 0.90, "clay_color": (0.95, 0.80, 0.25), "clay_disp": 0.09, "clay_tscale": 20.0},  # amarelo
    {"slug": "sink",  "label": "Pia",
     "blend": os.path.join(MODELS, r"sink_5dd4cadb-67b2-4147-8154-c9af7b91a682\sink_e3459e94-66a3-4ade-8256-0ffba93f42db.blend"),
     "height": 0.90, "clay_color": (0.45, 0.72, 0.45), "clay_disp": 0.05, "clay_tscale": 28.0},  # verde
]

COL_SPACING = 1.9   # distancia entre colunas (X)
ROW_Y = 1.9         # distancia entre fileiras (Y) — separa papelao/massinha pra ver os dois


def log(m): print(f"[BUILD] {m}", flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

n = len(FURNITURE)
x0 = -(n - 1) * COL_SPACING / 2.0

stats = []
for i, f in enumerate(FURNITURE):
    x = x0 + i * COL_SPACING
    log(f"--- {f['label']} (col {i}) ---")

    # PAPELAO (fileira de tras, Y+)
    oc = L.import_furniture(f["blend"], f"{f['slug']}_cardboard")
    L.normalize(oc, target_height=f["height"])
    L.apply_cardboard(oc)
    oc.location.x = x
    oc.location.y = ROW_Y / 2.0
    vc, fc = len(oc.data.vertices), len(oc.data.polygons)

    # MASSINHA (fileira da frente, Y-)
    om = L.import_furniture(f["blend"], f"{f['slug']}_clay")
    L.normalize(om, target_height=f["height"])
    L.apply_clay(om, color=f["clay_color"],
                 displacement=f.get("clay_disp", 0.1),
                 tex_scale=f.get("clay_tscale", 18.0))
    om.location.x = x
    om.location.y = -ROW_Y / 2.0
    vm = len(om.data.vertices)

    stats.append({"slug": f["slug"], "label": f["label"],
                  "cardboard_verts": vc, "cardboard_faces": fc,
                  "clay_verts": vm, "clay_color": f["clay_color"]})
    log(f"  cardboard {vc}v/{fc}f | clay {vm}v(base, +adaptive subdiv no render)")

# chao
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
plane = bpy.context.active_object
plane.name = "Floor"
pm = bpy.data.materials.new("FloorMat"); pm.use_nodes = True
bsdf = pm.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.22, 0.22, 0.25, 1)
bsdf.inputs["Roughness"].default_value = 0.85
plane.data.materials.append(pm)

# world (luz ambiente neutra clara)
w = bpy.data.worlds.new("World"); w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.62, 0.66, 0.74, 1)
bg.inputs[1].default_value = 1.0
bpy.context.scene.world = w

# luz principal (sol) + fill
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.5; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(35))

area_d = bpy.data.lights.new("Fill", 'AREA'); area_d.energy = 300; area_d.size = 6
area = bpy.data.objects.new("Fill", area_d); bpy.context.collection.objects.link(area)
area.location = (-4, -4, 4); area.rotation_euler = (math.radians(55), 0, math.radians(-40))

# settings cycles base (cameras vem do script de render)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try: sc.cycles.device = 'GPU'
except: pass
sc.cycles.dicing_rate = 1.0

blend_out = os.path.join(OUT, "scene_furniture.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
log(f"saved scene: {blend_out}")

import json
with open(os.path.join(OUT, "scene_stats.json"), "w") as fp:
    json.dump(stats, fp, indent=2)
log("=== SCENE BUILT ===")
