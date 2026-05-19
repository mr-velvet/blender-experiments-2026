import bpy
import os
import sys

SRC_BLEND = r"C:\Users\manu\Downloads\BLENDER-CARDBOARD\Cardboard Shader 1.2 (Blender 3.4+).blend"
OUT_DIR = r"C:\Users\manu\ved\blender-experiments-2026\out"
MATERIAL_NAME = "Cardboard Outer"

os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object
cube.name = "CardboardCube"

bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))

with bpy.data.libraries.load(SRC_BLEND, link=False) as (data_from, data_to):
    if MATERIAL_NAME in data_from.materials:
        data_to.materials = [MATERIAL_NAME]
    else:
        print("AVAIL_MATERIALS:", list(data_from.materials))
        raise SystemExit("Material not found in source blend")

mat = bpy.data.materials.get(MATERIAL_NAME)
if mat is None:
    raise SystemExit("Material append failed")

cube.data.materials.clear()
cube.data.materials.append(mat)
print("APPLIED_MATERIAL:", mat.name, "to", cube.name)

bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
bpy.ops.object.shade_smooth()

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (5, -5, 4)
cam.rotation_euler = (1.0, 0, 0.785)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (0.785, 0.3, 0.5)
bpy.context.scene.collection.objects.link(sun)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.filepath = os.path.join(OUT_DIR, "preview.png")
scene.render.image_settings.file_format = 'PNG'

try:
    bpy.ops.render.render(write_still=True)
    print("RENDER_OK:", scene.render.filepath)
except Exception as e:
    print("RENDER_FAIL:", e)

glb_path = os.path.join(OUT_DIR, "cardboard_cube.glb")
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_materials='EXPORT',
    export_image_format='AUTO',
)
print("GLB_EXPORTED:", glb_path, "size:", os.path.getsize(glb_path), "bytes")

blend_out = os.path.join(OUT_DIR, "scene.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print("BLEND_SAVED:", blend_out)
