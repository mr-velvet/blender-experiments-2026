"""30: diagnostico de ORIENTACAO NATURAL de cada feature.

Carimba cada brush ISOLADO em roll 0 (top-down) num plano, recorta em disco,
e renderiza de frente (vista +Z, olhando -Z) com luz rasante. Salva um PNG por
feature. Objetivo: VER como cada brush sai sem rotacao nenhuma, pra eu decidir
o angulo certo de cada um — em vez de chutar.

Features diagnosticadas: olho b25, nariz b28, bocas 15/16/17/18.
Render individual de frente (top-down) = exatamente a orientacao em que o
brush e carimbado. Assim sei se a boca sai vertical/horizontal, se o olho sai
deitado, etc.
"""
import bpy, os, sys, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\orient_diag"
os.makedirs(OUT,exist_ok=True)
LOGF=os.path.join(OUT,"log.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# (label, brush_idx, radius)
TARGETS=[
    ("olho_b25", 25, 0.55),
    ("nariz_b28",28, 0.45),
    ("boca_b15", 15, 0.50),
    ("boca_b16", 16, 0.50),
    ("boca_b17", 17, 0.50),
    ("boca_b18", 18, 0.50),
]

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

def stamp_feature(name,bidx,radius,ov,region,rv3d):
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active; obj.name=f"feat_{name}"
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
        ups.use_locked_size='SCENE'; ups.use_unified_size=True; ups.unprojected_radius=radius
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
        st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(0,0,0),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL'); bpy.ops.object.mode_set(mode='OBJECT')
    rcut=radius*1.05
    import bmesh
    bm=bmesh.new(); bm.from_mesh(obj.data)
    to_del=[v for v in bm.verts if (v.co.x*v.co.x+v.co.y*v.co.y) > rcut*rcut]
    bmesh.ops.delete(bm, geom=to_del, context='VERTS')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    zmax=max(v.co.z for v in obj.data.vertices); zmin=min(v.co.z for v in obj.data.vertices)
    # bbox em XY pra medir aspect ratio (largura X vs altura Y) — diz orientacao
    xs=[v.co.x for v in obj.data.vertices if v.co.z>zmax*0.4 or v.co.z<zmin*0.4]
    ys=[v.co.y for v in obj.data.vertices if v.co.z>zmax*0.4 or v.co.z<zmin*0.4]
    spanx=(max(xs)-min(xs)) if xs else 0; spany=(max(ys)-min(ys)) if ys else 0
    log(f"  {name} b{bidx} z[{zmin:.3f},{zmax:.3f}] relief_spanX={spanx:.3f} relief_spanY={spany:.3f} (X>Y=horizontal)")
    return obj,zmin,zmax

def setup_render(sc):
    sc.render.engine='CYCLES'; sc.cycles.samples=48
    sc.render.resolution_x=480; sc.render.resolution_y=480

def render_feature(name, obj, ov):
    sc=bpy.context.scene
    # material clay
    mat=bpy.data.materials.get("clay") or bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    obj.data.materials.clear(); obj.data.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active=obj; bpy.ops.object.shade_smooth()
    setup_render(sc)
    sc.render.filepath=os.path.join(OUT,f"{name}.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"  rendered {name}")

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}

    sc=bpy.context.scene
    # luz rasante vinda de cima-frente (olhando top-down, "cima" da imagem = +Y)
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.5; kd.angle=0.05
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(35),0,math.radians(0)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.0; fd.angle=0.6
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(20),0,math.radians(180)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.06,0.07,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.4; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam; cd.type='ORTHO'; cd.ortho_scale=1.6
    # camera top-down: olha -Z, "cima" da imagem aponta +Y
    cam.location=(0,0,5); cam.rotation_euler=(0,0,0)

    for name,bidx,radius in TARGETS:
        obj,zmin,zmax=stamp_feature(name,bidx,radius,ov,region,rv3d)
        # esconde tudo menos este obj
        for o in bpy.data.objects:
            if o.type=='MESH': o.hide_render=(o is not obj)
        render_feature(name,obj,ov)
    log("[done]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log("[init]")
