"""
07_render_edit.py — render de validacao de uma cena editada (A ou B).
Cria 2 cameras por codigo (frontal 3/4 + lateral) mirando a casa e renderiza Cycles.

Roda via:
  blender --background <blend> --python 07_render_edit.py -- <out_dir> <tag> <samples>
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv; argv = argv[argv.index("--")+1:]
OUT = argv[0]; TAG = argv[1]; SAMPLES = int(argv[2]) if len(argv)>2 else 64
os.makedirs(OUT, exist_ok=True)

def log(*a): print("[red]", *a, flush=True)

# escolhe a scene do asset (NAO a "Scene" default que tem o cubo padrao)
sc = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        sc = s; break
if sc is None:
    # fallback: a scene com mais objetos
    sc = max(bpy.data.scenes, key=lambda s: len(s.objects))
bpy.context.window.scene = sc
log("scene:", sc.name, "objs:", len(sc.objects))

# bbox da casa (Cube*) pra mirar
mn=Vector((1e9,)*3); mx=Vector((-1e9,)*3)
for o in sc.objects:
    if o.type=="MESH" and (o.name.startswith("Cube") or o.name.startswith("Icosphere") or o.name.startswith("IvyLeaf") or o.name=="FlatGround"):
        for c in o.bound_box:
            w=o.matrix_world@Vector(c)
            for i in range(3): mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
# foco so na casa (exclui FlatGround do centro vertical)
house=[o for o in sc.objects if o.type=="MESH" and (o.name.startswith("Cube") or o.name.startswith("Icosphere"))]
hmn=Vector((1e9,)*3); hmx=Vector((-1e9,)*3)
for o in house:
    for c in o.bound_box:
        w=o.matrix_world@Vector(c)
        for i in range(3): hmn[i]=min(hmn[i],w[i]); hmx[i]=max(hmx[i],w[i])
center=(hmn+hmx)*0.5
size=hmx-hmn
radius=max(size.x,size.y)
focus=center.copy(); focus.z=center.z+size.z*0.1
log("house center", tuple(round(v,1) for v in center), "radius", round(radius,1))

sc.render.engine="CYCLES"; sc.cycles.samples=SAMPLES
try:
    cp=bpy.context.preferences.addons["cycles"].preferences; cp.get_devices()
    for dt in ("OPTIX","CUDA","HIP","METAL","ONEAPI"):
        try: cp.compute_device_type=dt; break
        except: pass
    for d in cp.devices: d.use=True
    sc.cycles.device="GPU"
except Exception as e: log("gpu skip",e)
sc.render.resolution_x=1280; sc.render.resolution_y=720
sc.render.image_settings.file_format="PNG"

def make_cam(name,loc,look,lens=50):
    cd=bpy.data.cameras.new(name); cd.lens=lens
    cam=bpy.data.objects.new(name,cd); sc.collection.objects.link(cam)
    cam.location=loc; cam.rotation_euler=(Vector(look)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    return cam

dist=radius*4.2
shots=[("front",215,5,55),("side",300,7,55)]
for nm,az,h,lens in shots:
    a=math.radians(az)
    loc=Vector((center.x+dist*math.cos(a), center.y+dist*math.sin(a), center.z+h))
    cam=make_cam("C_"+nm,loc,focus,lens); sc.camera=cam
    p=os.path.join(OUT,f"{TAG}_{nm}.png"); sc.render.filepath=p
    bpy.ops.render.render(write_still=True)
    log(nm,"->",os.path.basename(p), os.path.getsize(p) if os.path.exists(p) else "FAIL")
log("DONE")
