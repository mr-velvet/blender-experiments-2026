"""32: rosto com pinceis VDM plantado numa face de CUBO. Versao corrigida.

Base: o asm_a2 (que o user achou "interessante") — olhos rotz=0, nariz 115, boca.
Correcoes do user (2026-05-26 19:44):
- olhos a 45deg: esquerdo anti-horario (+45), direito horario (-45) + espelhado
- testar outras bocas (env MOUTH_BRUSH; rodo b15/16/17/18 em processos separados)
- plantar numa face do cubo, prints viewport E render, incluindo lateral

Um processo por boca (env MOUTH_BRUSH, TAG). Evita crash por acumulo de estado.
"""
import bpy, os, sys, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
MOUTH=int(os.environ.get("MOUTH_BRUSH","16"))
TAG=os.environ.get("TAG",f"v2_m{MOUTH}")
LOGF=os.path.join(OUT,f"32_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

# nome, brush, radius, rot_z_deg, posx, posy, scale, mirror_x
FEATURES=[
    ["nariz",   28, 0.45,  115, 0.00,-0.02, 0.62, False],
    ["olho_esq",25, 0.55,   45,-0.34, 0.30, 0.42, False],  # 45 anti-horario
    ["olho_dir",25, 0.55,  -45, 0.34, 0.30, 0.42, True ],  # 45 horario + espelhado
    ["boca",  MOUTH, 0.42,  -78, 0.00,-0.44, 0.55, False],  # mesma orient do asm_a2
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
    log(f"  stamp {name} b{bidx} r={radius} z[{zmin:.3f},{zmax:.3f}] verts={len(obj.data.vertices)}")
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

    # placa-rosto de fundo
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        base=bpy.context.view_layer.objects.active; base.name="FaceBase"
        m=base.modifiers.new("s","SUBSURF"); m.levels=4; bpy.ops.object.modifier_apply(modifier=m.name)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT')
        for o in feat_objs+[base]: o.select_set(True)
        bpy.context.view_layer.objects.active=base
        bpy.ops.object.join()
        face=bpy.context.view_layer.objects.active; face.name="FacePlate"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.004)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        sm=face.modifiers.new("smooth","SMOOTH"); sm.factor=0.45; sm.iterations=6
        bpy.ops.object.modifier_apply(modifier=sm.name)
        bpy.ops.object.shade_smooth()

    # --- PLANTAR no CUBO (face -Y) ---
    CUBE_HALF=1.0
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0,0,0))
        cube=bpy.context.view_layer.objects.active; cube.name="Cube"
        bpy.ops.object.shade_flat()
    # placa em XY, relevo +Z. rot -90 em X manda +Z -> +Y? Nao: rot -90 X leva +Z->-Y.
    # Queremos relevo apontando -Y (face frontal -Y onde a camera olha). rot +90 X leva +Z->+Y.
    # Vou usar rot +90 X (relevo +Z -> -Y? testar). Convencao Blender: Rx(+90): y->z, z->-y.
    # Entao +Z -> -Y. Bom: relevo aponta -Y (frente). E +Y(cima da placa) -> +Z(cima do cubo). OK.
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
    for o in (cube,face):
        o.data.materials.clear(); o.data.materials.append(mat)

    sc=bpy.context.scene
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.2; kd.angle=0.05
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(55),0,math.radians(-25)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.0; fd.angle=0.6
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(40),0,math.radians(140)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.06,0.06,0.07,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.35; sc.world=w
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
        "side2": (Vector((-3.4,-3.0,2.2)), Vector((0,-0.6,0.1))),
    }
    for nm,(loc,tgt) in views.items():
        shoot(nm,loc,tgt)

    # PRINTS VIEWPORT (solid+cavity, render.opengl)
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
        with bpy.context.temp_override(**ov):
            bpy.ops.view3d.view_axis(type=axis)
        rv3d.view_location=Vector((0,-0.5,0.1)); rv3d.view_distance=dist; rv3d.view_perspective=persp
        bpy.context.view_layer.update()
        sc.render.filepath=os.path.join(OUT,f"cube_{TAG}_vp_{name}.png")
        with bpy.context.temp_override(**ov): bpy.ops.render.opengl(write_still=True)
        log(f"[viewport {name}] ok")

    vp("front", 'FRONT', persp='ORTHO', dist=5.0)
    vp("side",  'LEFT',  persp='PERSP', dist=6.5)
    from mathutils import Euler as _E
    with bpy.context.temp_override(**ov):
        bpy.ops.view3d.view_axis(type='FRONT')
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
