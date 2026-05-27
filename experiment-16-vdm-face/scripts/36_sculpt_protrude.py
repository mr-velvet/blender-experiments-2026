"""36: rosto VDM esculpido na MESMA malha (herda 34) + controle de PROTRUSAO e
brushes parametrizaveis por feature.

Novidades pedidas pelo user (2026-05-27):
- 'olhos e boca mais saltados pra fora': depois de esculpir tudo na mesma malha,
  multiplico o relevo positivo (Z>0) por PROTRUDE (>1 = mais saltado). So o que
  ja saiu pra fora cresce — nao distorce o plano, nao cria furo.
- testar outros olhos/narizes/bocas: EYE_BRUSH/NOSE_BRUSH/MOUTH_BRUSH via env.
- por-feature: posso dar mais protrusao so nos olhos via EYE_PROTRUDE (escala Z
  extra aplicada na regiao dos olhos depois).

Tudo continua esculpido numa unica malha densa (sculpt mode), entao nada fura:
o relevo brota da massa, igual o nariz sempre fez.

Env:
  EYE_BRUSH (def 25)  NOSE_BRUSH (def 28)  MOUTH_BRUSH (def 15)
  PROTRUDE (def 1.0)        multiplicador Z global do relevo positivo
  EYE_PROTRUDE (def 1.0)    multiplicador Z extra so na faixa dos olhos
  MOUTH_PROTRUDE (def 1.0)  multiplicador Z extra so na faixa da boca
  EYE_RADIUS NOSE_RADIUS MOUTH_RADIUS (raio do stamp = tamanho)
  TAG
"""
import bpy, os, math
from mathutils import Vector, Matrix
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
def F(k,d): return float(os.environ.get(k,d))
def I(k,d): return int(os.environ.get(k,d))
EYE_B=I("EYE_BRUSH",25); NOSE_B=I("NOSE_BRUSH",28); MOUTH_B=I("MOUTH_BRUSH",15)
PROTRUDE=F("PROTRUDE","1.0")
EYE_PROT=F("EYE_PROTRUDE","1.0"); MOUTH_PROT=F("MOUTH_PROTRUDE","1.0")
EYE_R=F("EYE_RADIUS","0.46"); NOSE_R=F("NOSE_RADIUS","0.40"); MOUTH_R=F("MOUTH_RADIUS","0.42")
TAG=os.environ.get("TAG",f"p_e{EYE_B}n{NOSE_B}m{MOUTH_B}")
LOGF=os.path.join(OUT,f"36_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# y dos olhos e da boca (pra escalar protrusao por regiao depois)
EYE_Y=0.40; MOUTH_Y=-0.56
FEATURES=[
    ["nariz",   NOSE_B, NOSE_R, ( 0.00, -0.04),   0],
    ["olho_esq",EYE_B,  EYE_R,  (-0.42,  EYE_Y),  90],
    ["olho_dir",EYE_B,  EYE_R,  ( 0.42,  EYE_Y), -90],
    ["boca",    MOUTH_B,MOUTH_R,( 0.00,  MOUTH_Y), 0],
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
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    px,py=pos
    if rot_mesh:
        bpy.ops.object.mode_set(mode='OBJECT')
        ang=math.radians(rot_mesh); piv=Vector((px,py,0))
        R=(Matrix.Translation(piv) @ Matrix.Rotation(ang,4,'Z') @ Matrix.Translation(-piv))
        for v in obj.data.vertices: v.co=R @ v.co
        obj.data.update(); bpy.ops.object.mode_set(mode='SCULPT')
    brush=load_brush(bidx)
    bpy.context.scene.tool_settings.sculpt.brush=brush
    ups=bpy.context.scene.tool_settings.unified_paint_settings
    ups.use_locked_size='SCENE'; ups.use_unified_size=True; ups.unprojected_radius=radius
    try: brush.texture_slot.map_mode='AREA_PLANE'
    except: pass
    target=Vector((px,py,0)); c=location_3d_to_region_2d(region,rv3d,target)
    st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
        {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":tuple(target),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
    bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')
    if rot_mesh:
        bpy.ops.object.mode_set(mode='OBJECT')
        ang=-math.radians(rot_mesh); piv=Vector((px,py,0))
        R=(Matrix.Translation(piv) @ Matrix.Rotation(ang,4,'Z') @ Matrix.Translation(-piv))
        for v in obj.data.vertices: v.co=R @ v.co
        obj.data.update(); bpy.ops.object.mode_set(mode='SCULPT')
    log(f"  stamp {name} b{bidx} r={radius} pos={pos} rotmesh={rot_mesh}")

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        clay=bpy.context.view_layer.objects.active; clay.name="Clay"
        m=clay.modifiers.new("s","SUBSURF"); m.subdivision_type='SIMPLE'; m.levels=9
        bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"clay verts={len(clay.data.vertices)} | eye_b{EYE_B} nose_b{NOSE_B} mouth_b{MOUTH_B} protrude={PROTRUDE} eyeP={EYE_PROT} mouthP={MOUTH_PROT}")
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); clay.select_set(True)
        bpy.context.view_layer.objects.active=clay; bpy.ops.object.mode_set(mode='SCULPT')
        for nm,bidx,radius,pos,rotm in FEATURES:
            with bpy.context.temp_override(**ov): stamp(clay,nm,bidx,radius,pos,rotm,ov,region,rv3d)
        bpy.ops.object.mode_set(mode='OBJECT')

    # --- BOCA FLIP opcional: o brush de boca e CONCAVO (afunda). Se MOUTH_FLIP=1,
    # inverto o Z negativo da faixa da boca pra ele saltar pra fora (virar labio). ---
    MOUTH_FLIP=os.environ.get("MOUTH_FLIP","0")=="1"
    me=clay.data
    if MOUTH_FLIP:
        for v in me.vertices:
            if abs(v.co.y-MOUTH_Y)<0.22 and v.co.z<0:
                v.co.z = -v.co.z
        me.update()
        log("boca FLIP aplicado")

    # --- PROTRUSAO: escala o relevo positivo. Global + por regiao ---
    for v in me.vertices:
        z=v.co.z
        if z>0:
            f=PROTRUDE
            # faixa dos olhos (em Y proximo de EYE_Y)
            if abs(v.co.y-EYE_Y)<0.30: f*=EYE_PROT
            # faixa da boca
            if abs(v.co.y-MOUTH_Y)<0.22: f*=MOUTH_PROT
            v.co.z = z*f
    me.update()
    zmax=max(v.co.z for v in me.vertices); zmin=min(v.co.z for v in me.vertices)
    log(f"apos protrude z[{zmin:.3f},{zmax:.3f}]")

    sm=clay.modifiers.new("smooth","SMOOTH"); sm.factor=0.4; sm.iterations=4
    with bpy.context.temp_override(**ov): bpy.ops.object.modifier_apply(modifier=sm.name)
    with bpy.context.temp_override(**ov): bpy.ops.object.shade_smooth()

    # planta na face do cubo
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"; bpy.ops.object.shade_flat()
    clay.rotation_euler=(math.radians(90),0,0); clay.scale=(0.95,0.95,0.95); clay.location=(0,-1.001,0.0)
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
    fo=bpy.data.objects.new("F",fd); fo.rotation_euler=(math.radians(20),0,math.radians(-150)); sc.collection.objects.link(fo)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.08,0.08,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.45; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam; cd.lens=55
    sc.render.engine='CYCLES'; sc.cycles.samples=40

    # viewport solid+cavity (sem render)
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
        setup(); bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"sc_{TAG}_vp_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        log(f"[vp {name}] ok")
    def s_front():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=5.0; rv3d.view_perspective='ORTHO'
    def s_3q():
        from mathutils import Euler as _E
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
        q=(_E((math.radians(20),0,math.radians(-35)),'XYZ').to_quaternion() @ rv3d.view_rotation.copy())
        rv3d.view_rotation=q; rv3d.view_perspective='PERSP'
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=6.5
    def s_side():
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='LEFT')
        rv3d.view_location=Vector((0,-0.5,0.0)); rv3d.view_distance=6.5; rv3d.view_perspective='PERSP'
    vp("3q", s_3q); vp("front", s_front); vp("side", s_side)

    # render simples
    def shoot(name, loc, tgt):
        cam.location=loc; cam.rotation_euler=(loc-tgt).to_track_quat('Z','Y').to_euler()
        sc.render.resolution_x=700; sc.render.resolution_y=700
        sc.render.filepath=os.path.join(OUT,f"sc_{TAG}_r_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
        log(f"[render {name}] ok")
    shoot("3q",   Vector((-2.6,-4.2,1.4)), Vector((0,-1.0,0.1)))
    shoot("side", Vector((-4.6,-2.0,0.6)), Vector((0,-1.0,0.1)))
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
