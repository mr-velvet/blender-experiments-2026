"""15: abre o face_v3.blend e descobre ONDE o relevo foi parar.
Lista os 20 vertices de maior y (projecao da face +Y) com suas coords x,z.
"""
import bpy, os
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,"face_v3.blend"))
obj=bpy.data.objects.get("Face")
vs=sorted(obj.data.vertices, key=lambda v:-v.co.y)[:30]
lines=[f"y={v.co.y:.3f} x={v.co.x:.3f} z={v.co.z:.3f}" for v in vs]
# tambem: vertices na face +Y (y>0.9) com maior desvio de y=1.0
face=[v for v in obj.data.vertices if v.co.y>0.5]
bump=sorted(face,key=lambda v:-abs(v.co.y-1.0))[:15]
lines.append("--- maiores desvios na face +Y ---")
lines+= [f"dy={v.co.y-1.0:+.3f} x={v.co.x:.3f} z={v.co.z:.3f}" for v in bump]
open(os.path.join(OUT,"15_where.txt"),"w").write("\n".join(lines))
bpy.ops.wm.quit_blender()
