"""
Monta a sequencia de cotidiano no MANNEQUIN NATIVO do Rokoko e renderiza em MP4.
Concatena os 4 clips (sit, drink, talk, stand) numa unica timeline via NLA strips,
usando o personagem skinned que ja vem no GLB do Rokoko (animacao impecavel).

Uso:
  blender --background --python 04_sequence_native.py -- <out.mp4> <clip1.glb> <clip2.glb> ...
"""
import bpy, sys, mathutils, math

argv = sys.argv[sys.argv.index("--") + 1:]
OUT_MP4 = argv[0]
CLIPS = argv[1:]


def log(*a):
    print("[seq]", *a)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# importa o primeiro clip COMPLETO (mesh + armature) = personagem base
log("base clip:", CLIPS[0])
bpy.ops.import_scene.gltf(filepath=CLIPS[0])
base_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
base_arm.name = "Mannequin"
meshes = [o for o in bpy.data.objects if o.type == 'MESH']

# coleta as actions de cada clip: importa cada um so pra extrair a action do armature
actions = []
base_action = base_arm.animation_data.action
base_action.name = "clip_0"
actions.append(base_action)

for i, clip in enumerate(CLIPS[1:], start=1):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=clip)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    act = arm.animation_data.action
    act.name = f"clip_{i}"
    act.use_fake_user = True
    actions.append(act)
    # remove os objetos extra desse clip (so queriamos a action)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    log(f"action extraida clip_{i} de {clip}")

# monta NLA no mannequin: empilha os clips em sequencia
base_arm.animation_data.action = None
nla = base_arm.animation_data.nla_tracks.new()
nla.name = "Sequence"
cursor = 0
gap = 4  # frames de respiro entre clips
for i, act in enumerate(actions):
    dur = int(act.frame_range[1] - act.frame_range[0])
    strip = nla.strips.new(act.name, int(cursor), act)
    strip.frame_start = cursor
    strip.frame_end = cursor + dur
    log(f"strip {act.name}: {int(cursor)}..{int(cursor+dur)}")
    cursor += dur + gap

sc.frame_start = 0
sc.frame_end = int(cursor)
log("timeline total:", sc.frame_start, "->", sc.frame_end)

# ----------------------------------------- material limpo
mat = bpy.data.materials.new("Skin"); mat.use_nodes = True
b = mat.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.82, 0.66, 0.55, 1)
b.inputs["Roughness"].default_value = 0.5
for m in meshes:
    m.data.materials.clear(); m.data.materials.append(mat)

# ----------------------------------------- bbox p/ camera (no frame 0)
sc.frame_set(0)
bpy.context.view_layer.update()
c = mathutils.Vector((0, 0, 0)); n = 0; zmin = 1e9
for m in meshes:
    for v in m.bound_box:
        w = m.matrix_world @ mathutils.Vector(v); c += w; n += 1; zmin = min(zmin, w.z)
c /= n
log("center", tuple(round(x, 2) for x in c), "zmin", round(zmin, 2))

# piso
bpy.ops.mesh.primitive_plane_add(size=30, location=(c.x, c.y, zmin))
fl = bpy.context.active_object
fmat = bpy.data.materials.new("Floor"); fmat.use_nodes = True
fmat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.22, 0.24, 0.28, 1)
fmat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.85
fl.data.materials.append(fmat)

# cadeira (assento + encosto) na altura de sentar
seat = max(0.42, c.z * 0.5)
for loc, scl in [((c.x, c.y, zmin + seat), (0.45, 0.45, 0.05)),
                 ((c.x, c.y + 0.42, zmin + seat + 0.45), (0.45, 0.05, 0.45))]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.scale = scl
    cm = bpy.data.materials.new("Chair"); cm.use_nodes = True
    cm.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.4, 0.24, 0.14, 1)
    o.data.materials.append(cm)

# camera
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d)
sc.collection.objects.link(cam)
cam.location = (c.x + 3.0, c.y - 4.2, c.z + 0.8)
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_d.lens = 50
sc.camera = cam

# luzes 3-point
for nm, loc, e, sz in [("Key", (c.x+3, c.y-3, c.z+4), 6000, 5),
                       ("Fill", (c.x-4, c.y-1, c.z+2), 2500, 6),
                       ("Rim", (c.x-1, c.y+4, c.z+4), 4000, 4)]:
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = e; ld.size = sz
    o = bpy.data.objects.new(nm, ld); o.location = loc
    o.rotation_euler = (c - o.matrix_world.translation).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(o)

if sc.world is None: sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.3, 0.34, 0.4, 1)
sc.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 1.0

# render
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.fps = 24
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'
sc.render.filepath = OUT_MP4
log("render", sc.frame_start, "->", sc.frame_end, "engine", sc.render.engine)

# stills de validacao (1 por movimento) antes do video
import os
sdir = os.path.join(os.path.dirname(OUT_MP4), "seq_stills")
sc.render.image_settings.file_format = 'JPEG'
for f in [36, 112, 188, 264]:
    sc.frame_set(f); sc.render.filepath = os.path.join(sdir, f"f{f:03d}.jpg")
    bpy.ops.render.render(write_still=True); log("still", f)

# video
sc.render.image_settings.file_format = 'FFMPEG'
sc.render.filepath = OUT_MP4
bpy.ops.render.render(animation=True)
log("OK:", OUT_MP4)
