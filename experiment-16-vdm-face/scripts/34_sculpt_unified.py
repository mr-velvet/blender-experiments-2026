"""34: rosto VDM esculpido DIRETO numa unica malha (sem placas/recorte).

Mudanca de approach pedida pelo user: em vez de carimbar cada feature numa placa
separada, recortar em disco e juntar (o que deixava olho/boca chapados e parecendo
furar a malha), aqui ENTRO EM SCULPT MODE uma vez numa malha bem subdividida e
carimbo as 4 features em coordenadas diferentes da MESMA malha. O brush VDM desloca
a massa existente PRA FORA -> relevo continuo, sem furos nem degraus.

Problemas resolvidos:
- Encolhimento ao carimbar varias features na mesma malha: reseto unprojected_radius
  ANTES de cada stroke (a 1a nao define mais a escala das seguintes).
- Mira de cada carimbo: converto a coord 3D do alvo na malha pra coord 2D da regiao
  (location_3d_to_region_2d) e dou o stroke ANCHORED ali.
- Rotacao do olho a 90deg (confirmado pelo user) sem encolher o stamp: em vez de
  girar textura/view (que encolhe), giro a MALHA 90deg em Z antes do stroke do olho
  e desfaco depois -> o carimbo fica rotacionado relativo a malha, em tamanho cheio.

Params via env: MOUTH_BRUSH (default 15), TAG.
"""
import bpy, os, math
from mathutils import Vector, Matrix
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
MOUTH=int(os.environ.get("MOUTH_BRUSH","15"))
TAG=os.environ.get("TAG",f"sc_m{MOUTH}")
LOGF=os.path.join(OUT,f"34_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# nome, brush, raio(mundo), pos(x,y) na malha, rot_da_malha_em_Z(graus). A rotacao
# da malha gira o carimbo relativo a malha SEM encolher (ao contrario de girar view).
MOUTH_ROT=float(os.environ.get("MOUTH_ROT","0"))
FEATURES=[
    ["nariz",   28, 0.40, ( 0.00, -0.04),   0],
    ["olho_esq",25, 0.46, (-0.42,  0.40),  90],   # 90deg = olho horizontal anatomico
    ["olho_dir",25, 0.46, ( 0.42,  0.40), -90],
    ["boca",  MOUTH, 0.42, ( 0.00, -0.56), MOUTH_ROT],
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

def stamp(obj,name,bidx,radius,pos,rot_mesh,ov,region,rv3d):
    """Carimba 1 feature na malha 'obj' (ja em sculpt mode). rot_mesh gira a malha
    em Z antes do stroke pra orientar o carimbo, e desfaz depois."""
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    # gira a malha em torno do ponto-alvo (no plano XY) por rot_mesh, no espaco do
    # objeto. Roda a geometria de modo que o carimbo (sempre top-down) caia rotacionado.
    px,py=pos
    if rot_mesh:
        bpy.ops.object.mode_set(mode='OBJECT')
        ang=math.radians(rot_mesh)
        piv=Vector((px,py,0))
        R=(Matrix.Translation(piv) @ Matrix.Rotation(ang,4,'Z') @ Matrix.Translation(-piv))
        me=obj.data
        for v in me.vertices: v.co=R @ v.co
        me.update()
        bpy.ops.object.mode_set(mode='SCULPT')

    brush=load_brush(bidx)
    ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
    ups=bpy.context.scene.tool_settings.unified_paint_settings
    ups.use_locked_size='SCENE'; ups.use_unified_size=True
    ups.unprojected_radius=radius   # reset ANTES de cada stroke -> sem encolher
    try: brush.texture_slot.map_mode='AREA_PLANE'
    except: pass
    # alvo no mundo: depois de girar a malha, o ponto que era (px,py) agora esta no
    # centro de rotacao (piv) -> miramos no piv (ele nao se move sob rotacao em torno de si).
    target=Vector((px,py,0))
    c=location_3d_to_region_2d(region,rv3d,target)
    st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
        {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
    bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')

    if rot_mesh:  # desfaz a rotacao da malha pra proxima feature partir do estado base
        bpy.ops.object.mode_set(mode='OBJECT')
        ang=-math.radians(rot_mesh)
        piv=Vector((px,py,0))
        R=(Matrix.Translation(piv) @ Matrix.Rotation(ang,4,'Z') @ Matrix.Translation(-piv))
        me=obj.data
        for v in me.vertices: v.co=R @ v.co
        me.update()
        bpy.ops.object.mode_set(mode='SCULPT')
    zmax=max(v.co.z for v in obj.data.vertices); zmin=min(v.co.z for v in obj.data.vertices)
    log(f"  stamp {name} b{bidx} r={radius} pos={pos} rotmesh={rot_mesh} z[{zmin:.3f},{zmax:.3f}]")

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}

    # UMA malha de barro, bem densa (multires nao -> aplico subsurf alto pra ter
    # resolucao uniforme suficiente pro VDM deslocar liso)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        clay=bpy.context.view_layer.objects.active; clay.name="Clay"
        m=clay.modifiers.new("s","SUBSURF"); m.subdivision_type='SIMPLE'; m.levels=9
        bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"clay verts={len(clay.data.vertices)}")

    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()

    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); clay.select_set(True)
        bpy.context.view_layer.objects.active=clay
        bpy.ops.object.mode_set(mode='SCULPT')
        for name,bidx,radius,pos,rotm in FEATURES:
            with bpy.context.temp_override(**ov):
                stamp(clay,name,bidx,radius,pos,rotm,ov,region,rv3d)
        bpy.ops.object.mode_set(mode='OBJECT')

    # suaviza levemente (so pra tirar micro-degrau de quantizacao do stamp), sem
    # matar volume
    sm=clay.modifiers.new("smooth","SMOOTH"); sm.factor=0.4; sm.iterations=4
    with bpy.context.temp_override(**ov): bpy.ops.object.modifier_apply(modifier=sm.name)
    with bpy.context.temp_override(**ov): bpy.ops.object.shade_smooth()

    # planta a placa numa face de um CUBO (pedido literal do user)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"
        bpy.ops.object.shade_flat()
    clay.rotation_euler=(math.radians(90),0,0)
    clay.scale=(0.95,0.95,0.95)
    clay.location=(0,-1.0-0.001,0.0)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); clay.select_set(True)
        bpy.context.view_layer.objects.active=clay
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    for o in (cube,clay): o.data.materials.clear(); o.data.materials.append(mat)

    sc=bpy.context.scene
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.5
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(35),0,math.radians(15)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.3; fd.angle=0.8
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(20),0,math.radians(-150)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.08,0.08,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.45; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam; cd.lens=55
    sc.render.engine='CYCLES'; sc.cycles.samples=48
    sc.render.resolution_x=800; sc.render.resolution_y=800

    # PRIMEIRO: prints de viewport (sem render Cycles) - pra confirmar relevo SAINDO
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='STUDIO'; sp.shading.color_type='SINGLE'
    sp.shading.single_color=(0.85,0.78,0.7)
    sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=1.6; sp.shading.cavity_valley_factor=1.6
    sp.shading.show_shadows=True
    try: sp.shading.shadow_intensity=0.5
    except: pass
    sp.overlay.show_overlays=False
    sc.render.resolution_x=700; sc.render.resolution_y=700

    def vp(name, setup):
        setup()
        bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"sc_{TAG}_vp_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        log(f"[viewport {name}] ok")

    def s_front():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=5.0; rv3d.view_perspective='ORTHO'
    def s_3q():
        from mathutils import Euler as _E
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        base_q=rv3d.view_rotation.copy()
        q=(_E((math.radians(20),0,math.radians(-35)),'XYZ').to_quaternion() @ base_q)
        rv3d.view_rotation=q; rv3d.view_perspective='PERSP'
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=6.5
    def s_side():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='LEFT')
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=6.5; rv3d.view_perspective='PERSP'

    vp("3q", s_3q)
    vp("front", s_front)
    vp("side", s_side)

    # DEPOIS: render simples (sem alta, samples baixos) das mesmas vistas
    def shoot(name, loc, tgt):
        cam.location=loc
        cam.rotation_euler=(loc-tgt).to_track_quat('Z','Y').to_euler()
        sc.render.resolution_x=800; sc.render.resolution_y=800
        sc.render.filepath=os.path.join(OUT,f"sc_{TAG}_r_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
        log(f"[render {name}] ok")
    shoot("3q",   Vector((-2.6,-4.2,1.4)), Vector((0,-1.0,0.1)))
    shoot("front",Vector((0,-5.2,0.1)),    Vector((0,-1.0,0.1)))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"sc_{TAG}.blend")); log("[saved]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
