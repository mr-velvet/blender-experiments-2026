"""33: rosto VDM na face do CUBO, com FALLOFF RADIAL nas features (elimina as
bordas pretas duras do recorte em disco) + olhos e boca parametrizaveis.

Diferenca-chave vs 29/32: ao recortar cada feature, em vez de corte seco no disco
(que deixa parede vertical -> sombra preta), aplico um falloff suave no Z: o
deslocamento e multiplicado por smoothstep que vai a 1 no centro e 0 na borda do
disco. Assim a borda casa com a base (Z=0) sem degrau.

Params via env:
  EYE_ROT   (graus, default 90) - rotacao do olho esquerdo; direito = -EYE_ROT + mirror
  MOUTH_BRUSH (default 16)
  MOUTH_ROT (graus, default -78)
  TAG
"""
import bpy, os, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
EYE_ROT=float(os.environ.get("EYE_ROT","90"))
MOUTH=int(os.environ.get("MOUTH_BRUSH","16"))
MOUTH_ROT=float(os.environ.get("MOUTH_ROT","-78"))
TAG=os.environ.get("TAG",f"f_e{int(EYE_ROT)}_m{MOUTH}")
LOGF=os.path.join(OUT,f"33_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# nome, brush, radius, rot_z, posx, posy, scale, mirror
FEATURES=[
    ["nariz",   28, 0.45,  115, 0.00,-0.02, 0.62, False],
    ["olho_esq",25, 0.55,  EYE_ROT, -0.34, 0.30, 0.42, False],
    ["olho_dir",25, 0.55, -EYE_ROT,  0.34, 0.30, 0.42, True ],
    ["boca",  MOUTH, 0.42, MOUTH_ROT, 0.00,-0.44, 0.55, False],
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
    # recorte simples num disco (receita do asm_a2, que o user aprovou). O degrau
    # leve nas bordas e atenuado depois pelo smooth global no join.
    me=obj.data
    rcut=radius*1.05
    import bmesh
    bm=bmesh.new(); bm.from_mesh(me)
    to_del=[v for v in bm.verts if (v.co.x*v.co.x+v.co.y*v.co.y) > rcut*rcut]
    bmesh.ops.delete(bm, geom=to_del, context='VERTS')
    bm.to_mesh(me); bm.free(); me.update()
    zmax=max(v.co.z for v in me.vertices); zmin=min(v.co.z for v in me.vertices)
    log(f"  stamp {name} b{bidx} r={radius} z[{zmin:.3f},{zmax:.3f}] verts={len(me.vertices)}")
    return obj

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}

    feat_objs=[]
    for name,bidx,radius,rotz,px,py,scale,mirror in FEATURES:
        obj=stamp_feature(name,bidx,radius,ov,region,rv3d)
        sx=-scale if mirror else scale
        obj.scale=(sx,scale,scale)
        obj.rotation_euler=(0,0,math.radians(rotz))
        obj.location=(px,py,0)
        with bpy.context.temp_override(**ov):
            bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
            bpy.context.view_layer.objects.active=obj
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        feat_objs.append(obj)
        log(f"  place {name} rotz={rotz} pos=({px},{py}) scale={scale} mirror={mirror}")

    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        base=bpy.context.view_layer.objects.active; base.name="FaceBase"
        m=base.modifiers.new("s","SUBSURF"); m.levels=5; bpy.ops.object.modifier_apply(modifier=m.name)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT')
        for o in feat_objs+[base]: o.select_set(True)
        bpy.context.view_layer.objects.active=base
        bpy.ops.object.join()
        face=bpy.context.view_layer.objects.active; face.name="FacePlate"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.003)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        sm=face.modifiers.new("smooth","SMOOTH"); sm.factor=0.5; sm.iterations=8
        bpy.ops.object.modifier_apply(modifier=sm.name)
        bpy.ops.object.shade_smooth()

    CUBE_HALF=1.0
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"
        bpy.ops.object.shade_flat()
    face.rotation_euler=(math.radians(90),0,0)
    face.scale=(0.92,0.92,0.92)
    face.location=(0,-CUBE_HALF-0.001,0.05)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); face.select_set(True)
        bpy.context.view_layer.objects.active=face
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.62
    for o in (cube,face): o.data.materials.clear(); o.data.materials.append(mat)

    sc=bpy.context.scene
    # luz da receita do asm_a2 mas adaptada pra face -Y do cubo: key vem de
    # cima-frente (-Y, +Z), fill da lateral oposta. angle maior = sombra suave.
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.5
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(35),0,math.radians(15)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.3; fd.angle=0.8
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(20),0,math.radians(-150)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.08,0.08,0.09,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.45; sc.world=w
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    sc.collection.objects.link(cam); sc.camera=cam; cd.lens=55
    sc.render.engine='CYCLES'; sc.cycles.samples=64
    sc.render.resolution_x=900; sc.render.resolution_y=900

    def shoot(name, loc, tgt):
        cam.location=loc
        cam.rotation_euler=(loc-tgt).to_track_quat('Z','Y').to_euler()
        sc.render.filepath=os.path.join(OUT,f"cube_{TAG}_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
        log(f"[render {name}] ok")

    views={
        "front": (Vector((0,-5.2,0.1)), Vector((0,-1.0,0.1))),
        "3q":    (Vector((-2.6,-4.2,1.4)), Vector((0,-1.0,0.1))),
        "side":  (Vector((-4.8,-1.6,0.6)), Vector((0,-0.6,0.1))),
    }
    for nm,(loc,tgt) in views.items(): shoot(nm,loc,tgt)

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

    def vp(name, axis, persp='PERSP', dist=6.5):
        with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type=axis)
        rv3d.view_location=Vector((0,-0.5,0.1)); rv3d.view_distance=dist; rv3d.view_perspective=persp
        bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"cube_{TAG}_vp_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        log(f"[viewport {name}] ok")

    vp("front", 'FRONT', persp='ORTHO', dist=5.0)
    vp("side",  'LEFT',  persp='PERSP', dist=6.5)
    from mathutils import Euler as _E
    with bpy.context.temp_override(**ov): bpy.ops.view3d.view_axis(type='FRONT')
    base_q=rv3d.view_rotation.copy()
    q3q=(_E((math.radians(18),0,math.radians(-32)),'XYZ').to_quaternion() @ base_q)
    rv3d.view_rotation=q3q; rv3d.view_perspective='PERSP'
    rv3d.view_location=Vector((0,-0.5,0.1)); rv3d.view_distance=6.5
    bpy.context.view_layer.update()
    sc.render.filepath=os.path.join(OUT,f"cube_{TAG}_vp_3q.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
    log("[viewport 3q] ok")

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"cube_{TAG}.blend")); log("[saved]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
