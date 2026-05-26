"""17: orbita a face do v5 em varios angulos pra achar a vista que mostra o
relevo. Camera sempre mirando o ponto medio das features (0,1,0), distancia
fixa, varia azimute e elevacao. Luz key segue a camera (headlight 3/4).
"""
import bpy, os, math
from mathutils import Vector
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\orbit"
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\face_v5.blend")
sc=bpy.context.scene
obj=bpy.data.objects.get("Face")
# limpa cameras e luzes antigas
for o in list(sc.objects):
    if o.type in ('CAMERA','LIGHT'): bpy.data.objects.remove(o,do_unlink=True)
aim=Vector((0,0.0,0.0))  # mira o centro do cubo; a face +Y fica de frente
cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
cd.type='ORTHO'; cd.ortho_scale=2.5; sc.collection.objects.link(cam); sc.camera=cam
ld=bpy.data.lights.new("K",type='SUN'); ld.energy=4.0; ld.angle=0.05
lamp=bpy.data.objects.new("K",ld); sc.collection.objects.link(lamp)
fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.0; fd.angle=0.5
fl=bpy.data.objects.new("F",fd); sc.collection.objects.link(fl)
w=bpy.data.worlds.new("W"); w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.05,0.06,1)
w.node_tree.nodes["Background"].inputs[1].default_value=0.2; sc.world=w
sc.render.engine='CYCLES'; sc.cycles.samples=40
sc.render.resolution_x=500; sc.render.resolution_y=500
R=5.0
# (azim em graus a partir de -Y, elev em graus)
views=[("front",0,0),("q_r",30,15),("q_l",-30,15),("side_r",60,10),("low",0,-20),("high",0,35)]
for name,az,el in views:
    azr=math.radians(az); elr=math.radians(el)
    # base: -Y. azimute gira em torno de Z, elevacao em torno de X
    d=Vector((math.sin(azr)*math.cos(elr), -math.cos(azr)*math.cos(elr), math.sin(elr)))
    cam.location=aim+d*R
    cam.rotation_euler=(cam.location-aim).to_track_quat('Z','Y').to_euler()
    # luz key: vinda de cima-esquerda relativa a vista
    kd=Vector((math.sin(azr-0.7)*0.6, -math.cos(azr-0.7), 0.7))
    lamp.rotation_euler=(-kd).to_track_quat('Z','Y').to_euler()
    fl.rotation_euler=(-Vector((-kd.x,kd.y,0.3))).to_track_quat('Z','Y').to_euler()
    sc.render.filepath=os.path.join(OUT,f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("saved",name)
bpy.ops.wm.quit_blender()
