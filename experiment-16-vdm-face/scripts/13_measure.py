"""13: mede cada brush quantitativamente pra classificar (olho/nariz/boca/orelha).

Pra cada brush, carimba num plano denso e mede sobre os vertices DESLOCADOS:
  - z_max (altura da maior saliencia), z_min (profundidade da maior cavidade)
  - convex_frac: fracao de verts que subiram vs desceram (convexo vs concavo)
  - aspect: bbox XY da regiao deslocada (largura/altura) -> orientacao
  - centroid offset da regiao deslocada
Heuristica:
  - boca: z_min forte (concavo), z_max fraco
  - nariz: z_max forte e assimetrico (projecao)
  - orelha: z_max forte lateral
  - olho: relevo raso, leve convexo, forma amendoa
"""
import bpy, os, math
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF = os.path.join(OUT,"13_measure.txt")
buf=[]
def log(*a):
    buf.append("\t".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='VIEW_3D':
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                return win,area,region,area.spaces.active.region_3d
    return None,None,None,None

def load_brush(idx):
    fname=f"Human Face VDM {idx:02d}.asset.blend"; before=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,fname),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    b=bpy.data.brushes[list(set(bpy.data.brushes.keys())-before)[0]]
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

def measure(i,ov,region,rv3d):
    wipe(ov)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="P"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7; bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; bpy.context.view_layer.update()
    brush=load_brush(i)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        from bpy_extras.view3d_utils import location_3d_to_region_2d
        c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
        stroke=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT')
    zs=[v.co.z for v in obj.data.vertices]
    zmax=max(zs); zmin=min(zs)
    thr=0.01
    up=[v for v in obj.data.vertices if v.co.z> thr]
    dn=[v for v in obj.data.vertices if v.co.z< -thr]
    ntot=len(up)+len(dn)
    convex_frac = (len(up)/ntot) if ntot else 0
    # bbox da regiao deslocada (|z|>thr) -> orientacao
    act=[v for v in obj.data.vertices if abs(v.co.z)>thr]
    if act:
        xs=[v.co.x for v in act]; ys=[v.co.y for v in act]
        wdt=max(xs)-min(xs); hgt=max(ys)-min(ys)
        aspect = wdt/hgt if hgt>1e-4 else 99
        cx=sum(xs)/len(xs); cy=sum(ys)/len(ys)
    else:
        aspect=0; cx=cy=0; wdt=hgt=0
    # classificacao heuristica
    if zmin < -0.10 and zmax < 0.12:
        kind="BOCA"
    elif zmax > 0.30 and convex_frac>0.6:
        kind="NARIZ/ORELHA"
    elif abs(zmax)<0.15 and abs(zmin)<0.06 and convex_frac>0.55:
        kind="OLHO?"
    else:
        kind="?"
    log(i, f"zmax={zmax:.3f}", f"zmin={zmin:.3f}", f"cvx={convex_frac:.2f}",
        f"asp={aspect:.2f}", f"w={wdt:.2f}", f"h={hgt:.2f}", kind)

_i=[0]; _d=[False]
def tick():
    if _d[0]: return None
    i=_i[0]+1
    if i>30: _d[0]=True; log("DONE"); bpy.ops.wm.quit_blender(); return None
    _i[0]=i
    win,area,region,rv3d=get_view3d()
    if rv3d is None: _i[0]=i-1; return 0.5
    ov={'window':win,'area':area,'region':region}
    try: measure(i,ov,region,rv3d)
    except Exception as e: log(i,"ERR",e)
    return 0.05
if not buf: log("idx","metrics...")
bpy.app.timers.register(tick,first_interval=2.0)
