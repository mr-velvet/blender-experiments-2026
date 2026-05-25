"""Orbita completa (4 angulos) do nivel de Separation vencedor, vista geral."""
import bpy, os, sys, math
from mathutils import Vector
argv = sys.argv; argv = argv[argv.index("--")+1:] if "--" in argv else []
GLB=argv[0]; SEP=float(argv[1]); TAG=argv[2]; RES=int(argv[3]) if len(argv)>3 else 560; SAMPLES=int(argv[4]) if len(argv)>4 else 36
SD=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(SD)
ASSET=os.path.join(os.path.dirname(ROOT),"experiment-13-easy-cardboard","assets","easy-cardboard-3.1.blend")
OUT=os.path.join(ROOT,"output","model_renders"); os.makedirs(OUT,exist_ok=True)
NG="\U0001F4E6 Easy Cardboard 3.0"; MAT="Easy Cardboard 3"
def log(m): print(f"[ORBIT] {m}",flush=True)
AGED={"Thickness":0.006,"Global Scale":0.5,"Wear ⏰":0.7,"Seed \U0001F3B2":7,"Split Angle":math.radians(35),"Strength":0.35,"Separation":SEP,"Separation Noise Scale":0.0,"Z Position":1.0," Fibers Density":8.0,"Fibers Size":0.02,"Displacement Strength":0.4,"Normal Strength":1.0,"Roughness ":0.9,"Metallic":0.0,"UV Name":"UVMap"}
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.meshes): bpy.data.meshes.remove(c)
for c in list(bpy.data.materials): bpy.data.materials.remove(c)
with bpy.data.libraries.load(ASSET,link=False) as (s,d): d.node_groups=[NG]; d.materials=[MAT]
ng=bpy.data.node_groups.get(NG); mat=bpy.data.materials.get(MAT)
bpy.ops.import_scene.gltf(filepath=GLB)
ms=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects: o.select_set(False)
for o in ms: o.select_set(True)
bpy.context.view_layer.objects.active=ms[0]
if len(ms)>1: bpy.ops.object.join()
obj=bpy.context.active_object; obj.name="house"
bpy.context.view_layer.objects.active=obj; obj.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.context.view_layer.update()
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]; obj.location-=sum(bb,Vector())/8.0
bpy.ops.object.transform_apply(location=True)
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]
md=max((max(p[i] for p in bb)-min(p[i] for p in bb)) for i in range(3)); obj.scale=(0.3/md,)*3
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')
if obj.data.uv_layers: obj.data.uv_layers[0].name='UVMap'; obj.data.uv_layers[0].active_render=True
obj.data.materials.clear(); obj.data.materials.append(mat)
mod=obj.modifiers.new(name="EC",type='NODES'); mod.node_group=ng
def si(n,v):
    for it in mod.node_group.interface.items_tree:
        if getattr(it,'in_out',None)=='INPUT' and (it.name or "").strip()==n.strip():
            try: mod[it.identifier]=v; return
            except Exception as e: log(f"FAIL {n}:{e}"); return
for k,v in AGED.items(): si(k,v)
bpy.context.view_layer.update(); bpy.context.view_layer.objects.active=obj
bpy.ops.object.modifier_apply(modifier="EC")
scn=bpy.context.scene; scn.render.engine='CYCLES'; scn.cycles.samples=SAMPLES; scn.cycles.use_denoising=True
scn.render.resolution_x=RES; scn.render.resolution_y=RES
w=bpy.data.worlds[0]; scn.world=w; w.use_nodes=True
bgn=w.node_tree.nodes.get("Background")
if bgn: bgn.inputs[0].default_value=(0.05,0.05,0.06,1.0); bgn.inputs[1].default_value=1.0
def al(n,l,e,s):
    ld=bpy.data.lights.new(n,'AREA'); ld.energy=e; ld.size=s
    lo=bpy.data.objects.new(n,ld); lo.location=l; bpy.context.collection.objects.link(lo)
    lo.rotation_euler=(-1*lo.location).to_track_quat('-Z','Y').to_euler()
al("k",Vector((0.35,-0.3,0.45)),60,0.5); al("f",Vector((-0.4,-0.2,0.2)),25,0.6); al("r",Vector((0.0,0.4,0.35)),45,0.4)
bpy.context.view_layer.update()
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]; obj.location-=sum(bb,Vector())/8.0
bpy.context.view_layer.update()
bb=[obj.matrix_world@Vector(c) for c in obj.bound_box]
md=max((max(p[i] for p in bb)-min(p[i] for p in bb)) for i in range(3))
cd=bpy.data.cameras.new("C"); cd.lens=50; cam=bpy.data.objects.new("C",cd); bpy.context.collection.objects.link(cam); scn.camera=cam
r=md*1.9; el=math.radians(18)
for i,azd in enumerate([25,115,205,300]):
    az=math.radians(azd); c=Vector((r*math.cos(az)*math.cos(el),r*math.sin(az)*math.cos(el),r*math.sin(el)))
    cam.location=c; cam.rotation_euler=(Vector((0,0,0))-c).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update(); p=os.path.join(OUT,f"final_{TAG}_o{i}.png"); scn.render.filepath=p
    log(f"Render {TAG} o{i}"); bpy.ops.render.render(write_still=True)
log("DONE"); print("[ORBIT] === SUCCESS ===",flush=True)
