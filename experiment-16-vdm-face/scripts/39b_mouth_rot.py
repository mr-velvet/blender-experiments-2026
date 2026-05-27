"""39: CUBO com uma BOCA VDM carimbada em cada face, cada face variando uma
PROPRIEDADE DO PINCEL (raio/strength). Mesmo metodo que funcionou no olho (script 38).

Pedido do user (2026-05-27):
- igual ao cubo de olhos, mas com BOCAS. Varias bocas diferentes, uma em cada face,
  com propriedades de protrusao variadas.
- garantir que a boca seja relevo CONTINUO da malha (protrusao natural), nao placa
  chumbada em cima.
- print de viewport antes de render; render em BAIXA resolucao.
- medir TEMPOS (subir blender, esculpir, renderizar) -> escrito no log.

REGRA TRAVADA: SO carimbo VDM + SO propriedades do pincel. ZERO manipulacao de
vertice pos-carimbo (nada de v.co.z, nada de flip, nada de pinçar malha). Se a boca
do pincel e rasa, ela e rasa — reporto honesto.

Mecanica (herdada do 34/38 que funciona):
- 1 plano denso por face, sculpt mode top-down, carimbo a boca 1x.
- planta o plano na face do cubo, orientado pra fora.
- a continuidade vem de esculpir na propria malha (sculpt mode), nao de colar objeto.

Bocas do pack: 15,16,17,18 (catalogadas como labio projetado). Variamos qual brush
+ raio + strength por face.
Env: TAG (def mouthcube).
"""
import bpy, os, math, time
from mathutils import Vector, Matrix, Euler
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG=os.environ.get("TAG","mouthcube")
LOGF=os.path.join(OUT,f"39_{TAG}.txt")
T0=time.time()
buf=[]
def log(*a):
    t=time.time()-T0
    buf.append(f"[{t:6.1f}s] "+" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# 6 faces. cada uma: nome, normal, loc_offset, euler_placa, BRUSH idx, radius, strength, mouth_rot
# mouth_rot = orientacao rigida do carimbo (giro da malha em Z antes do stroke, desfeito depois).
# A boca do pack sai como labio projetado; rot 0 deixa ela na orientacao canonica do brush.
# variacao = brush diferente + raio + strength.
FACES=[
    # nome,      normal,        loc_offset,        euler_placa(rad),                       brush, radius, strength, rot
    ["+Y_frente",( 0, 1, 0),   ( 0, 1.001, 0),   (math.radians(-90),0,math.radians(180)), 15, 0.52, 1.00,  90],
    ["-Y_tras",  ( 0,-1, 0),   ( 0,-1.001, 0),   (math.radians( 90),0,0),                 15, 0.52, 1.60,  90],
    ["+X_dir",   ( 1, 0, 0),   ( 1.001,0, 0),    (math.radians(90),0,math.radians(90)),   16, 0.52, 1.30,  90],
    ["-X_esq",   (-1, 0, 0),   (-1.001,0, 0),    (math.radians(90),0,math.radians(-90)),  17, 0.52, 1.30,  90],
    ["+Z_topo",  ( 0, 0, 1),   ( 0,0, 1.001),    (0,0,0),                                 18, 0.52, 1.30,  90],
    ["-Z_base",  ( 0, 0,-1),   ( 0,0,-1.001),    (math.radians(180),0,0),                 15, 0.52, 2.00,  90],  # strength 2.0 = max
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

def make_plate(name, brush_idx, radius, strength, rot, ov, region, rv3d):
    """Plano denso, sculpt mode, carimba a boca 1x. NAO mexe na malha alem do carimbo."""
    ts0=time.time()
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        plate=bpy.context.view_layer.objects.active; plate.name=name
        m=plate.modifiers.new("s","SUBSURF"); m.subdivision_type='SIMPLE'; m.levels=8
        bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    if rot:
        R=Matrix.Rotation(math.radians(rot),4,'Z')
        for v in plate.data.vertices: v.co=R @ v.co
        plate.data.update()
    with bpy.context.temp_override(**ov):
        if bpy.context.object and bpy.context.object.mode!='OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
        bpy.context.view_layer.objects.active=plate
        bpy.ops.object.mode_set(mode='SCULPT')
    brush=load_brush(brush_idx)
    ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
    brush.strength=strength
    ups=bpy.context.scene.tool_settings.unified_paint_settings
    ups.use_locked_size='SCENE'; ups.use_unified_size=True; ups.unprojected_radius=radius
    try: brush.texture_slot.map_mode='AREA_PLANE'
    except: pass
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    target=Vector((0,0,0)); c=location_3d_to_region_2d(region,rv3d,target)
    st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
        {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
    with bpy.context.temp_override(**ov):
        bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')
        bpy.ops.object.mode_set(mode='OBJECT')
    if rot:
        R=Matrix.Rotation(-math.radians(rot),4,'Z')
        for v in plate.data.vertices: v.co=R @ v.co
        plate.data.update()
    zmax=max(v.co.z for v in plate.data.vertices); zmin=min(v.co.z for v in plate.data.vertices)
    log(f"  plate {name} brush={brush_idx} r={radius} str={strength} -> z[{zmin:.3f},{zmax:.3f}] protrusao={zmax-zmin:.3f} ({time.time()-ts0:.1f}s)")
    return plate

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    log(f"[build {TAG}] (blender pronto em {time.time()-T0:.1f}s desde start do script)")

    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"; bpy.ops.object.shade_flat()

    t_sculpt=time.time()
    plates=[]
    for i,(nm,normal,loc,euler,brush,radius,strength,rot) in enumerate(FACES):
        plate=make_plate(f"mouth_{nm}",brush,radius,strength,rot,ov,region,rv3d)
        sc_p=0.96
        plate.scale=(sc_p,sc_p,sc_p)
        plate.rotation_euler=Euler(euler,'XYZ')
        plate.location=Vector(loc)
        bpy.context.view_layer.update()
        with bpy.context.temp_override(**ov):
            bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
            bpy.context.view_layer.objects.active=plate
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        plates.append(plate)
    log(f"[sculpt] 6 bocas carimbadas em {time.time()-t_sculpt:.1f}s")

    # material barro
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    for o in [cube]+plates: o.data.materials.clear(); o.data.materials.append(mat)

    sc=bpy.context.scene
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.5
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(40),0,math.radians(25)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.4; fd.angle=0.8
    fo=bpy.data.objects.new("F",fd); fo.rotation_euler=(math.radians(15),0,math.radians(-140)); sc.collection.objects.link(fo)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.08,0.08,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.5; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam; cd.lens=50
    sc.render.engine='CYCLES'; sc.cycles.samples=32

    # VIEWPORT (sem render)
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='STUDIO'; sp.shading.color_type='SINGLE'
    sp.shading.single_color=(0.85,0.78,0.7)
    sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=1.8; sp.shading.cavity_valley_factor=1.8
    sp.shading.show_shadows=True
    try: sp.shading.shadow_intensity=0.5
    except: pass
    sp.overlay.show_overlays=False
    sc.render.resolution_x=640; sc.render.resolution_y=640

    t_vp=time.time()
    def vp(name, setup):
        setup(); bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"39_{TAG}_vp_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        log(f"[vp {name}] ok")
    def s_3q():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        q=(Euler((math.radians(25),0,math.radians(-40)),'XYZ').to_quaternion() @ rv3d.view_rotation.copy())
        rv3d.view_rotation=q; rv3d.view_perspective='PERSP'
        rv3d.view_location=Vector((0,0,0)); rv3d.view_distance=7.5
    def s_front():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        rv3d.view_location=Vector((0,0,0)); rv3d.view_distance=6.0; rv3d.view_perspective='ORTHO'
    def s_side():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='RIGHT')
        rv3d.view_location=Vector((0,0,0)); rv3d.view_distance=6.0; rv3d.view_perspective='ORTHO'
    vp("3q", s_3q); vp("front", s_front); vp("side", s_side)
    log(f"[viewport] 3 prints em {time.time()-t_vp:.1f}s")

    # RENDER baixo
    t_r=time.time()
    def shoot(name, loc, tgt, res=480):
        cam.location=loc; cam.rotation_euler=(loc-tgt).to_track_quat('Z','Y').to_euler()
        sc.render.resolution_x=res; sc.render.resolution_y=res
        sc.render.filepath=os.path.join(OUT,f"39_{TAG}_r_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
        log(f"[render {name}] ok ({time.time()-t_r:.1f}s acumulado)")
    shoot("3q", Vector((4.5,-4.5,3.2)), Vector((0,0,0)))
    shoot("side", Vector((6.0,0,0.2)), Vector((0,0,0)))   # mostra a protrusao da frente de lado
    shoot("front", Vector((0,-6.0,0)), Vector((0,0,0)))
    log(f"[render] 3 renders baixos em {time.time()-t_r:.1f}s")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"39_{TAG}.blend"))
    log(f"[saved] TOTAL {time.time()-T0:.1f}s")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
