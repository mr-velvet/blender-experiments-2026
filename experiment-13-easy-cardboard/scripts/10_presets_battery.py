"""
Passo 9 — bateria de presets calibrados.

Geras varios GLBs do Easy Cardboard 3.0 variando UM SOCKET DE CADA VEZ pra
entender o impacto isolado, mais 3 presets compostos finais ("caixa usada",
"caixa velha", "caixa surrada-mas-reconhecivel").

Ancora: preset oficial do plano de demo dentro do .blend do plugin (objeto Plane).
Todas as variantes mantem Split Angle=30deg (default oficial — 5deg foi um erro
do experimento anterior que despedacou tudo).

Saida:
  output/presets/<NN>_<nome>.glb
  output/presets/<NN>_<nome>.png
  output/presets/stats.json
"""
import bpy
import bmesh
import os
import json
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output", "presets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"

def log(m): print(f"[BATTERY] {m}", flush=True)

# === Preset OFICIAL extraido do objeto Plane do .blend do autor ===
PRESET_OFICIAL = {
    "Thickness": 0.01,
    "Global Scale": 1.0,
    "Wear ⏰": 0.174,
    "Seed \U0001f3b2": 0,
    "Split Angle": 0.5236,  # 30deg
    "Strength": 0.20,
    "Separation": 1.0,
    "Separation Noise Scale": 0.0,
    "Z Position": 1.0,
    " Fibers Density": 2.0,
    "Fibers Size": 0.02,
    "Displacement Strength": 0.161,
    "Normal Strength": 1.0,
    "UV Name": "UVMap",
}

def derive(base, **overrides):
    p = dict(base)
    for k, v in overrides.items():
        # tradutor: nomes amigaveis -> nomes reais do plugin (com emoji/espaco)
        keymap = {
            "wear": "Wear ⏰",
            "seed": "Seed \U0001f3b2",
            "strength": "Strength",
            "separation": "Separation",
            "sepnoise": "Separation Noise Scale",
            "displacement": "Displacement Strength",
            "fibers": " Fibers Density",
            "fibers_size": "Fibers Size",
            "thickness": "Thickness",
            "split_angle_deg": "Split Angle",
        }
        rk = keymap.get(k, k)
        if k == "split_angle_deg":
            v = math.radians(v)
        p[rk] = v
    return p

VARIANTS = [
    # === Grupo 1: baseline oficial ===
    ("01_preset_oficial", "Preset oficial do autor (objeto Plane do .blend)", PRESET_OFICIAL),

    # === Grupo 2: isola UM socket por vez ===
    ("02_wear_03",          "Wear=0.3 (baixo desgaste)",     derive(PRESET_OFICIAL, wear=0.3)),
    ("03_wear_06",          "Wear=0.6 (medio desgaste)",     derive(PRESET_OFICIAL, wear=0.6)),
    ("04_wear_10",          "Wear=1.0 (max - caixa bem desgastada)", derive(PRESET_OFICIAL, wear=1.0)),
    ("05_strength_05",      "Strength=0.5 (edge split medio)", derive(PRESET_OFICIAL, strength=0.5)),
    ("06_strength_10",      "Strength=1.0 (edge split max)",   derive(PRESET_OFICIAL, strength=1.0)),
    ("07_separation_20",    "Separation=2.0",                derive(PRESET_OFICIAL, separation=2.0)),
    ("08_separation_50",    "Separation=5.0 (max - cuidado!)", derive(PRESET_OFICIAL, separation=5.0)),
    ("09_sepnoise_20",      "Sep Noise Scale=2.0",           derive(PRESET_OFICIAL, sepnoise=2.0)),
    ("10_sepnoise_100",     "Sep Noise Scale=10.0 (max)",    derive(PRESET_OFICIAL, sepnoise=10.0)),
    ("11_displacement_10",  "Displacement Strength=1.0 (max)", derive(PRESET_OFICIAL, displacement=1.0)),
    ("12_fibers_15",        "Fibers Density=15 (medio)",     derive(PRESET_OFICIAL, fibers=15.0)),
    ("13_fibers_100",       "Fibers Density=100 (max - explode mesh)", derive(PRESET_OFICIAL, fibers=100.0)),
    ("14_thickness_004",    "Thickness=0.04 (parede 4mm)",   derive(PRESET_OFICIAL, thickness=0.04)),

    # === Grupo 3: composicoes finais ===
    ("15_used_box",         "USED — usada mas inteira",
        derive(PRESET_OFICIAL, wear=0.4, strength=0.4, separation=1.0, sepnoise=1.0, displacement=0.4, fibers=5.0, thickness=0.025)),
    ("16_aged_box",         "AGED — bem velha",
        derive(PRESET_OFICIAL, wear=0.7, strength=0.5, separation=1.5, sepnoise=2.0, displacement=0.6, fibers=10.0, thickness=0.03)),
    ("17_battered_box",     "BATTERED — surrada mas reconhecivel",
        derive(PRESET_OFICIAL, wear=1.0, strength=0.6, separation=2.0, sepnoise=3.0, displacement=0.8, fibers=15.0, thickness=0.035)),
]

# ============================================================
# Helpers
# ============================================================
def set_input(mod, name, value):
    ng = mod.node_group
    target = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == target:
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"   FAIL '{name}'={value}: {e}"); return False
    return False

def clean_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for l in list(bpy.data.lights): bpy.data.lights.remove(l)
    for c in list(bpy.data.cameras): bpy.data.cameras.remove(c)

def make_kraft_mat():
    mat = bpy.data.materials.new("Kraft")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location=(400,0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location=(100,0)
    bsdf.inputs['Base Color'].default_value = (0.55, 0.38, 0.22, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def setup_render():
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    scn.render.resolution_x = 512
    scn.render.resolution_y = 512
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = 'PNG'
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (2.6, -2.6, 1.9)
    cam.rotation_euler = (math.radians(65), 0, math.radians(45))
    scn.camera = cam
    sun_data = bpy.data.lights.new("Sun", 'SUN')
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (3, -2, 5)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.04, 0.03, 1.0)
        bg.inputs[1].default_value = 1.0

# ============================================================
# Append node groups (1x so)
# ============================================================
log("Append node groups (once)")
clean_scene()
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = [n for n in (NG_BOX, NG_CARDBOARD, NG_SMOOTH) if n in data_from.node_groups]
ng_box = bpy.data.node_groups[NG_BOX]
ng_cb = bpy.data.node_groups[NG_CARDBOARD]
ng_smooth = bpy.data.node_groups[NG_SMOOTH]

setup_render()
kraft = make_kraft_mat()

stats = {"variants": []}

# ============================================================
# Build base SBC mesh once, duplicate per variant
# ============================================================
def build_sbc_base():
    mesh = bpy.data.meshes.new("BoxBase")
    obj = bpy.data.objects.new("BoxBase", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
    bm.to_mesh(mesh); bm.free()
    m_box = obj.modifiers.new("SBC", 'NODES')
    m_box.node_group = ng_box
    for k, v in {
        'Width': 1.0, 'Length': 1.0, 'Height': 1.0,
        'Gaps (Length)': 0.07, 'Gap (Width)': 0.07, 'Flap Length': 0.11,
        'Simple Sub-D Level': 3, 'CC Sub-D Level': 0,
        'Edge Crease': 0.802, 'Delete Bounds': False,
    }.items():
        set_input(m_box, k, v)
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="SBC")
    # uv cube_project + mark seam
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True, clip_to_bounds=False, scale_to_bounds=True)
    bpy.ops.mesh.mark_seam(clear=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    if obj.data.uv_layers:
        obj.data.uv_layers[0].name = 'UVMap'
        obj.data.uv_layers[0].active = True
        obj.data.uv_layers[0].active_render = True
    return obj

log("Build SBC base mesh once")
base_obj = build_sbc_base()
base_mesh = base_obj.data.copy()  # snapshot pra duplicar
base_v = len(base_obj.data.vertices)
base_f = len(base_obj.data.polygons)
log(f"   base SBC: {base_v}v / {base_f}f")
bpy.data.objects.remove(base_obj, do_unlink=True)

# ============================================================
# Run each variant
# ============================================================
for slug, descricao, preset in VARIANTS:
    log("")
    log("=" * 60)
    log(f"VARIANT: {slug} — {descricao}")
    log("=" * 60)

    # nova copia da mesh base
    mesh_copy = base_mesh.copy()
    obj = bpy.data.objects.new(slug, mesh_copy)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(kraft)

    # Cardboard modifier com preset
    m_cb = obj.modifiers.new("EC", 'NODES')
    m_cb.node_group = ng_cb
    for k, v in preset.items():
        set_input(m_cb, k, v)

    m_sm = obj.modifiers.new("Smooth", 'NODES')
    m_sm.node_group = ng_smooth
    set_input(m_sm, 'Angle', math.radians(30.0))
    set_input(m_sm, 'Ignore Sharpness', False)

    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="EC")
    bpy.ops.object.modifier_apply(modifier="Smooth")

    v_after = len(obj.data.vertices)
    f_after = len(obj.data.polygons)
    log(f"   {base_v}v -> {v_after}v ({v_after/max(base_v,1):.1f}x), {base_f}f -> {f_after}f ({f_after/max(base_f,1):.1f}x)")

    # Export GLB
    glb = os.path.join(OUTPUT_DIR, f"{slug}.glb")
    for o in bpy.data.objects: o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format='GLB',
        use_selection=True, export_apply=True, export_yup=True,
        export_image_format='NONE',
    )
    glb_kb = os.path.getsize(glb) / 1024
    log(f"   GLB -> {os.path.basename(glb)} ({glb_kb:.1f} KB)")

    # Render
    png = os.path.join(OUTPUT_DIR, f"{slug}.png")
    bpy.context.scene.render.filepath = png
    bpy.ops.render.render(write_still=True)
    log(f"   PNG -> {os.path.basename(png)}")

    stats["variants"].append({
        "slug": slug,
        "descricao": descricao,
        "preset": {k: v for k, v in preset.items()},
        "verts_before": base_v, "faces_before": base_f,
        "verts_after": v_after, "faces_after": f_after,
        "ratio_v": v_after / max(base_v, 1),
        "ratio_f": f_after / max(base_f, 1),
        "glb_kb": glb_kb,
    })

    # Limpa a copia pra proxima rodada
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh_copy, do_unlink=True)

# Salva stats
stats_path = os.path.join(OUTPUT_DIR, "stats.json")
with open(stats_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
log(f"\nstats -> {stats_path}")

log("=== ALL DONE ===")
print("[BATTERY] === SUCCESS ===", flush=True)
