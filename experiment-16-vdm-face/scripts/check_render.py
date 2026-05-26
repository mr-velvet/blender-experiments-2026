"""Carrega um .blend e renderiza o Target de frente (olhando a face +X) pra ver
se a deformacao VDM realmente apareceu. Headless OK (so render, sem sculpt)."""
import bpy, sys, os

argv = sys.argv[sys.argv.index("--")+1:]
blendpath = argv[0]
outpng = argv[1]

bpy.ops.wm.open_mainfile(filepath=blendpath)
obj = bpy.data.objects.get("Target")

# stats de deformacao: bounding box em X (face +X deveria ter saido pra fora de 1.0)
xs = [ (obj.matrix_world @ v.co).x for v in obj.data.vertices ]
print(f"[geo] x range = {min(xs):.4f} .. {max(xs):.4f}  (cubo base = -1..1)")

# material cinza claro
for o in bpy.data.objects:
    pass
mat = bpy.data.materials.new("clay"); mat.use_nodes=True
b = mat.node_tree.nodes.get("Principled BSDF")
if b:
    b.inputs["Base Color"].default_value=(0.8,0.72,0.62,1)
    b.inputs["Roughness"].default_value=0.6
obj.data.materials.clear(); obj.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.object.shade_smooth()

# camera olhando a face +X de frente, levemente de cima/lado
cam_data=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cam_data)
cam.location=(4.5,-1.2,1.0);
import mathutils
look=mathutils.Vector((0.6,0,0))
d=(cam.location-look);
cam.rotation_euler=d.to_track_quat('Z','Y').to_euler()
bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera=cam

sun_d=bpy.data.lights.new("S",type='SUN'); sun_d.energy=3.5
sun=bpy.data.objects.new("S",sun_d); sun.rotation_euler=(0.7,0.2,-0.6)
bpy.context.scene.collection.objects.link(sun)
w=bpy.data.worlds.new("W"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.55,0.57,0.6,1)
w.node_tree.nodes["Background"].inputs[1].default_value=0.6
bpy.context.scene.world=w

s=bpy.context.scene
s.render.engine='CYCLES'; s.cycles.samples=48
s.render.resolution_x=700; s.render.resolution_y=700
s.render.filepath=outpng; s.render.image_settings.file_format='PNG'
bpy.ops.render.render(write_still=True)
print(f"[render] {outpng}")
