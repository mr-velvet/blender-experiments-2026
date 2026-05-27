"""35: carimba uma LISTA de brushes candidatos, cada um isolado numa malha,
recorta em disco, e renderiza em 3/4 (perfil revela protrusao real). Monta tudo
num grid pra eu escolher candidatos de olho/nariz/boca com variedade.

Diferente do catalogo top-down (so revela contorno): aqui a vista 3/4 mostra
QUANTO cada feature protrui pra fora — exatamente o criterio do user ('mais saltado').

Tambem testa o flip do displacement nas bocas (BOCA_FLIP): as bocas do pack sao
concavas (afundam), entao inverto o delta-Z local pra ver se viram labio saltado.

Env: CAND_LIST = csv de indices (ex '1,7,28,30'); CAND_FLIP='1' inverte Z;
     CAND_TAG = nome do mosaico.
"""
import bpy, os, math, bmesh
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\cand"
os.makedirs(OUT,exist_ok=True)
LIST=[int(x) for x in os.environ.get("CAND_LIST","25").split(",") if x.strip()]
FLIP=os.environ.get("CAND_FLIP","0")=="1"
RADIUS=float(os.environ.get("CAND_RADIUS","0.55"))
TAG=os.environ.get("CAND_TAG","cand")
LOGF=os.path.join(OUT,f"{TAG}.txt")
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

def stamp_one(idx, ov, region, rv3d):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active; obj.name=f"b{idx}"
        m=obj.modifiers.new("s","SUBSURF"); m.subdivision_type='SIMPLE'; m.levels=8
        bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    brush=load_brush(idx)
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
    bm=bmesh.new(); bm.from_mesh(obj.data)
    to_del=[v for v in bm.verts if (v.co.x*v.co.x+v.co.y*v.co.y) > rcut*rcut]
    bmesh.ops.delete(bm, geom=to_del, context='VERTS')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    if FLIP:  # inverte o relevo: concavo -> convexo
        me=obj.data
        for v in me.vertices: v.co.z = -v.co.z
        me.update()
    zmax=max(v.co.z for v in obj.data.vertices); zmin=min(v.co.z for v in obj.data.vertices)
    log(f"b{idx} z[{zmin:.3f},{zmax:.3f}] flip={FLIP}")
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.shade_smooth()
    return obj

def render_3q(obj, idx):
    sc=bpy.context.scene
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    obj.data.materials.clear(); obj.data.materials.append(mat)
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam
    cd.type='ORTHO'; cd.ortho_scale=1.5
    loc=Vector((0,-1.9,1.5)); cam.location=loc
    cam.rotation_euler=(loc-Vector((0,0,0.1))).to_track_quat('Z','Y').to_euler()
    sc.render.engine='CYCLES'; sc.cycles.samples=36
    sc.render.resolution_x=400; sc.render.resolution_y=400
    p=os.path.join(OUT,f"{TAG}_b{idx}.png")
    sc.render.filepath=p
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    return p

def build():
    for idx in LIST:
        win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
        with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
        win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
        # luz rasante
        sc=bpy.context.scene
        kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.5; kd.angle=0.1
        k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(40),0,math.radians(10)); sc.collection.objects.link(k)
        w=bpy.data.worlds.new("W"); w.use_nodes=True
        w.node_tree.nodes["Background"].inputs[0].default_value=(0.07,0.07,0.08,1)
        w.node_tree.nodes["Background"].inputs[1].default_value=0.4; sc.world=w
        obj=stamp_one(idx, ov, region, rv3d)
        render_3q(obj, idx)
        log(f"[rendered b{idx}]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=1.5)
