# -*- coding: utf-8 -*-
"""
Experimento 27 — Render Passes / Light Groups / compositing por camadas (headless).

Monta um quarto visto de cima (camera de seguranca), ilumina com 3 luzes de
cores/temperaturas distintas, e renderiza no Cycles SEPARANDO em PNGs:
  - beauty           (imagem final completa)
  - shadow           (pass de sombra isolado)
  - lg_window  (light group: luz fria da janela)
  - lg_lamp    (light group: abajur quente)
  - lg_ambient (light group: luz colorida ambiente)

Cada light group e a contribuicao SO daquela(s) luz(es) — exatamente o
"cada luz/cor numa imagem separada" pedido. O roteamento dos passes pra
arquivos distintos e feito pelo compositor (File Output nodes), 100% headless.

Uso:
  blender --background --python build_and_render.py
"""
import bpy
import os
import math
from mathutils import Vector

# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "passes")
os.makedirs(OUT, exist_ok=True)

RES_X = int(os.environ.get("EXP27_RESX", "1920"))
RES_Y = int(os.environ.get("EXP27_RESY", "1080"))
SAMPLES = int(os.environ.get("EXP27_SAMPLES", "256"))

# ---------------------------------------------------------------------------
# 0. Cena limpa
# ---------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m


def add_box(name, size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    ob.rotation_euler = rot
    bpy.ops.object.transform_apply(scale=True, rotation=False)
    ob.data.materials.append(material)
    bpy.ops.object.shade_smooth() if False else None
    return ob


# ---------------------------------------------------------------------------
# 1. Materiais
# ---------------------------------------------------------------------------
m_floor = mat("Floor", (0.62, 0.52, 0.40), rough=0.45)     # piso de madeira clara
m_wall = mat("Wall", (0.78, 0.76, 0.74), rough=0.9)        # parede off-white
m_rug = mat("Rug", (0.45, 0.12, 0.12), rough=0.95)         # tapete vermelho
m_bed = mat("Bed", (0.30, 0.40, 0.55), rough=0.8)          # colcha azul
m_pillow = mat("Pillow", (0.92, 0.92, 0.95), rough=0.85)
m_wood = mat("Wood", (0.25, 0.16, 0.10), rough=0.55)       # moveis escuros
m_metal = mat("Metal", (0.7, 0.7, 0.72), rough=0.25, metal=1.0)
m_screen = mat("Screen", (0.02, 0.02, 0.02), rough=0.3,
               emit=(0.2, 0.5, 1.0), emit_strength=2.5)     # tela/monitor emissivo
m_lampshade = mat("LampShade", (0.95, 0.85, 0.6), rough=0.7,
                  emit=(1.0, 0.75, 0.4), emit_strength=3.0)

# ---------------------------------------------------------------------------
# 2. Geometria do quarto (planta ~6x5m, paredes 3m)
# ---------------------------------------------------------------------------
W, D, H = 6.0, 5.0, 3.0
t = 0.15  # espessura parede

# piso (um pouco maior que as paredes pra ancorar visualmente)
add_box("Floor", (W, D, t), (0, 0, -t / 2), m_floor)
# tapete
add_box("Rug", (3.0, 2.2, 0.03), (0.6, -0.4, 0.02), m_rug)
# 3 paredes (a parede SUL fica baixa/parcial — e por cima dela que a camera CCTV olha)
# Vista dollhouse olha de SE->NW: paredes do FUNDO (N e W) ficam visiveis e
# fecham a cena; paredes da FRENTE (E e S) ficam ABERTAS pra nao tampar.
add_box("Wall_N", (W, t, H), (0, D / 2, H / 2), m_wall)

# parede OESTE solida + janela como PAINEL EMISSIVO embutido (azul claro).
# Mais limpo que vao fragmentado e da uma "janela" nitida na parede.
add_box("Wall_W", (t, D, H), (-W / 2, 0, H / 2), m_wall)
m_window = mat("WindowGlass", (0.6, 0.75, 1.0), rough=0.1,
               emit=(0.62, 0.78, 1.0), emit_strength=22.0)
add_box("WindowPane", (0.04, 2.0, 1.5), (-W / 2 + t / 2 + 0.03, -1.0, 1.6),
        m_window)

# cama
add_box("BedBase", (2.6, 2.0, 0.45), (-1.2, 1.2, 0.225), m_wood)
add_box("Mattress", (2.5, 1.9, 0.25), (-1.2, 1.2, 0.55), m_bed)
add_box("Pillow1", (1.0, 0.5, 0.18), (-1.2, 1.9, 0.78), m_pillow)

# mesa + monitor (canto sudeste)
add_box("Desk", (1.6, 0.7, 0.08), (2.0, -1.4, 0.78), m_wood)
add_box("DeskLeg1", (0.08, 0.08, 0.78), (1.3, -1.7, 0.39), m_wood)
add_box("DeskLeg2", (0.08, 0.08, 0.78), (2.7, -1.7, 0.39), m_wood)
add_box("Monitor", (0.9, 0.06, 0.55), (2.0, -1.15, 1.15), m_screen)
add_box("MonitorStand", (0.1, 0.2, 0.2), (2.0, -1.3, 0.92), m_metal)

# estante + caixas
add_box("Shelf", (1.8, 0.4, 2.2), (1.6, 2.2, 1.1), m_wood)
add_box("Box1", (0.4, 0.3, 0.4), (1.0, 2.2, 1.7), m_bed)
add_box("Box2", (0.4, 0.3, 0.4), (1.6, 2.2, 1.7), m_rug)
add_box("Box3", (0.4, 0.3, 0.4), (2.2, 2.2, 0.6), m_metal)

# abajur na mesinha de cabeceira
add_box("NightTable", (0.5, 0.5, 0.55), (0.5, 1.9, 0.275), m_wood)
add_box("LampBase", (0.12, 0.12, 0.3), (0.5, 1.9, 0.7), m_metal)
add_box("LampShade", (0.35, 0.35, 0.3), (0.5, 1.9, 0.95), m_lampshade)

# cadeira simples
add_box("ChairSeat", (0.5, 0.5, 0.08), (2.0, -0.7, 0.5), m_wood)
add_box("ChairBack", (0.5, 0.08, 0.5), (2.0, -0.46, 0.78), m_wood)

# ---------------------------------------------------------------------------
# 3. Luzes — cada uma vira um LIGHT GROUP
# ---------------------------------------------------------------------------
# registrar os grupos no view layer ANTES de atribuir nas luzes
_vl = scene.view_layers[0]
for _g in ("window", "lamp", "ambient"):
    _vl.lightgroups.add(name=_g)


def add_light(name, ltype, loc, energy, color, group, size=1.0,
              rot=(0, 0, 0), spot_size=1.2):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = color
    if ltype == "AREA":
        ld.size = size
    if ltype == "SPOT":
        ld.spot_size = spot_size
        ld.spot_blend = 0.4
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    ob.lightgroup = group  # <- light group e atributo do OBJETO (nao do data-block) no 4.3
    return ob


# (a) Luz da janela: NAO uso area light separada (area lights aparecem como
# painel branco flutuante pra camera no Cycles 4.3 e nao da pra esconder via
# visible_camera). Em vez disso, o PROPRIO painel de janela emissivo ilumina
# a cena (mesh light) — fica integrado na parede e nao flutua. Ele entra no
# light group "window".
_wp = bpy.data.objects.get("WindowPane")
if _wp:
    _wp.lightgroup = "window"

# (b) Abajur: ponto quente LOGO ACIMA do quebra-luz (nao dentro dele)
add_light("LampLight", "POINT", (0.5, 1.9, 1.18),
          energy=600.0, color=(1.0, 0.55, 0.2), group="lamp")

# (c) Ambiente colorido: spot largo de cima jogando um tom magenta/roxo no centro
add_light("AmbientLight", "SPOT", (0.5, -0.2, 2.9),
          energy=1400.0, color=(0.75, 0.2, 0.95), group="ambient",
          rot=(0, 0, 0), spot_size=math.radians(150))

# World: leve preenchimento azulado pra cena nao boiar no preto absoluto
world = bpy.data.worlds.new("W")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.03, 0.035, 0.05, 1.0)
bg.inputs["Strength"].default_value = 1.0
scene.world = world

# ---------------------------------------------------------------------------
# 4. Camera de seguranca — alta, inclinada pra baixo, olhando o quarto
# ---------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("SecCam")
# vista "dollhouse" diagonal de cima — sempre enquadra o quarto inteiro sem
# paredes saindo do quadro. Ortografica, olhando o quarto de cima/diagonal.
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 9.5
cam = bpy.data.objects.new("SecCam", cam_data)
cam.location = (6.5, -6.5, 7.5)
scene.collection.objects.link(cam)
scene.camera = cam
target = Vector((-0.2, 0.0, 0.4))  # centro do quarto
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------------------
# 5. Render settings — Cycles + passes
# ---------------------------------------------------------------------------
scene.render.engine = 'CYCLES'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
# tentar GPU; se nao houver, cai pra CPU automaticamente
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = 'GPU'
except Exception as e:
    print("GPU setup falhou, usando CPU:", e)
    scene.cycles.device = 'CPU'

scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
# tonemap: AgX (4.x) da rolloff suave nos estouros; leve exposicao negativa
try:
    scene.view_settings.view_transform = 'AgX'
    print("view_transform = AgX OK")
except Exception as e:
    print("view transform falhou:", e)
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception as e:
    print("look falhou:", e)
scene.view_settings.exposure = -0.2

vl = scene.view_layers[0]
# passes (light groups ja foram registrados na secao 3)
vl.use_pass_combined = True
vl.use_pass_shadow = True
vl.use_pass_diffuse_direct = True
vl.use_pass_diffuse_color = True
vl.use_pass_ambient_occlusion = True

print("LightGroups no view layer:", [lg.name for lg in vl.lightgroups])

# ---------------------------------------------------------------------------
# 6. Compositor — rotear cada pass pra um File Output PNG separado
# ---------------------------------------------------------------------------
scene.use_nodes = True
nt = scene.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)

rl = nt.nodes.new("CompositorNodeRLayers")
rl.location = (-400, 0)

print("Sockets de saida do Render Layers:")
for s in rl.outputs:
    print("   ", repr(s.name), "enabled=", s.enabled)


def file_out(label, socket_name, y, color_only=True):
    """Cria um File Output node de 1 slot PNG para o socket dado."""
    if socket_name not in rl.outputs:
        print("!! socket ausente:", socket_name, "-> pulando", label)
        return False
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.location = (300, y)
    fo.base_path = OUT
    fo.format.file_format = 'PNG'
    fo.format.color_mode = 'RGBA'
    fo.file_slots[0].path = label + "_"
    nt.links.new(rl.outputs[socket_name], fo.inputs[0])
    print("   roteado:", socket_name, "->", label)
    return True


# beauty
file_out("beauty", "Image", 300)
# AO (bonus de profundidade/contato)
file_out("ao", "AO", 0)
# light groups -> sockets chamam "Combined_<grupo>"
file_out("lg_window", "Combined_window", -150)
file_out("lg_lamp", "Combined_lamp", -300)
file_out("lg_ambient", "Combined_ambient", -450)

# ---------------------------------------------------------------------------
# 7. Render passada 1 — beauty + AO + light groups
# ---------------------------------------------------------------------------
print(">>> Passada 1 (beauty + light groups)", RES_X, "x", RES_Y,
      "samples", SAMPLES)
bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# 8. Render passada 2 — SOMBRA isolada via Shadow Catcher
# ---------------------------------------------------------------------------
# Sombra pura: piso/tapete viram shadow catcher (so registram a sombra
# recebida, com alpha onde nao ha sombra). Todos os outros objetos ficam
# INVISIVEIS a camera mas continuam PROJETANDO sombra (visible_camera=False,
# visible_shadow=True). film_transparent => camada limpa pra sobrepor em 2D.
print(">>> Passada 2 (shadow catcher)")
CATCHERS = {"Floor", "Rug"}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if o.name in CATCHERS:
        o.is_shadow_catcher = True
    else:
        o.visible_camera = False
        o.visible_shadow = True
        o.visible_diffuse = False
        o.visible_glossy = False

scene.render.film_transparent = True

# compositor so com o beauty (=sombra projetada no catcher) -> shadow PNG
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
# 9. Normalizar nomes (compositor adiciona sufixo de frame _0001)
# ---------------------------------------------------------------------------
import re
for f in os.listdir(OUT):
    m = re.match(r"(.+?)_(\d{4})\.png$", f)
    if m:
        new = m.group(1) + ".png"
        src = os.path.join(OUT, f)
        dst = os.path.join(OUT, new)
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)

print(">>> Render concluido. Arquivos em:", OUT)
for f in sorted(os.listdir(OUT)):
    print("   ", f)
