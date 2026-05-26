"""23: mede a orientacao natural (roll 0) de cada feature via PCA dos vertices
deslocados. Retorna o angulo do eixo principal no plano XY -> quanto girar
pra alinhar. Tambem mede bbox pra escala.
"""
import bpy, os, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF=os.path.join(OUT,"23_pca.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w").write("\n".join(buf))
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
def wipe(ov):
    with bpy.context.temp_override(**ov):
        if bpy.context.mode!='OBJECT':
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except: pass
    for o in list(bpy.data.objects):
        if o.type=='MESH': bpy.data.objects.remove(o,do_unlink=True)
    for b in list(bpy.data.brushes):
        if b.name.startswith("Human Face VDM") and b.users==0: bpy.data.brushes.remove(b)
def proc(bidx,ov,region,rv3d):
    wipe(ov)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active
        m=obj.modifiers.new("s","SUBSURF"); m.levels=8; bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    brush=load_brush(bidx)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
        st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":150.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":150.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT')
    # PCA dos vertices com |z|>thr
    thr=0.02
    pts=[(v.co.x,v.co.y) for v in obj.data.vertices if abs(v.co.z)>thr]
    n=len(pts)
    if n<10: log(f"b{bidx}: poucos pts ({n})"); return
    mx=sum(p[0] for p in pts)/n; my=sum(p[1] for p in pts)/n
    sxx=sum((p[0]-mx)**2 for p in pts)/n
    syy=sum((p[1]-my)**2 for p in pts)/n
    sxy=sum((p[0]-mx)*(p[1]-my) for p in pts)/n
    # angulo do eixo principal
    ang=0.5*math.atan2(2*sxy, sxx-syy)
    # extensao ao longo dos eixos principais
    import math as M
    ca,sa=M.cos(ang),M.sin(ang)
    proj1=[ (p[0]-mx)*ca+(p[1]-my)*sa for p in pts]
    proj2=[-(p[0]-mx)*sa+(p[1]-my)*ca for p in pts]
    len1=max(proj1)-min(proj1); len2=max(proj2)-min(proj2)
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    log(f"b{bidx}: n={n} centroid=({mx:.3f},{my:.3f}) pca_ang={math.degrees(ang):.1f} "
        f"len_major={len1:.3f} len_minor={len2:.3f} bbox_w={max(xs)-min(xs):.3f} bbox_h={max(ys)-min(ys):.3f}")
_q=[28,25,17,16]; _i=[0]; _d=[False]
def tick():
    if _d[0]: return None
    if _i[0]>=len(_q): _d[0]=True; log("DONE"); bpy.ops.wm.quit_blender(); return None
    bidx=_q[_i[0]]; _i[0]+=1
    win,area,region,rv3d=gv()
    if rv3d is None: _i[0]-=1; return 0.5
    ov={'window':win,'area':area,'region':region}
    try: proc(bidx,ov,region,rv3d)
    except Exception as e: log("ERR",bidx,e)
    return 0.05
bpy.app.timers.register(tick,first_interval=2.0); log("[init]")
