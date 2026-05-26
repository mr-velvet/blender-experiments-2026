"""16: close-up extremo no centro da face do v5 + estatistica do relevo.
Confirma se o relevo esta no mesh renderizado."""
import bpy, os, math
from mathutils import Vector
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"face_v5.blend"))
obj=bpy.data.objects.get("Face")
# stats
ys=[v.co.y for v in obj.data.vertices]
n_bump=sum(1 for y in ys if y>1.05)
print(f"VERTS y>1.05 (relevo real): {n_bump}, ymax={max(ys):.3f}")
# garante sem modifiers escondendo
for m in list(obj.modifiers): print("MOD:", m.type, m.show_render, m.show_viewport)
# camera close no centro do relevo (x~-0.1, z~0.12), olhando de 3/4
sc=bpy.context.scene
for o in list(sc.objects):
    if o.type=='CAMERA': sc.collection.objects.unlink(o)
cd=bpy.data.cameras.new("CC"); cam=bpy.data.objects.new("CC",cd)
cd.type='ORTHO'; cd.ortho_scale=0.9
cam.location=(0.6,-2.2,0.6); aim=Vector((-0.05,1.0,0.12))
cam.rotation_euler=(cam.location-aim).to_track_quat('Z','Y').to_euler()
sc.collection.objects.link(cam); sc.camera=cam
sc.render.resolution_x=600; sc.render.resolution_y=600
sc.render.engine='CYCLES'; sc.cycles.samples=48
sc.render.filepath=os.path.join(OUT,"face_v5_close.png")
bpy.ops.render.render(write_still=True)
print("saved close")
bpy.ops.wm.quit_blender()
