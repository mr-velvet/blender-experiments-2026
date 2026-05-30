# -*- coding: utf-8 -*-
"""
experiment-28 / 12_export_glb.py
Exporta a casa (sem as cascas clouds/mist que envolvem a camera) em GLB pro
viewer web. Mantem casa + deck + folhagem + Tree. Grava tambem o path da camera
(mesmas coords do 11_tour.py) num JSON, convertido Blender Z-up -> Three.js Y-up.

Roda: blender --background <blend> --python 12_export_glb.py -- <out_glb> <out_path_json>
"""
import bpy, sys, os, json, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT_GLB=argv[0] if len(argv)>0 else "out/web/house.glb"
OUT_PATH=argv[1] if len(argv)>1 else "out/web/campath.json"
os.makedirs(os.path.dirname(os.path.abspath(OUT_GLB)),exist_ok=True)

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc

KEEP_PREFIX=("Cube","Icosphere","IvyLeaf","Tree","IVY_Curve","Spot")
to_remove=[o for o in list(sc.objects) if not any(o.name.startswith(p) for p in KEEP_PREFIX)]
for o in to_remove:
    try: bpy.data.objects.remove(o,do_unlink=True)
    except Exception as e: print("rm warn",o.name,e)
print("kept",len(sc.objects),"objs for export")

bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects:
    try: o.select_set(True)
    except Exception: pass

# encolher texturas 4K -> max 1024 (walkthrough web nao precisa de 4K; corta o
# GLB de ~68MB pra poucos MB). Faz in-place via image.scale antes de exportar.
MAXTEX=1024
for img in bpy.data.images:
    try:
        if img.size[0] > MAXTEX or img.size[1] > MAXTEX:
            nw=min(MAXTEX,img.size[0]) if img.size[0] else MAXTEX
            nh=min(MAXTEX,img.size[1]) if img.size[1] else MAXTEX
            img.scale(nw,nh)
            print("scaled",img.name,"->",nw,nh)
    except Exception as e:
        print("scale warn",img.name,e)

bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format='GLB',
    use_selection=True, export_apply=True, export_yup=True,
    export_image_format='WEBP', export_image_quality=80,
)
print("EXPORTED GLB",OUT_GLB, os.path.getsize(OUT_GLB) if os.path.exists(OUT_GLB) else "MISSING")

# path da camera (espelha 11_tour.py)
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3;mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
DOOR_X=3.1; Y_S=mn[1]; Y_N=mx[1]; FLOOR_Z=-1.73; EYE=FLOOR_Z+1.55
pts=[
 (0.00, DOOR_X-0.2, Y_S-6.5, EYE+0.15),
 (0.18, DOOR_X,     Y_S-2.2, EYE),
 (0.32, DOOR_X,     Y_S+0.3, EYE-0.05),
 (0.55, DOOR_X+0.15,(Y_S+Y_N)/2, EYE),
 (0.78, DOOR_X,     Y_N-0.3, EYE-0.05),
 (1.00, DOOR_X-0.1, Y_N+6.0, EYE+0.1),
]
def look_target(frac):
    ahead=4.0
    y=(Y_S-6.5)+frac*((Y_N+6.0)-(Y_S-6.5))+ahead
    return (DOOR_X, y, EYE-0.15)
def to_three(p): return [round(p[0],4), round(p[2],4), round(-p[1],4)]  # Z-up -> Y-up
campath={"fov":50,"points":[]}
for frac,x,y,z in pts:
    campath["points"].append({"t":frac,"pos":to_three((x,y,z)),"look":to_three(look_target(frac))})
with open(OUT_PATH,"w",encoding="utf-8") as f: json.dump(campath,f,indent=2)
print("WROTE PATH",OUT_PATH)
print("EXPORT_DONE")
