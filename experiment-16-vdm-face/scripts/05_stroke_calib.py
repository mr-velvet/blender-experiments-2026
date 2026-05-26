"""05: calibra o stroke ANCHORED do VDM pra sair limpo (sem rastro cometa).

Testa varias mecanicas num plano com o brush 01 (nariz, forma assimetrica facil
de ver distorcao). Renderiza cada variante. Escolho a que da carimbo limpo.

Variantes:
  A: 1 ponto so (is_start=True apenas)
  B: 2 pontos, drag curtissimo (raio pequeno em px)
  C: 2 pontos, mesmo mouse xy nos dois (drag zero)
  D: anchored com size grande e drag medio na vertical
"""
import bpy, os
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\calib"
LOGF = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\05_log.txt"
os.makedirs(OUT, exist_ok=True)
logbuf=[]
def log(*a):
    logbuf.append(" ".join(str(x) for x in a))
    open(LOGF,"w",encoding="utf-8").write("\n".join(logbuf))

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

def wipe(ov):
    with bpy.context.temp_override(**ov):
        if bpy.context.mode!='OBJECT':
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except: pass
    for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)

def ensure_scene():
    sc=bpy.context.scene
    if "C" not in bpy.data.objects:
        cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
        cd.type='ORTHO'; cd.ortho_scale=2.5; cam.location=(0,-1.4,2.6)
        d=cam.location-Vector((0,0,0.15)); cam.rotation_euler=d.to_track_quat('Z','Y').to_euler()
        sc.collection.objects.link(cam); sc.camera=cam
    if "S" not in bpy.data.objects:
        sd=bpy.data.lights.new("S",type='SUN'); sd.energy=2.2; sd.angle=0.05
        s=bpy.data.objects.new("S",sd); s.rotation_euler=(1.15,0,0.5); sc.collection.objects.link(s)
    if sc.world is None:
        w=bpy.data.worlds.new("W"); w.use_nodes=True
        w.node_tree.nodes["Background"].inputs[0].default_value=(0.5,0.52,0.55,1)
        w.node_tree.nodes["Background"].inputs[1].default_value=0.5; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=24
    sc.render.resolution_x=360; sc.render.resolution_y=360

def make_stroke(region, rv3d, variant):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
    def pt(mx,my,loc,start,t):
        return {"name":"","mouse":(mx,my),"mouse_event":(mx,my),"pen_flip":False,
                "is_start":start,"location":loc,"size":120.0,"pressure":1.0,"time":t,
                "x_tilt":0,"y_tilt":0}
    if variant=="A":
        return [pt(c.x,c.y,(0,0,0),True,0.0)]
    if variant=="B":
        return [pt(c.x,c.y,(0,0,0),True,0.0), pt(c.x+8,c.y,(0,0,0),False,0.02)]
    if variant=="C":
        return [pt(c.x,c.y,(0,0,0),True,0.0), pt(c.x,c.y,(0,0,0),False,0.02)]
    if variant=="D":
        return [pt(c.x,c.y,(0,0,0),True,0.0), pt(c.x,c.y-40,(0,0,0),False,0.05)]

def run_variant(v, idx, ov, region, rv3d):
    wipe(ov)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="P"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7
        bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'
    bpy.context.view_layer.update()
    brush=load_brush(idx)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        stroke=make_stroke(region,rv3d,v)
        try:
            bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'); res="OK"
        except Exception as e: res=f"FAIL {e}"
        bpy.ops.object.mode_set(mode='OBJECT')
    ensure_scene()
    mat=bpy.data.materials.new("c"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.8,0.73,0.64,1); bb.inputs["Roughness"].default_value=0.6
    obj.data.materials.clear(); obj.data.materials.append(mat)
    with bpy.context.temp_override(**ov):
        obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.shade_smooth()
    outp=os.path.join(OUT,f"var_{v}_brush{idx:02d}.png")
    bpy.context.scene.render.filepath=outp
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"[{v} b{idx}] {res}")

_q=[("A",1),("B",1),("C",1),("D",1),("A",15),("C",15),("A",30),("C",30)]
_i=[0]; _done=[False]
def tick():
    if _done[0]: return None
    if _i[0]>=len(_q):
        _done[0]=True; log("DONE"); bpy.ops.wm.quit_blender(); return None
    v,idx=_q[_i[0]]; _i[0]+=1
    win,area,region,rv3d=get_view3d()
    if rv3d is None: log("NO_RV3D"); _i[0]-=1; return 0.5
    ov={'window':win,'area':area,'region':region}
    try: run_variant(v,idx,ov,region,rv3d)
    except Exception as e: log(f"ERR {v} {idx}: {e}")
    return 0.1
bpy.app.timers.register(tick,first_interval=2.0)
log("[init] calib")
