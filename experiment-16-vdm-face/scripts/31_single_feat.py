"""31: carimba UM brush, opcionalmente rotaciona o objeto, e renderiza top-down.
Um processo por chamada (robusto, sem crash por acumulo de estado).

Args via env:
  FEAT_BRUSH = indice do brush (ex 25)
  FEAT_RADIUS = raio (ex 0.55)
  FEAT_ROT = rotacao Z em graus aplicada ao objeto antes do render (ex 90)
  FEAT_MIRROR = "1" pra espelhar em X
  FEAT_OUT = nome do png de saida (sem extensao)
"""
import bpy, os, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\orient_diag"
os.makedirs(OUT,exist_ok=True)
BIDX=int(os.environ.get("FEAT_BRUSH","25"))
RADIUS=float(os.environ.get("FEAT_RADIUS","0.55"))
ROT=float(os.environ.get("FEAT_ROT","0"))
MIRROR=os.environ.get("FEAT_MIRROR","0")=="1"
NAME=os.environ.get("FEAT_OUT",f"feat_b{BIDX}")
LOGF=os.path.join(OUT,f"{NAME}.txt")
def log(*a): open(LOGF,"a",encoding="utf-8").write(" ".join(str(x) for x in a)+"\n")

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

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}

    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active; obj.name="feat"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=8; bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    brush=load_brush(BIDX)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        ups=bpy.context.scene.tool_settings.unified_paint_settings
        ups.use_locked_size='SCENE'; ups.use_unified_size=True; ups.unprojected_radius=RADIUS
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
        st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT')
    rcut=RADIUS*1.05
    import bmesh
    bm=bmesh.new(); bm.from_mesh(obj.data)
    to_del=[v for v in bm.verts if (v.co.x*v.co.x+v.co.y*v.co.y) > rcut*rcut]
    bmesh.ops.delete(bm, geom=to_del, context='VERTS')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

    # rotaciona/espelha o OBJETO
    sx=-1.0 if MIRROR else 1.0
    obj.scale=(sx,1,1)
    obj.rotation_euler=(0,0,math.radians(ROT))
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

    # material + smooth
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    obj.data.materials.clear(); obj.data.materials.append(mat)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.shade_smooth()

    sc=bpy.context.scene
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.5; kd.angle=0.05
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(35),0,0); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.0; fd.angle=0.6
    fo=bpy.data.objects.new("F",fd); fo.rotation_euler=(math.radians(20),0,math.radians(180)); sc.collection.objects.link(fo)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.06,0.07,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.4; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam
    CAM=os.environ.get("FEAT_CAM","top")
    if CAM=="3q":
        cd.type='ORTHO'; cd.ortho_scale=1.6
        loc=Vector((0,-2.2,2.2)); cam.location=loc
        cam.rotation_euler=(loc-Vector((0,0,0))).to_track_quat('Z','Y').to_euler()
    else:
        cd.type='ORTHO'; cd.ortho_scale=1.5
        cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
    sc.render.engine='CYCLES'; sc.cycles.samples=40
    sc.render.resolution_x=440; sc.render.resolution_y=440
    sc.render.filepath=os.path.join(OUT,f"{NAME}.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"done b{BIDX} rot={ROT} mirror={MIRROR}")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=1.5)
