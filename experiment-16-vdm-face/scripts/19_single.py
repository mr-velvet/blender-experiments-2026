"""19: tudo num processo so. Carimba nariz grande no centro, recalcula normais,
mede silhueta, renderiza matcap 3/4 e cycles. Elimina a variavel save/reabrir.
"""
import bpy, os, math
from mathutils import Vector, Euler
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\single"
os.makedirs(OUT,exist_ok=True)
def gv():
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type=='VIEW_3D':
                r=next((x for x in a.regions if x.type=='WINDOW'),None)
                return win,a,r,a.spaces.active.region_3d
    return None,None,None,None
def load_brush(idx):
    f=f"Human Face VDM {idx:02d}.asset.blend"; b0=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,f),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    b=bpy.data.brushes[list(set(bpy.data.brushes.keys())-b0)[0]]
    if b.texture and b.texture.image: b.texture.image.colorspace_settings.name='Non-Color'
    return b
_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2)
        obj=bpy.context.view_layer.objects.active
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7; m.subdivision_type='SIMPLE'
        bpy.ops.object.modifier_apply(modifier=m.name)
    # vista frontal da face +Y pra carimbar
    rv3d.view_rotation=Euler((math.radians(90),0,0),'XYZ').to_quaternion()
    rv3d.view_perspective='ORTHO'; rv3d.view_distance=3.0; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    brush=load_brush(28)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        c=location_3d_to_region_2d(region,rv3d,Vector((0,1.0,0)))
        st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,1.0,0),"size":200.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,1.0,0),"size":200.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')
        bpy.ops.object.mode_set(mode='OBJECT')
    # recalc normais explicitamente
    obj.data.update(); obj.data.calc_loop_triangles()
    me=obj.data
    ys=[v.co.y for v in me.vertices]
    print(f"[stamp] ymax={max(ys):.3f} n_bump={sum(1 for y in ys if y>1.05)}")
    with bpy.context.temp_override(**ov):
        obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.shade_flat()  # flat: silhueta e relevo sem suavizar
    # matcap 3/4
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='MATCAP'; sp.shading.single_color=(0.8,0.74,0.66)
    sp.shading.color_type='SINGLE'; sp.overlay.show_overlays=False
    rv3d.view_rotation=Euler((math.radians(72),0,math.radians(-32)),'XYZ').to_quaternion()
    rv3d.view_distance=2.6; bpy.context.view_layer.update()
    sc=bpy.context.scene; sc.render.resolution_x=700; sc.render.resolution_y=700
    sc.render.filepath=os.path.join(OUT,"matcap34.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
    print("saved matcap34")
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0)
