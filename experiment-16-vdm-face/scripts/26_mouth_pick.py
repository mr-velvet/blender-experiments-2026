"""26: carimba bocas 15-18 e olhos 25 em tamanho controlado (unprojected_radius)
no plano, render frontal, pra eu escolher a boca mais horizontal e ver o olho."""
import bpy, os, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\pick"
os.makedirs(OUT,exist_ok=True)
LOGF=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\26_log.txt"
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
def ensure_scene():
    sc=bpy.context.scene
    if "C" not in bpy.data.objects:
        cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
        cd.type='ORTHO'; cd.ortho_scale=1.4; cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
        sc.collection.objects.link(cam); sc.camera=cam
    if "K" not in bpy.data.objects:
        kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.04
        k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(58),0,math.radians(20)); sc.collection.objects.link(k)
    if "F" not in bpy.data.objects:
        fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.1; fd.angle=0.6
        f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(35),0,math.radians(-150)); sc.collection.objects.link(f)
    if sc.world is None:
        w=bpy.data.worlds.new("W"); w.use_nodes=True
        w.node_tree.nodes["Background"].inputs[0].default_value=(0.08,0.08,0.09,1)
        w.node_tree.nodes["Background"].inputs[1].default_value=0.3; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=48; sc.render.resolution_x=300; sc.render.resolution_y=300
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
        ups=bpy.context.scene.tool_settings.unified_paint_settings
        ups.use_locked_size='SCENE'; ups.use_unified_size=True; ups.unprojected_radius=0.34
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
        st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_smooth()
    ensure_scene()
    mat=bpy.data.materials.new("c"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.6
    obj.data.materials.clear(); obj.data.materials.append(mat)
    outp=os.path.join(OUT,f"b{bidx:02d}.png"); bpy.context.scene.render.filepath=outp
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"b{bidx} ok")
_q=[15,16,17,18,25]; _i=[0]; _d=[False]
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
