# -*- coding: utf-8 -*-
"""inspeciona + renderiza preview do asset baixado (pampas grass) isolado.
blender --background --python 11_preview_asset.py -- <asset_blend> <out_dir>"""
import bpy, sys, os, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
ASSET=argv[0]; OUT=argv[1]; os.makedirs(OUT,exist_ok=True)
# cena limpa
bpy.ops.wm.read_homefile(use_empty=True)
sc=bpy.context.scene
before=set(bpy.data.objects.keys())
with bpy.data.libraries.load(ASSET, link=False) as (src,dst):
    dst.objects=list(src.objects)
app=[o for o in dst.objects if o is not None]
for o in app:
    try: sc.collection.objects.link(o)
    except Exception: pass
meshes=[o for o in app if o.type=='MESH']
print("APPENDED objs:",len(app),"meshes:",len(meshes))
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3;mx=[-1e9]*3
for o in meshes:
    a,b=wbb(o)
    for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
size=[mx[i]-mn[i] for i in range(3)]
cx,cy,cz=[(mn[i]+mx[i])/2 for i in range(3)]
print("ASSET bbox size x=%.2f y=%.2f z=%.2f (altura=%.2f m)"%(size[0],size[1],size[2],size[2]))
for o in meshes[:20]:
    a,b=wbb(o); print("  %-24s h=%.2f"%(o.name[:24], b[2]-a[2]))
# luz+world
w=bpy.data.worlds.new("W"); w.use_nodes=True; sc.world=w
bg=w.node_tree.nodes.get("Background")
if bg: bg.inputs["Color"].default_value=(0.6,0.66,0.74,1); bg.inputs["Strength"].default_value=1.3
sd=bpy.data.lights.new("S",'SUN'); sd.energy=3.5
su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(52),math.radians(8),math.radians(35)); sc.collection.objects.link(su)
for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try: sc.render.engine=e; break
    except Exception: continue
sc.render.resolution_x=700; sc.render.resolution_y=900
try: sc.eevee.taa_render_samples=24
except Exception: pass
try: sc.view_settings.view_transform='AgX'
except Exception: pass
cd=bpy.data.cameras.new("c"); cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
r=max(size[0],size[1],size[2])*1.6
cam.location=(cx+r*0.7, cy-r, cz+size[2]*0.15)
d=mathutils.Vector((cx,cy,cz))-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.lens=50
sc.render.filepath=os.path.join(OUT,"asset_preview.png")
bpy.ops.render.render(write_still=True)
print("PREVIEW_DONE", os.path.join(OUT,"asset_preview.png"))
