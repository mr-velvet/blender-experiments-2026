"""Teste: 1 movel x 2 efeitos lado a lado, render rapido. Valida a lib."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_furniture as L

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
STOVE = r"C:\Users\manu\blenderkit_data\models\old-rusty-stove_d0b8ec34-c43c-4df5-9c81-0b644dcf6286\old-rusty-stove_0_5K_ebe04362-f109-4921-a28a-8af0c65a766a.blend"

# limpar
bpy.ops.wm.read_factory_settings(use_empty=True)

# cardboard (esquerda)
o1 = L.import_furniture(STOVE, "stove_cardboard")
L.normalize(o1, target_height=0.9)
L.apply_cardboard(o1)
o1.location.x = -0.7

# massinha (direita)
o2 = L.import_furniture(STOVE, "stove_clay")
L.normalize(o2, target_height=0.9)
L.apply_clay(o2, color=(0.85, 0.35, 0.30), displacement=0.2)
o2.location.x = 0.7

# chao
bpy.ops.mesh.primitive_plane_add(size=10, location=(0,0,0))
plane = bpy.context.active_object
pm = bpy.data.materials.new("Floor"); pm.use_nodes = True
pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18,0.18,0.2,1)
plane.data.materials.append(pm)

# camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0, -2.6, 1.3)
cam.rotation_euler = (math.radians(75), 0, 0)
bpy.context.scene.camera = cam

# luz + world
sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_d); bpy.context.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(40))
w = bpy.data.worlds.new("W"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.6,0.65,0.75,1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
bpy.context.scene.world = w

# render
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
try: sc.cycles.device = 'GPU'
except: pass
sc.cycles.samples = 48
sc.cycles.dicing_rate = 1.0
sc.render.resolution_x = 1000
sc.render.resolution_y = 600
sc.render.filepath = os.path.join(OUT, "test_stove_pair.png")
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("[TEST] rendered", sc.render.filepath, flush=True)
