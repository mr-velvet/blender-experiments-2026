# -*- coding: utf-8 -*-
"""
Experimento 27 (cena CUBO, modelo PBR base+luz) — separa ALBEDO (base
estatica) das camadas de ILUMINACAO (que variam).

Diferenca pro build_cube.py: aqui a base e o albedo puro (DiffCol, cor do
material SEM luz) e cada light group vira ILUMINACAO PURA (luz sem a cor do
material), extraida dividindo Combined_<grupo> pela DiffCol no compositor.
Assim no viewer a base fica TRAVADA e so a luz/sombra variam por cima.

Saidas em passes_pbr/:
  base.png        = albedo puro (fixo)
  light_window/lamp/ambient.png = iluminacao pura de cada luz (multiplica a base)
  ao.png, shadow.png = mascaras (multiplicam)
  beauty.png      = referencia (imagem final completa)

Uso:
  blender --background --python build_cube_pbr.py
"""
import bpy
import os
import math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "passes_pbr")
os.makedirs(OUT, exist_ok=True)

RES_X = int(os.environ.get("EXP27_RESX", "1600"))
RES_Y = int(os.environ.get("EXP27_RESY", "1600"))
SAMPLES = int(os.environ.get("EXP27_SAMPLES", "256"))

# ---------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# ---------------------------------------------------------------------------
# 1. CUBO com bevel leve + chao
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 1.0))
cube = bpy.context.active_object
cube.name = "Cube"
# bevel leve nos cantos (modifier, fica limpo e parametrico)
bev = cube.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.08
bev.segments = 4
bev.limit_method = 'ANGLE'
bpy.ops.object.shade_smooth()
cube.data.materials.append(mat("CubeMat", (0.80, 0.78, 0.74), rough=0.45))
# auto smooth pra bevel ficar nitido sem suavizar as faces planas
try:
    bpy.ops.object.modifier_add(type='SMOOTH_BY_ANGLE')
except Exception:
    pass

# chao
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.data.materials.append(mat("FloorMat", (0.5, 0.5, 0.52), rough=0.7))

# ---------------------------------------------------------------------------
# 2. Light groups (registrar antes) + luzes
# ---------------------------------------------------------------------------
vl = scene.view_layers[0]
for g in ("window", "lamp", "ambient"):
    vl.lightgroups.add(name=g)


def add_light(name, ltype, loc, energy, color, group, size=2.0,
              rot=(0, 0, 0), spot=2.0):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = color
    if ltype == "AREA":
        ld.size = size
    if ltype == "SPOT":
        ld.spot_size = spot
        ld.spot_blend = 0.5
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    ob.lightgroup = group
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# luz fria da "janela" — vem da esquerda/frente, area grande
wl = add_light("WindowLight", "AREA", (-4.0, -3.0, 3.5),
               energy=900.0, color=(0.55, 0.72, 1.0), group="window", size=4.0)
look_at(wl, (0, 0, 1.0))

# abajur quente — pontual, da direita perto do chao
ll = add_light("LampLight", "POINT", (3.2, 1.5, 1.4),
               energy=450.0, color=(1.0, 0.55, 0.2), group="lamp")

# ambiente magenta — spot de cima
al = add_light("AmbientLight", "SPOT", (0.5, 3.5, 5.0),
               energy=1500.0, color=(0.75, 0.2, 0.95), group="ambient",
               spot=math.radians(80))
look_at(al, (0, 0, 1.0))

# world fill bem leve
world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.035, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------------------------------------------------------------------------
# 3. Camera 3/4 olhando o cubo
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (5.5, -5.5, 4.2)
scene.collection.objects.link(cam)
scene.camera = cam
look_at(cam, (0, 0, 0.9))

# ---------------------------------------------------------------------------
# 4. Render settings + passes
# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = 'GPU'
except Exception as e:
    print("GPU setup falhou, CPU:", e)
    scene.cycles.device = 'CPU'

scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass
scene.view_settings.exposure = -0.1

vl.use_pass_combined = True
vl.use_pass_ambient_occlusion = True
vl.use_pass_diffuse_color = True
vl.use_pass_diffuse_direct = True
vl.use_pass_diffuse_indirect = True

# ---------------------------------------------------------------------------
# 5. Compositor: cada pass -> PNG
# ---------------------------------------------------------------------------
scene.use_nodes = True
nt = scene.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new("CompositorNodeRLayers")


def out_node(label, y):
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.location = (700, y)
    fo.base_path = OUT
    fo.format.file_format = 'PNG'
    fo.format.color_mode = 'RGBA'
    fo.file_slots[0].path = label + "_"
    return fo


def file_out(label, socket, y):
    if socket not in rl.outputs:
        print("!! socket ausente:", socket)
        return
    fo = out_node(label, y)
    nt.links.new(rl.outputs[socket], fo.inputs[0])
    print("roteado", socket, "->", label)


# referencia + base (albedo puro) + AO
file_out("beauty", "Image", 400)
file_out("base", "DiffCol", 250)      # <- camada BASE estatica (cor do material sem luz)
file_out("ao", "AO", 100)

# ILUMINACAO PURA por light group = Combined_<grupo> / DiffCol
# (remove a cor do material, sobra so a luz daquela fonte). Multiplica a base.
EPS = 0.001  # evita divisao por zero onde o albedo e preto


def light_pure(label, group, y):
    socket = "Combined_" + group
    if socket not in rl.outputs:
        print("!! socket ausente:", socket)
        return
    # DiffCol + eps (pra nao dividir por zero)
    add = nt.nodes.new("CompositorNodeMixRGB")
    add.blend_type = 'ADD'
    add.location = (150, y)
    add.inputs[0].default_value = 1.0
    nt.links.new(rl.outputs["DiffCol"], add.inputs[1])
    add.inputs[2].default_value = (EPS, EPS, EPS, 1.0)
    # divide Combined / (DiffCol+eps)
    div = nt.nodes.new("CompositorNodeMixRGB")
    div.blend_type = 'DIVIDE'
    div.location = (400, y)
    div.inputs[0].default_value = 1.0
    nt.links.new(rl.outputs[socket], div.inputs[1])
    nt.links.new(add.outputs[0], div.inputs[2])
    fo = out_node(label, y)
    nt.links.new(div.outputs[0], fo.inputs[0])
    print("luz pura:", socket, "/ DiffCol ->", label)


light_pure("light_window", "window", -80)
light_pure("light_lamp", "lamp", -260)
light_pure("light_ambient", "ambient", -440)

# ---------------------------------------------------------------------------
# 6. Passada 1
# ---------------------------------------------------------------------------
print(">>> Passada 1 (beauty + base albedo + AO + iluminacao pura)", RES_X, "x", RES_Y)
bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# 7. Passada 2 — sombra via shadow catcher
# ---------------------------------------------------------------------------
print(">>> Passada 2 (shadow catcher)")
floor.is_shadow_catcher = True
cube.visible_camera = False
cube.visible_shadow = True
scene.render.film_transparent = True

for n in list(nt.nodes):
    nt.nodes.remove(n)
rl2 = nt.nodes.new("CompositorNodeRLayers")
fo = nt.nodes.new("CompositorNodeOutputFile")
fo.base_path = OUT
fo.format.file_format = 'PNG'
fo.format.color_mode = 'RGBA'
fo.file_slots[0].path = "shadow_"
nt.links.new(rl2.outputs["Image"], fo.inputs[0])
bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# 8. Normalizar nomes
# ---------------------------------------------------------------------------
import re
for f in os.listdir(OUT):
    m = re.match(r"(.+?)_(\d{4})\.png$", f)
    if m:
        dst = os.path.join(OUT, m.group(1) + ".png")
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(os.path.join(OUT, f), dst)

print(">>> Concluido. Arquivos:")
for f in sorted(os.listdir(OUT)):
    print("   ", f)
