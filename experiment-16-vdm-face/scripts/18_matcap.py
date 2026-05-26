"""18: abre o v5 e renderiza viewport com MATCAP (clay) em 3 vistas.
MatCap sombreia pela normal -> mostra relevo sem depender de posicao de luz.
Timer-driven (precisa de GUI pro OpenGL). Auto-fecha.
"""
import bpy, os, math
from mathutils import Vector, Euler
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\matcap"
os.makedirs(OUT,exist_ok=True)
BLEND=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\face_v5.blend"

def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='VIEW_3D':
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                return win,area,region,area.spaces.active.region_3d
    return None,None,None,None

_done=[False]
def tick():
    if _done[0]: return None
    _done[0]=True
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    win,area,region,rv3d=get_view3d(); ov={'window':win,'area':area,'region':region}
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='MATCAP'
    # escolhe um matcap clay disponivel
    try: sp.shading.studio_light='clay_brown.exr'
    except: pass
    sp.shading.color_type='SINGLE'; sp.shading.single_color=(0.8,0.74,0.66)
    sp.overlay.show_overlays=False
    sc=bpy.context.scene
    sc.render.resolution_x=700; sc.render.resolution_y=700
    views={
        "front":Euler((math.radians(90),0,0),'XYZ'),
        "q34":  Euler((math.radians(72),0,math.radians(-32)),'XYZ'),
        "side": Euler((math.radians(78),0,math.radians(-60)),'XYZ'),
    }
    rv3d.view_perspective='ORTHO'; rv3d.view_location=(0,0,0); rv3d.view_distance=2.6
    for name,eul in views.items():
        rv3d.view_rotation=eul.to_quaternion(); bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        print("saved",name)
    # lista matcaps disponiveis
    try:
        names=[s.name for s in bpy.context.preferences.studio_lights if s.type=='MATCAP']
        print("MATCAPS:", names[:12])
    except Exception as e: print("ml err",e)
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick, first_interval=2.0)
