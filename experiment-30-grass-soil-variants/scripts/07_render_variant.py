# -*- coding: utf-8 -*-
"""render check de uma variante: aereo 3/4 + eye-level. .jpg default.
blender --background <variant_blend> --python 07_render_variant.py -- <out_dir> <tag>"""
import bpy, sys, os, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0]; TAG=argv[1] if len(argv)>1 else "v"
os.makedirs(OUT,exist_ok=True)
SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3;mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
cx,cy=(mn[0]+mx[0])/2,(mn[1]+mx[1])/2; base_z=mn[2]
for o in sc.objects:
    if o.name.startswith("clouds") or o.name.startswith("mist"): o.hide_render=True
sd=bpy.data.lights.new("S",'SUN'); sd.energy=3.0
su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(52),math.radians(8),math.radians(35)); sc.collection.objects.link(su)
for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try: sc.render.engine=e; break
    except Exception: continue
sc.render.resolution_x=1000; sc.render.resolution_y=666
try: sc.eevee.taa_render_samples=20
except Exception: pass
try: sc.view_settings.view_transform='AgX'
except Exception: pass
def cam(n):
    cd=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,cd);sc.collection.objects.link(o);return o
def look(c,t):
    d=mathutils.Vector(t)-c.location;c.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
c1=cam("c1"); c1.location=(cx-16,cy-16,base_z+13); look(c1,(cx,cy,base_z+1)); c1.data.lens=28
sc.camera=c1; sc.render.filepath=os.path.join(OUT,f"{TAG}_aerial.jpg"); bpy.ops.render.render(write_still=True); print("R aerial")
c3=cam("c3"); c3.location=(cx-0.5,mn[1]-9,base_z+1.6); look(c3,(cx,cy,base_z+1.5)); c3.data.lens=30
sc.camera=c3; sc.render.filepath=os.path.join(OUT,f"{TAG}_eye.jpg"); bpy.ops.render.render(write_still=True); print("R eye")
print("RV_DONE",TAG)
