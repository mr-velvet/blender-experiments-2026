"""38: CUBO com um OLHO carimbado em cada face, cada face com uma VARIACAO de
PROPRIEDADE DO PINCEL (nada de mexer na malha depois do carimbo).

Pedido do user (2026-05-27 noite):
- pegar um cubo, em cada face por o pincel de olho com uma diferenca de PROPRIEDADE
  do pincel (raio, strength, height...). So propriedade do pincel.
- numa das faces, por uma ESFERA no meio do olho (globo ocular) do tamanho do pincel.
- print de viewport antes de renderizar.

REGRA TRAVADA (apos feedback do user): SO carimbo VDM + SO propriedades do pincel.
ZERO manipulacao de vertice pos-carimbo (nada de v.co.z*=k, nada de flip). Se o
relevo do brush e raso, e raso.

Mecanica que funciona (herdada do 34):
- 1 plano denso por face, sculpt mode top-down, carimbo o olho b25.
- rotacao do olho a 90deg (anatomico, confirmado pelo user): giro a MALHA 90deg em Z
  antes do stroke e desfaco depois. Isso e ORIENTACAO rigida do carimbo, nao deforma.
- variacao por face = (unprojected_radius, strength, height, mesh_rot).
- planta cada plano na face correspondente do cubo, orientado pra fora.

Propriedades do brush VDM que controlam o relevo (do PROPRIO pincel, medidas no 37):
  strength (def 1.0)  -> intensidade do deslocamento
  height   (def 0.4)  -> altura do vector-displacement (protrusao real do pincel)
  unprojected_radius  -> tamanho

Env: TAG (def eyecube), SPHERE_FACE (qual face ganha a esfera, def 0).
"""
import bpy, os, math
from mathutils import Vector, Matrix, Euler
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG=os.environ.get("TAG","eyecube")
# uma ou varias faces ganham globo ocular. SPHERE_FACES csv (ex "0,2,4"); ou SPHERE_FACE unico.
_sf=os.environ.get("SPHERE_FACES", os.environ.get("SPHERE_FACE","0"))
SPHERE_FACES=set(int(x) for x in _sf.split(",") if x.strip()!="")
LOGF=os.path.join(OUT,f"38_{TAG}.txt")
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# 6 faces do cubo (size=2 -> faces em +-1). normal, "up" da face, rotacao euler da placa.
# A placa e gerada no plano XY com relevo +Z; rotacionamos pra alinhar +Z da placa com
# a normal da face. eye_rot = giro da malha (orientacao do olho) por face.
# variacao = (radius, strength, height) -> SO propriedade do pincel.
# variacao SO por propriedade do pincel: raio (tamanho) e strength (profundidade/relevo).
# height nao reescala VDM image-based (medido), entao nao varia por ele.
FACES=[
    # nome,      normal,        loc_offset,        euler_placa(rad),                       radius, strength, eye_rot
    ["+Y_frente",( 0, 1, 0),   ( 0, 1.001, 0),   (math.radians(-90),0,math.radians(180)), 0.50, 1.00,  90],
    ["-Y_tras",  ( 0,-1, 0),   ( 0,-1.001, 0),   (math.radians( 90),0,0),                 0.42, 1.00,  90],
    ["+X_dir",   ( 1, 0, 0),   ( 1.001,0, 0),    (math.radians(90),0,math.radians(90)),   0.36, 1.00,  90],
    ["-X_esq",   (-1, 0, 0),   (-1.001,0, 0),    (math.radians(90),0,math.radians(-90)),  0.58, 1.00,  90],
    ["+Z_topo",  ( 0, 0, 1),   ( 0,0, 1.001),    (0,0,0),                                 0.50, 0.55,  90],  # strength baixo = relevo sutil
    ["-Z_base",  ( 0, 0,-1),   ( 0,0,-1.001),    (math.radians(180),0,0),                 0.50, 1.00,   0],  # rot 0 = olho vertical (variacao de orientacao)
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

def make_eye_plate(name, radius, strength, eye_rot, ov, region, rv3d):
    """Cria um plano denso, entra em sculpt, carimba o olho b25 1x com as props dadas.
    Retorna o objeto. NAO mexe na malha alem do carimbo."""
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        plate=bpy.context.view_layer.objects.active; plate.name=name
        m=plate.modifiers.new("s","SUBSURF"); m.subdivision_type='SIMPLE'; m.levels=8
        bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    # orienta o olho girando a malha em Z ANTES de entrar em sculpt (orientacao rigida,
    # nao deforma; e a forma de orientar o carimbo sem encolher o stamp).
    if eye_rot:
        R=Matrix.Rotation(math.radians(eye_rot),4,'Z')
        for v in plate.data.vertices: v.co=R @ v.co
        plate.data.update()
    # garante active + selecionado em OBJECT mode, depois entra em SCULPT
    with bpy.context.temp_override(**ov):
        if bpy.context.object and bpy.context.object.mode!='OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
        bpy.context.view_layer.objects.active=plate
        bpy.ops.object.mode_set(mode='SCULPT')
    brush=load_brush(25)
    ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
    # PROPRIEDADES DO PINCEL (o ponto do experimento):
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
    if eye_rot:  # desfaz a rotacao da orientacao -> placa volta ao XY base
        R=Matrix.Rotation(-math.radians(eye_rot),4,'Z')
        for v in plate.data.vertices: v.co=R @ v.co
        plate.data.update()
    zmax=max(v.co.z for v in plate.data.vertices); zmin=min(v.co.z for v in plate.data.vertices)
    # centro do olho = ponto mais baixo (concavidade do globo) perto da origem
    cands=[v.co for v in plate.data.vertices if v.co.x**2+v.co.y**2 < (radius*0.5)**2]
    eye_center=min(cands,key=lambda c:c.z) if cands else Vector((0,0,0))
    log(f"  plate {name} r={radius} str={strength} rot={eye_rot} -> z[{zmin:.3f},{zmax:.3f}] center={tuple(round(x,3) for x in eye_center)}")
    return plate, zmax, eye_center.copy()

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    log(f"[build {TAG}] sphere_faces={sorted(SPHERE_FACES)}")

    # cubo base
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"; bpy.ops.object.shade_flat()

    plates=[]; sphere_targets=[]
    for i,(nm,normal,loc,euler,radius,strength,eye_rot) in enumerate(FACES):
        plate,zmax,eye_center=make_eye_plate(f"eye_{nm}",radius,strength,eye_rot,ov,region,rv3d)
        # planta na face: scale levemente <1 pra caber, rotaciona, posiciona
        sc_p=0.96
        plate.scale=(sc_p,sc_p,sc_p)
        plate.rotation_euler=Euler(euler,'XYZ')
        plate.location=Vector(loc)
        bpy.context.view_layer.update()
        if i in SPHERE_FACES:
            # transforma o centro do olho (coord local da placa) pra mundo usando a
            # matriz da placa ANTES de aplicar transform. Esse e o meio real do olho.
            wc=plate.matrix_world @ eye_center
            sphere_targets.append((nm, Vector(normal), wc.copy(), radius*sc_p))
        with bpy.context.temp_override(**ov):
            bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
            bpy.context.view_layer.objects.active=plate
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        plates.append(plate)
    log("plates plantadas:",len(plates))

    # ESFERA(S) no globo ocular: centro real do olho, raio ~ metade da abertura,
    # empurrada pela normal pra aflorar dentro da palpebra (globo visivel).
    spheres=[]
    for nm,normal,wc,eye_r in sphere_targets:
        sph_r=eye_r*0.38
        face_surf=normal*1.0
        spos=face_surf + Vector((wc.x-normal.x*1.0, wc.y-normal.y*1.0, wc.z-normal.z*1.0)) \
             + normal*(sph_r*0.65)
        with bpy.context.temp_override(**ov):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=sph_r, location=tuple(spos), segments=48, ring_count=24)
            s=bpy.context.view_layer.objects.active; s.name=f"Eyeball_{nm}"
            bpy.ops.object.shade_smooth()
        spheres.append(s)
        log(f"esfera (globo) na face {nm} r={sph_r:.3f} em {tuple(round(x,3) for x in spos)}")

    # materiais: barro pro cubo+placas, branco/iris pra esfera
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    for o in [cube]+plates: o.data.materials.clear(); o.data.materials.append(mat)
    if spheres:
        em=bpy.data.materials.new("eyeball"); em.use_nodes=True
        eb=em.node_tree.nodes.get("Principled BSDF")
        if eb: eb.inputs["Base Color"].default_value=(0.92,0.92,0.95,1); eb.inputs["Roughness"].default_value=0.25
        for s in spheres: s.data.materials.clear(); s.data.materials.append(em)

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
    sc.render.engine='CYCLES'; sc.cycles.samples=40

    # VIEWPORT (sem render) primeiro
    sp=area.spaces.active
    sp.shading.type='SOLID'; sp.shading.light='STUDIO'; sp.shading.color_type='SINGLE'
    sp.shading.single_color=(0.85,0.78,0.7)
    sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
    sp.shading.cavity_ridge_factor=1.8; sp.shading.cavity_valley_factor=1.8
    sp.shading.show_shadows=True
    try: sp.shading.shadow_intensity=0.5
    except: pass
    sp.overlay.show_overlays=False
    sc.render.resolution_x=720; sc.render.resolution_y=720

    def vp(name, setup):
        setup(); bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"38_{TAG}_vp_{name}.png")
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
    def s_top():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='TOP')
        rv3d.view_location=Vector((0,0,0)); rv3d.view_distance=6.0; rv3d.view_perspective='ORTHO'
    vp("3q", s_3q); vp("front", s_front); vp("top", s_top)

    # RENDER 3/4
    def shoot(name, loc, tgt):
        cam.location=loc; cam.rotation_euler=(loc-tgt).to_track_quat('Z','Y').to_euler()
        sc.render.resolution_x=800; sc.render.resolution_y=800
        sc.render.filepath=os.path.join(OUT,f"38_{TAG}_r_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
        log(f"[render {name}] ok")
    shoot("3q", Vector((4.5,-4.5,3.2)), Vector((0,0,0)))
    # close-up frontal da 1a face que tem esfera (olha a face de frente, perto)
    if sphere_targets:
        n=sphere_targets[0][1]
        shoot("eyeball", Vector(n)*4.2 + Vector((0,0,0.15)), Vector((0,0,0)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"38_{TAG}.blend")); log("[saved]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
