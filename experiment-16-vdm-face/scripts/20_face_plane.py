"""20: monta o ROSTO num PLANO (carimbando top-down, onde o VDM funciona).

Eixos do plano (top-down, vista olhando -Z):
  X = horizontal da face (esq/dir), Y = vertical da face (cima/baixo), Z = relevo (pra fora)

Layout facial (no plano XY):
  olho_esq (-X, +Y),  olho_dir (+X, +Y),  nariz (centro),  boca (centro, -Y)

Render: vista 3/4 de cima (como olhar uma mascara deitada na mesa de um angulo),
+ uma vista frontal-da-face (camera olhando -Z reto, mas com luz rasante).
texture_slot.angle por feature pra orientar (a editar entre runs).
"""
import bpy, os, sys, math
from mathutils import Vector, Euler
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG=sys.argv[-1] if len(sys.argv)>1 and not sys.argv[-1].endswith(".py") else "p1"
LOGF=os.path.join(OUT,f"20_{TAG}.txt")
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# nome, brush, x, y (no plano), size_px, angle_deg
FACE_PLAN=[
    ("olho_esq",25,-0.42, 0.34,150, 0),
    ("olho_dir",25, 0.42, 0.34,150, 0),
    ("nariz",   28, 0.00, 0.00,170, 0),
    ("boca",    17, 0.00,-0.46,160, 0),
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

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active; obj.name="Face"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=8  # denso pra detalhe fino
        bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"[plane] verts={len(obj.data.vertices)}")
    # top-down exato pra carimbar
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'
    rv3d.view_distance=2.6; rv3d.view_location=(0,0,0); bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt
        for name,bidx,x,y,size,ang in FACE_PLAN:
            brush=load_brush(bidx); ts.brush=brush
            try: brush.texture_slot.map_mode='AREA_PLANE'
            except: pass
            brush.texture_slot.angle=math.radians(ang)
            world=Vector((x,y,0))
            p2d=location_3d_to_region_2d(region,rv3d,world)
            if p2d is None: log(f"[{name}] PROJFAIL"); continue
            st=[{"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,"is_start":True,"location":tuple(world),"size":float(size),"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,"is_start":False,"location":tuple(world),"size":float(size),"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
            z0=max(v.co.z for v in obj.data.vertices)
            bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')
            z1=max(v.co.z for v in obj.data.vertices)
            log(f"[{name}] b{bidx} @({x},{y}) ang={ang} zmax {z0:.3f}->{z1:.3f}")
        bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_smooth()
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.6
    obj.data.materials.clear(); obj.data.materials.append(mat)

    sc=bpy.context.scene
    # vista FRONTAL da face (olhando o plano de cima, reto) com luz rasante
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    cd.type='ORTHO'; cd.ortho_scale=2.1; cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
    sc.collection.objects.link(cam); sc.camera=cam
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.04
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(58),0,math.radians(20))
    sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.1; fd.angle=0.6
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(35),0,math.radians(-150))
    sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.07,0.07,0.08,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.3; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=64
    sc.render.resolution_x=800; sc.render.resolution_y=800
    sc.render.filepath=os.path.join(OUT,f"face_{TAG}_front.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[front] ok")
    # vista 3/4: inclina a camera
    cam.location=(1.3,-2.6,3.2); cam.rotation_euler=(cam.location-Vector((0,0,0))).to_track_quat('Z','Y').to_euler()
    sc.render.filepath=os.path.join(OUT,f"face_{TAG}_3q.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[3q] ok")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"face_{TAG}.blend")); log("[saved]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0)
log(f"[init] {TAG}")
