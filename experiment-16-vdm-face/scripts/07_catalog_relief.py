"""07: re-renderiza os 30 brushes ja catalogados (reusa as MESHES? nao — recarimba)
com iluminacao que revela relevo de verdade: vista de topo + luz rasante dura
lateral, fundo escuro. Sombra longa = forma legivel. Gera mosaico.

Reaproveita a logica do 04 mas so muda camera/luz e mantem stroke drag-zero.
"""
import bpy, os
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\relief"
LOGF = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\07_log.txt"
os.makedirs(OUT, exist_ok=True)
logbuf=[]
def log(*a):
    logbuf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(logbuf))

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
    for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
    for b in list(bpy.data.brushes):
        if b.name.startswith("Human Face VDM") and b.users==0: bpy.data.brushes.remove(b)

def ensure_scene():
    sc=bpy.context.scene
    if "C" not in bpy.data.objects:
        cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
        cd.type='ORTHO'; cd.ortho_scale=2.2; cam.location=(0,0,5)
        cam.rotation_euler=(0,0,0)  # topo puro
        sc.collection.objects.link(cam); sc.camera=cam
    if "S" not in bpy.data.objects:
        sd=bpy.data.lights.new("S",type='SUN'); sd.energy=4.0; sd.angle=0.02
        s=bpy.data.objects.new("S",sd)
        # luz bem rasante vindo de cima-esquerda (sombra longa revela relevo)
        s.rotation_euler=(1.35,0.0,0.6); sc.collection.objects.link(s)
    if sc.world is None:
        w=bpy.data.worlds.new("W"); w.use_nodes=True
        w.node_tree.nodes["Background"].inputs[0].default_value=(0.02,0.02,0.03,1)
        w.node_tree.nodes["Background"].inputs[1].default_value=0.15; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=32
    sc.render.resolution_x=300; sc.render.resolution_y=300

def proc(i,ov,region,rv3d):
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
        stroke=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":110.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":110.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT')
    ensure_scene()
    mat=bpy.data.materials.new("c"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.85,0.85,0.85,1); bb.inputs["Roughness"].default_value=0.9
    obj.data.materials.clear(); obj.data.materials.append(mat)
    with bpy.context.temp_override(**ov):
        obj.select_set(True); bpy.context.view_layer.objects.active=obj; bpy.ops.object.shade_smooth()
    outp=os.path.join(OUT,f"r_{i:02d}.png"); bpy.context.scene.render.filepath=outp
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"[{i}] ok")

_i=[0]; _d=[False]
def tick():
    if _d[0]: return None
    i=_i[0]+1
    if i>30: _d[0]=True; log("DONE"); bpy.ops.wm.quit_blender(); return None
    _i[0]=i
    win,area,region,rv3d=get_view3d()
    if rv3d is None: log(f"[{i}] NO_RV3D"); _i[0]=i-1; return 0.5
    ov={'window':win,'area':area,'region':region}
    try: proc(i,ov,region,rv3d)
    except Exception as e: log(f"[{i}] ERR {e}")
    return 0.1
bpy.app.timers.register(tick,first_interval=2.0); log("[init]")
