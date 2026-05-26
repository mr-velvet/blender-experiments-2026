"""14: monta o ROSTO no cubo carimbando as features identificadas na face +Y.

Features (identificadas no passo 12-13):
  olho = 25, nariz = 28, boca = 17

A face +Y do cubo (size 2 -> face em y=+1) recebe o rosto. Vista frontal:
camera em -Y olhando +Y. "Para cima" da feature deve ser +Z do mundo.

Carimbo via sculpt.brush_stroke ANCHORED drag-zero, com a VIEW posicionada
de frente pra face +Y (pra location_3d_to_region_2d projetar certo). A
orientacao de cada feature e ajustada por texture_slot.angle (parametro ANG
em cada item do plano). Tiro print da tela (viewport) e tambem salvo o blend.

Edite FACE_PLAN[*][ANG] entre execucoes ate as features ficarem em pe.
"""
import bpy, os, sys, math
from mathutils import Vector, Euler

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG = sys.argv[-1] if len(sys.argv)>1 and not sys.argv[-1].endswith(".py") else "v1"
LOGF = os.path.join(OUT, f"14_{TAG}.txt")
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# nome, brush, x, z (na face +Y), size_px, angle_deg, mirror_x
# sizes grandes: a face e 2x2, features precisam ocupar espaco real
FACE_PLAN = [
    ("olho_esq", 25, -0.45, 0.35, 150, 0,   False),
    ("olho_dir", 25,  0.45, 0.35, 150, 0,   True),
    ("nariz",    28,  0.00,-0.05, 170, 0,   False),
    ("boca",     17,  0.00,-0.55, 170, 0,   False),
]
FACE_Y = 1.0

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

def build():
    win,area,region,rv3d=get_view3d(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=get_view3d(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="Face"
        # SIMPLE subdivision: densifica mantendo forma de CUBO (faces planas)
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7; m.subdivision_type='SIMPLE'
        bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"[cube] verts={len(obj.data.vertices)}")

    # vista olhando a face +Y de frente: camera em -Y. view_rotation que poe
    # -Y como direcao de visao e +Z como up: rotacao X de -90 graus.
    rv3d.view_rotation = Euler((math.radians(90),0,0),'XYZ').to_quaternion()
    rv3d.view_perspective='ORTHO'; rv3d.view_distance=3.2; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    test=location_3d_to_region_2d(region, rv3d, Vector((0,FACE_Y,0)))
    log(f"[proj] centro face +Y -> {test}")
    # checa orientacao: +Z deve subir na tela
    pz=location_3d_to_region_2d(region, rv3d, Vector((0,FACE_Y,0.5)))
    log(f"[proj] +Z(0.5) -> {pz} (deve ter y MAIOR que centro)")

    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt
        for name,bidx,x,z,size,ang,mirror in FACE_PLAN:
            brush=load_brush(bidx); ts.brush=brush
            try: brush.texture_slot.map_mode='AREA_PLANE'
            except: pass
            a=ang
            brush.texture_slot.angle=math.radians(a)
            world=Vector((x, FACE_Y, z))
            p2d=location_3d_to_region_2d(region, rv3d, world)
            if p2d is None: log(f"[{name}] PROJ_FAIL"); continue
            stroke=[
                {"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,
                 "is_start":True,"location":tuple(world),"size":float(size),"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(p2d.x,p2d.y),"mouse_event":(p2d.x,p2d.y),"pen_flip":False,
                 "is_start":False,"location":tuple(world),"size":float(size),"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0},
            ]
            ymax0=max(v.co.y for v in obj.data.vertices)
            bpy.ops.sculpt.brush_stroke(stroke=stroke, mode='NORMAL')
            ymax1=max(v.co.y for v in obj.data.vertices)
            log(f"[{name}] b{bidx} @({x},{z}) ang={a} y_max {ymax0:.3f}->{ymax1:.3f}")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()

    # material clay
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.85,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.6
    obj.data.materials.clear(); obj.data.materials.append(mat)

    # ---- PRINT DA TELA (viewport OpenGL) com sombra + cavity ----
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='STUDIO'
    sp.shading.color_type='SINGLE'; sp.shading.single_color=(0.85,0.78,0.7)
    sp.shading.show_shadows=True
    try: sp.shading.shadow_intensity=0.5
    except: pass
    sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=2.0; sp.shading.cavity_valley_factor=2.0
    sp.overlay.show_overlays=False
    rv3d.view_rotation = Euler((math.radians(82),0,0),'XYZ').to_quaternion()
    rv3d.view_distance=3.0; bpy.context.view_layer.update()
    sc=bpy.context.scene
    sc.render.resolution_x=700; sc.render.resolution_y=700
    outp=os.path.join(OUT,f"face_{TAG}_viewport.png"); sc.render.filepath=outp
    with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
    log(f"[viewport] {outp}")

    # ---- DIAG Cycles: camera 3/4 enquadrando a face + key 45 + fill ----
    cd=bpy.data.cameras.new("RC"); cam=bpy.data.objects.new("RC",cd)
    cd.type='ORTHO'; cd.ortho_scale=2.6
    cam.location=(1.7,-3.4,1.1)             # 3/4 de frente-cima-direita
    aim=Vector((0,1.0,0.0))
    cam.rotation_euler=(cam.location-aim).to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(cam); sc.camera=cam
    # KEY a ~45 graus de cima-frente-esquerda (ilumina a face E cria sombra nas features)
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.03
    k=bpy.data.objects.new("K",kd)
    kdir=Vector((-0.7,-1.0,0.8))
    k.rotation_euler=(-kdir).to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.3; fd.angle=0.5
    f=bpy.data.objects.new("F",fd)
    f.rotation_euler=(-Vector((0.9,-1.0,0.3))).to_track_quat('Z','Y').to_euler()
    sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.06,0.07,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.25; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=48
    outp2=os.path.join(OUT,f"face_{TAG}_diag.png"); sc.render.filepath=outp2
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log(f"[diag] {outp2}")

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"face_{TAG}.blend"))
    log("[saved]")

_done=[False]
def tick():
    if _done[0]: return None
    _done[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR", traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick, first_interval=2.0)
log(f"[init] {TAG}")
