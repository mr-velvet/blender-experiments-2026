"""28: PRINT DA TELA (viewport) do rosto montado, SEM render Cycles.
Abre asm_a3.blend, shading SOLID com sombra+cavity (matcap-like), tira
screenshot OpenGL da viewport em frontal e 3/4. Isso e literalmente "print
da tela do Blender" sem path-tracing."""
import bpy, os, math
from mathutils import Euler
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
BLEND=os.path.join(OUT,"asm_a3.blend")
def gv():
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type=='VIEW_3D':
                r=next((x for x in a.regions if x.type=='WINDOW'),None)
                return win,a,r,a.spaces.active.region_3d
    return None,None,None,None
_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='STUDIO'
    sp.shading.color_type='SINGLE'; sp.shading.single_color=(0.85,0.78,0.7)
    sp.shading.show_shadows=True
    try: sp.shading.shadow_intensity=0.5
    except: pass
    sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=1.5; sp.shading.cavity_valley_factor=1.5
    sp.overlay.show_overlays=False
    sc=bpy.context.scene; sc.render.resolution_x=700; sc.render.resolution_y=700
    rv3d.view_perspective='ORTHO'; rv3d.view_location=(0,0,0)
    views={
        "front":(Euler((0,0,0),'XYZ'),2.3),
        "tilt": (Euler((math.radians(-20),0,0),'XYZ'),2.5),
    }
    for nm,(eul,dist) in views.items():
        rv3d.view_rotation=eul.to_quaternion(); rv3d.view_distance=dist
        bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"asm_a3_viewport_{nm}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        print("saved",nm)
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0)
