"""27: monta o rosto por OBJETOS. Cada feature e carimbada isolada num plano
(tamanho cheio garantido em roll 0), depois o objeto e ROTACIONADO (Z) e
POSICIONADO na cara, e tudo e juntado.

Isso resolve: escala consistente (cada feature carimba sozinha) + orientacao
(rotaciono o objeto, nao o stamp). As features sao VDM reais do sculpt.

FEATURES: nome, brush, radius, rot_z_deg (girar a feature), pos (x,y na cara), scale
"""
import bpy, os, sys, math, json
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG=sys.argv[-1] if len(sys.argv)>1 and not sys.argv[-1].endswith(".py") else "a1"
LOGF=os.path.join(OUT,f"27_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

_default=[
    # nome, brush, radius, rot_z_deg, posx, posy, scale, mirror_x
    ["nariz",   28, 0.45,  115, 0.00,-0.02, 0.62, False],
    ["olho_esq",25, 0.55,    0,-0.34, 0.30, 0.42, False],
    ["olho_dir",25, 0.55,    0, 0.34, 0.30, 0.42, True ],
    ["boca",    15, 0.42,  -78, 0.00,-0.42, 0.55, False],
]
FEATURES=json.loads(os.environ.get("ASM_PLAN", json.dumps(_default)))

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
    """cria um plano, carimba a feature sozinha no centro (roll0), recorta pra
    a regiao com relevo, retorna o objeto."""
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
    zmax=max(v.co.z for v in obj.data.vertices); zmin=min(v.co.z for v in obj.data.vertices)
    # recorta um DISCO central (raio = radius*1.05) pra so manter a feature,
    # sem o resto do plano que criaria bordas pretas ao sobrepor
    rcut=radius*1.05
    import bmesh
    bm=bmesh.new(); bm.from_mesh(obj.data)
    to_del=[v for v in bm.verts if (v.co.x*v.co.x+v.co.y*v.co.y) > rcut*rcut]
    bmesh.ops.delete(bm, geom=to_del, context='VERTS')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    log(f"  stamp {name} b{bidx} r={radius} z[{zmin:.3f},{zmax:.3f}] cut_r={rcut:.2f} verts={len(obj.data.vertices)}")
    return obj

def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}

    feat_objs=[]
    for name,bidx,radius,rotz,px,py,scale,mirror in FEATURES:
        obj=stamp_feature(name,bidx,radius,ov,region,rv3d)
        # recorta um disco central (onde esta o relevo) pra nao carregar o plano todo
        # transforma: escala, espelha, rotaciona Z, translada
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

    # plano-cara de fundo (a "face base")
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        base=bpy.context.view_layer.objects.active; base.name="FaceBase"
        m=base.modifiers.new("s","SUBSURF"); m.levels=4; bpy.ops.object.modifier_apply(modifier=m.name)

    # junta tudo
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT')
        for o in feat_objs+[base]: o.select_set(True)
        bpy.context.view_layer.objects.active=base
        bpy.ops.object.join()
        face=bpy.context.view_layer.objects.active; face.name="Face"
        # solda vertices coincidentes das bordas dos discos com a base
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.004)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        # smooth corretivo leve pra suavizar o degrau nas juntas
        sm=face.modifiers.new("smooth","SMOOTH"); sm.factor=0.5; sm.iterations=8
        bpy.ops.object.modifier_apply(modifier=sm.name)
        bpy.ops.object.shade_smooth()

    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.6
    face.data.materials.clear(); face.data.materials.append(mat)

    sc=bpy.context.scene
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    cd.type='ORTHO'; cd.ortho_scale=2.2; cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
    sc.collection.objects.link(cam); sc.camera=cam
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.04
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(58),0,math.radians(20)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.1; fd.angle=0.6
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(35),0,math.radians(-150)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.07,0.07,0.08,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.3; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.render.resolution_x=800; sc.render.resolution_y=800
    sc.render.filepath=os.path.join(OUT,f"asm_{TAG}_front.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[front] ok")
    cam.location=(1.0,-2.2,3.4); cam.rotation_euler=(cam.location-Vector((0,0,0))).to_track_quat('Z','Y').to_euler()
    sc.render.filepath=os.path.join(OUT,f"asm_{TAG}_3q.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[3q] ok")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"asm_{TAG}.blend")); log("[saved]")

_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
