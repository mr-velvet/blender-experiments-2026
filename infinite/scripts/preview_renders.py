"""Renderiza preview rapido (Eevee Next) de cada blend pra inspecao visual."""
import bpy
import os
import sys
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "out"))
GLB_DIR = os.path.join(OUT_DIR, "glb")
PREVIEW_DIR = os.path.join(OUT_DIR, "previews")
os.makedirs(PREVIEW_DIR, exist_ok=True)

name = sys.argv[-1]
blend_path = os.path.join(GLB_DIR, f"{name}.blend")
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene

# eevee
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 720
scene.render.image_settings.file_format = 'PNG'

# centro da cena: bbox de tudo visivel
import mathutils
mins = mathutils.Vector((1e9, 1e9, 1e9))
maxs = mathutils.Vector((-1e9, -1e9, -1e9))
for o in scene.objects:
    if o.type != 'MESH':
        continue
    if o.location.x < -50:  # template escondido
        continue
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            mins[i] = min(mins[i], w[i])
            maxs[i] = max(maxs[i], w[i])
center = (mins + maxs) / 2
size = max(maxs - mins)

# camera
cam_data = bpy.data.cameras.new("PreviewCam")
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

dist = size * 1.4
cam_obj.location = (center.x + dist * 0.7, center.y - dist * 0.9, center.z + dist * 0.55)
# look_at
direction = center - cam_obj.location
rot_q = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

# luz extra (caso o sun do blend nao esteja iluminando bem)
bpy.ops.object.light_add(type='SUN', location=(20, -20, 50))
bpy.context.active_object.data.energy = 4.0
bpy.context.active_object.rotation_euler = (math.radians(45), math.radians(20), 0)

# world
world = scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.65, 0.75, 0.85, 1.0)
    bg.inputs["Strength"].default_value = 0.8

out_png = os.path.join(PREVIEW_DIR, f"{name}.png")
scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print(f"OK render {out_png}")
