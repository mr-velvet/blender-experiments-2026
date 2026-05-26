"""06: monta um ROSTO num cubo carimbando VDM brushes reais nas coordenadas
faciais (2 olhos, 1 nariz, 1 boca) e renderiza.

Mecanica validada nos passos 03-05:
  - GUI dirigida por timer (viewport 3D inicializado, sem crash)
  - stroke ANCHORED com drag-zero = carimbo limpo
  - temp_override da view3d em todos os ops do timer

A face do cubo que recebe o rosto e a +Y (olhando -Y). Carimbamos cada parte
no ponto 3D correspondente da superficie, projetado pra 2D pra alimentar o stroke.

Config (editar BRUSHES/SPOTS conforme deliberacao do catalogo):
  SPOTS: (x, z) no plano da face +Y (y fixo ~1.0), tamanho em px, brush idx.
"""
import bpy, os, sys
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF = os.path.join(OUT, "06_log.txt")

# ---- DELIBERACAO: qual brush e cada parte + onde carimbar ----
# preenchido apos ver catalogo limpo. placeholder inicial:
FACE_PLAN = [
    # nome,        brush_idx, x,     z,     size_px
    ("olho_esq",   25,        -0.42,  0.32, 62),
    ("olho_dir",   25,         0.42,  0.32, 62),
    ("nariz",      23,         0.00, -0.05, 78),
    ("boca",       21,         0.00, -0.48, 88),
]
FACE_Y = 1.0  # face +Y do cubo size=2 esta em y=1

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
    nw=set(bpy.data.brushes.keys())-before
    b=bpy.data.brushes[list(nw)[0]]
    if b.texture and b.texture.image: b.texture.image.colorspace_settings.name='Non-Color'
    return b

def build():
    win,area,region,rv3d=get_view3d()
    ov={'window':win,'area':area,'region':region}

    # cubo denso
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=get_view3d(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="Face"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7   # cubo bem denso
        bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"[cube] verts={len(obj.data.vertices)}")

    # vista olhando a face +Y de frente (camera em -Y olhando +Y)
    # quaternion pra olhar ao longo de +Y: rotacao que aponta -Z view pra +Y world
    view_q = Vector((0,0,0))  # placeholder
    rv3d.view_rotation = (0.7071, 0.7071, 0.0, 0.0)  # olhar +Y de frente (frontal)
    rv3d.view_perspective='ORTHO'
    bpy.context.view_layer.update()

    from bpy_extras.view3d_utils import location_3d_to_region_2d
    # checa projecao
    test=location_3d_to_region_2d(region, rv3d, Vector((0,FACE_Y,0)))
    log(f"[proj] centro face +Y -> {test}")

    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt

        for name, bidx, x, z, size, rot in FACE_PLAN:
            brush=load_brush(bidx); ts.brush=brush
            try: brush.texture_slot.map_mode='AREA_PLANE'
            except: pass
            world=Vector((x, FACE_Y, z))
            p2d=location_3d_to_region_2d(region, rv3d, world)
            if p2d is None:
                log(f"[{name}] PROJ_FAIL"); continue
            stroke=[
                {"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,
                 "is_start":True,"location":tuple(world),"size":float(size),"pressure":1.0,
                 "time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,
                 "is_start":False,"location":tuple(world),"size":float(size),"pressure":1.0,
                 "time":0.02,"x_tilt":0,"y_tilt":0},
            ]
            zmax0=max(v.co.y for v in obj.data.vertices)
            bpy.ops.sculpt.brush_stroke(stroke=stroke, mode='NORMAL')
            zmax1=max(v.co.y for v in obj.data.vertices)
            log(f"[{name}] brush{bidx} @({x},{z}) y_max {zmax0:.3f}->{zmax1:.3f}")
        bpy.ops.object.mode_set(mode='OBJECT')

    # material clay claro
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.82,0.74,0.66,1); bb.inputs["Roughness"].default_value=0.55
    obj.data.materials.clear(); obj.data.materials.append(mat)
    with bpy.context.temp_override(**ov):
        obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.shade_smooth()

    # cena de render: camera frontal olhando a face +Y
    sc=bpy.context.scene
    cd=bpy.data.cameras.new("RC"); cam=bpy.data.objects.new("RC",cd)
    cam.location=(0,-5.0,0.0)
    d=cam.location-Vector((0,1.0,-0.05)); cam.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(cam); sc.camera=cam
    key=bpy.data.lights.new("K",type='AREA'); key.energy=600; key.size=4
    ko=bpy.data.objects.new("K",key); ko.location=(-3,-4,3)
    ko.rotation_euler=(Vector((-3,-4,3))-Vector((0,1,0))).to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(ko)
    rim=bpy.data.lights.new("R",type='AREA'); rim.energy=300; rim.size=3
    ro=bpy.data.objects.new("R",rim); ro.location=(3,-3,-1)
    ro.rotation_euler=(Vector((3,-3,-1))-Vector((0,1,0))).to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(ro)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.07,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=1.0; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=96
    sc.render.resolution_x=800; sc.render.resolution_y=800

    outp=os.path.join(OUT,"face_front.png")
    sc.render.filepath=outp
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"[render] {outp}")

    # vista 3/4
    cam.location=(3.2,-4.0,1.2)
    d=cam.location-Vector((0,1.0,0)); cam.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    outp2=os.path.join(OUT,"face_3q.png"); sc.render.filepath=outp2
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"[render] {outp2}")

    # salvar blend
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"face.blend"))
    log("[saved] face.blend")

_done=[False]
def tick():
    if _done[0]: return None
    _done[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR", traceback.format_exc())
    bpy.ops.wm.quit_blender()
    return None

bpy.app.timers.register(tick, first_interval=2.0)
log("[init] face builder")
