# -*- coding: utf-8 -*-
"""preview de cada planta baixada (le downloaded_plants.json). 1 render por asset.
blender --background --python 04_preview_all.py -- <plants_json> <out_dir>"""
import bpy, sys, os, math, mathutils, json
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
PJSON=argv[0]; OUT=argv[1]; os.makedirs(OUT,exist_ok=True)
plants=json.load(open(PJSON,encoding="utf-8"))

def render_asset(key, blendpath):
    bpy.ops.wm.read_homefile(use_empty=True)
    sc=bpy.context.scene
    with bpy.data.libraries.load(blendpath, link=False) as (src,dst):
        dst.objects=list(src.objects)
    app=[o for o in dst.objects if o is not None]
    for o in app:
        try: sc.collection.objects.link(o)
        except Exception: pass
    meshes=[o for o in app if o.type=='MESH']
    if not meshes: print("  no mesh in",key); return None
    def wbb(o):
        cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
        return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
    mn=[1e9]*3;mx=[-1e9]*3
    for o in meshes:
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
    size=[mx[i]-mn[i] for i in range(3)]; cx,cy,cz=[(mn[i]+mx[i])/2 for i in range(3)]
    print("  %s: h=%.2f w=%.2f meshes=%d"%(key,size[2],max(size[0],size[1]),len(meshes)))
    w=bpy.data.worlds.new("W"); w.use_nodes=True; sc.world=w
    bg=w.node_tree.nodes.get("Background")
    if bg: bg.inputs["Color"].default_value=(0.6,0.66,0.74,1); bg.inputs["Strength"].default_value=1.3
    sd=bpy.data.lights.new("S",'SUN'); sd.energy=3.5
    su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(52),math.radians(8),math.radians(35)); sc.collection.objects.link(su)
    for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
        try: sc.render.engine=e; break
        except Exception: continue
    sc.render.resolution_x=600; sc.render.resolution_y=780
    try: sc.eevee.taa_render_samples=20
    except Exception: pass
    try: sc.view_settings.view_transform='AgX'
    except Exception: pass
    cd=bpy.data.cameras.new("c"); cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
    r=max(size)*1.7+0.5
    cam.location=(cx+r*0.7,cy-r,cz+size[2]*0.1)
    d=mathutils.Vector((cx,cy,cz))-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    cam.data.lens=50
    fp=os.path.join(OUT,f"{key}.png"); sc.render.filepath=fp
    bpy.ops.render.render(write_still=True)
    print("  RENDERED",fp)
    return size[2]

heights={}
for key,info in plants.items():
    if info.get("blend") and os.path.exists(info["blend"]):
        h=render_asset(key, info["blend"])
        heights[key]=h
    else:
        print("  SKIP",key,"no blend")
json.dump(heights,open(os.path.join(OUT,"heights.json"),"w"),indent=2)
print("PREVIEW_ALL_DONE",heights)
