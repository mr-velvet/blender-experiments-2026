"""
Monta cena de render a partir do .blend retargetado e renderiza a sequencia em MP4.
Camera orbital leve, 3-point light, piso, cadeira simples (contexto do 'sentar').

Uso:
  blender --background <retarget.blend> --python 02_render.py -- <out.mp4>
"""
import bpy, sys, math

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_MP4 = argv[0]


def log(*a):
    print("[render]", *a)


sc = bpy.context.scene

# acha o target animado e seu mesh
target = bpy.data.objects.get("TARGET_Quaternius")
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent == target]
log("target:", target.name if target else None, "meshes:", [m.name for m in meshes])

# esconde o source (mocap Rokoko) e seu mesh do render
src = bpy.data.objects.get("SOURCE_Rokoko")
for o in bpy.data.objects:
    if o == src or (o.parent == src):
        o.hide_render = True
        o.hide_viewport = True

# bbox do personagem alvo para posicionar camera/piso
import mathutils
zmin = 1e9
center = mathutils.Vector((0, 0, 0))
n = 0
for m in meshes:
    for v in m.bound_box:
        wv = m.matrix_world @ mathutils.Vector(v)
        zmin = min(zmin, wv.z)
        center += wv
        n += 1
if n:
    center /= n
log("center", tuple(round(c, 2) for c in center), "zmin", round(zmin, 3))

# ------------------------------------------------- piso
bpy.ops.mesh.primitive_plane_add(size=20, location=(center.x, center.y, zmin))
floor = bpy.context.active_object
mat_f = bpy.data.materials.new("FloorMat")
mat_f.use_nodes = True
bsdf = mat_f.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.18, 0.19, 0.22, 1)
bsdf.inputs["Roughness"].default_value = 0.9
floor.data.materials.append(mat_f)

# ------------------------------------------------- cadeira simples (contexto do sentar)
# assento na altura ~ quadril sentado; cubo achatado + 4 pernas finas
seat_h = center.z * 0.55
bpy.ops.mesh.primitive_cube_add(size=1, location=(center.x, center.y + 0.02, zmin + seat_h))
chair = bpy.context.active_object
chair.scale = (0.42, 0.42, 0.05)
mat_c = bpy.data.materials.new("ChairMat")
mat_c.use_nodes = True
mat_c.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.35, 0.2, 0.12, 1)
chair.data.materials.append(mat_c)
# encosto
bpy.ops.mesh.primitive_cube_add(size=1, location=(center.x, center.y + 0.42, zmin + seat_h + 0.42))
back = bpy.context.active_object
back.scale = (0.42, 0.05, 0.42)
back.data.materials.append(mat_c)

# ------------------------------------------------- material do personagem
# substitui TODOS os slots (FBX importou materiais com texturas faltando -> roxo)
skin = bpy.data.materials.new("Skin")
skin.use_nodes = True
bs = skin.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value = (0.82, 0.64, 0.52, 1)
bs.inputs["Roughness"].default_value = 0.55
cloth = bpy.data.materials.new("Cloth")
cloth.use_nodes = True
cloth.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.2, 0.35, 0.6, 1)
for m in meshes:
    m.data.materials.clear()
    # corpo principal pele, demais (sobrancelha/olhos) tom escuro
    m.data.materials.append(skin if m.name.lower().startswith("superhero") or "male" in m.name.lower() else cloth)

# ------------------------------------------------- camera (3/4 frontal)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
dist = 4.2
cam.location = (center.x + dist * 0.7, center.y - dist * 0.85, center.z + 0.4)
# aponta pro centro do corpo
direction = center - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam

# ------------------------------------------------- luzes 3-point
def add_light(name, loc, energy, kind='AREA', size=3):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if kind == 'AREA':
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    sc.collection.objects.link(o)
    d = center - o.matrix_world.translation
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o

add_light("Key", (center.x + 3, center.y - 3, center.z + 4), 6000, size=5)
add_light("Fill", (center.x - 4, center.y - 1, center.z + 2), 2500, size=6)
add_light("Rim", (center.x - 1, center.y + 4, center.z + 4), 4000, size=4)

# world claro (ambient)
if sc.world is None:
    sc.world = bpy.data.worlds.new("World")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.32, 0.36, 0.42, 1)
    bg.inputs["Strength"].default_value = 1.0

# ------------------------------------------------- render settings
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 4.2+
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.fps = 24
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'
sc.render.filepath = OUT_MP4
log("engine:", sc.render.engine, "frames:", sc.frame_start, "->", sc.frame_end)

# salva a cena montada (pra stills/reuso)
bpy.ops.wm.save_as_mainfile(filepath=OUT_MP4.rsplit('.', 1)[0] + "_scene.blend")

bpy.ops.render.render(animation=True)
log("render concluido:", OUT_MP4)
