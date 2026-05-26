"""09: resolve o '90 graus girado' dos VDM.

Hipotese: em stroke ANCHORED, a orientacao do stamp e definida pelo vetor
mouse_start -> mouse_event (drag). O catalogo usou drag-zero, entao a rotacao
ficou no default (girada). Vou testar dragar em 4 direcoes e ver qual deixa o
nariz (brush 23) em pe.

Carimba o mesmo brush 23 em 4 planos lado a lado, cada um com drag apontando
pra uma direcao diferente (UP/RIGHT/DOWN/LEFT na tela). Captura via OpenGL
viewport render (print da tela, sem path-tracing) com luz rasante.
"""
import bpy, os, math
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\angle"
LOGF = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\09_log.txt"
os.makedirs(OUT, exist_ok=True)
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='VIEW_3D':
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                return win,area,region,area.spaces.active.region_3d
    return None,None,None,None

def load_brush(idx):
    fname=f"Human Face VDM {idx:02d}.asset.blend"
    before=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,fname),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    b=bpy.data.brushes[list(set(bpy.data.brushes.keys())-before)[0]]
    if b.texture and b.texture.image: b.texture.image.colorspace_settings.name='Non-Color'
    return b

# 4 variantes de direcao de drag (dx,dy em px na tela), drag de 50px
DIRS = {"UP":(0,50), "RIGHT":(50,0), "DOWN":(0,-50), "LEFT":(-50,0)}

def setup_scene_view(ov):
    win,area,region,rv3d = get_view3d()
    # vista top-down (olhando -Z), plano no XY; zoom pra plano preencher tela
    # top-down exato pra carimbar (drag no plano da tela = plano XY do mundo)
    rv3d.view_rotation=(1,0,0,0)
    rv3d.view_perspective='ORTHO'
    rv3d.view_distance=1.45
    rv3d.view_location=(0,0,0)
    # shading: STUDIO com cavity (revela relevo mesmo de cima)
    sp=area.spaces.active
    sp.shading.type='SOLID'
    sp.shading.light='STUDIO'
    sp.shading.studio_light='Default'
    sp.shading.color_type='SINGLE'
    sp.shading.single_color=(0.8,0.74,0.66)
    sp.shading.show_cavity=True
    sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=2.0
    sp.shading.cavity_valley_factor=2.0
    sp.shading.curvature_ridge_factor=1.0
    sp.shading.curvature_valley_factor=1.0
    sp.overlay.show_overlays=False
    bpy.context.view_layer.update()
    return win,area,region,rv3d

def run(idx, label, dx, dy, ov, region, rv3d):
    # garante top-down exato pra carimbar
    rv3d.view_rotation=(1,0,0,0); rv3d.view_distance=1.45; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    # plano novo
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="P"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7
        bpy.ops.object.modifier_apply(modifier=m.name)
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
    brush=load_brush(idx)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except Exception as e: log("mapmode_err",e)
        stroke=[
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,
             "is_start":True,"location":(0,0,0),"size":110.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x+dx,c.y+dy),"mouse_event":(c.x+dx,c.y+dy),"pen_flip":False,
             "is_start":False,"location":(0,0,0),"size":110.0,"pressure":1.0,"time":0.05,"x_tilt":0,"y_tilt":0},
        ]
        z0=(min(v.co.z for v in obj.data.vertices),max(v.co.z for v in obj.data.vertices))
        try: bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'); res="OK"
        except Exception as e: res=f"FAIL {e}"
        bpy.ops.object.mode_set(mode='OBJECT')
        z1=(min(v.co.z for v in obj.data.vertices),max(v.co.z for v in obj.data.vertices))
        bpy.ops.object.shade_smooth()
    res+=f" z {z0[0]:.3f}/{z0[1]:.3f} -> {z1[0]:.3f}/{z1[1]:.3f}"
    # inclina a vista 22 graus so pra screenshot (relevo fica legivel)
    import math as _m
    from mathutils import Euler
    rv3d.view_rotation=Euler((_m.radians(22),0,0),'XYZ').to_quaternion()
    bpy.context.view_layer.update()
    # OpenGL viewport render (print da tela)
    outp=os.path.join(OUT,f"b{idx:02d}_{label}.png")
    bpy.context.scene.render.filepath=outp
    bpy.context.scene.render.resolution_x=400; bpy.context.scene.render.resolution_y=400
    with bpy.context.temp_override(**ov):
        bpy.ops.render.opengl(write_still=True)
    log(f"[b{idx} {label} d=({dx},{dy})] {res} -> {outp}")
    # limpa plano
    bpy.data.objects.remove(obj,do_unlink=True)

_done=[False]
def tick():
    if _done[0]: return None
    _done[0]=True
    try:
        win,area,region,rv3d=setup_scene_view(None)
        ov={'window':win,'area':area,'region':region}
        for idx in (23, 15):  # nariz e boca
            for label,(dx,dy) in DIRS.items():
                run(idx,label,dx,dy,ov,region,rv3d)
        log("DONE")
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender()
    return None

bpy.app.timers.register(tick, first_interval=2.0)
log("[init] angle sweep")
