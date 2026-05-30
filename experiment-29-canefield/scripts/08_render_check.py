# -*- coding: utf-8 -*-
"""render de verificacao do capinzal: 3/4 aereo, top, nivel do olho sul e oeste.
blender --background <canefield_blend> --python 08_render_check.py -- <out_dir>"""
import bpy, sys, os, math, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0] if argv else "out/check"
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
su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(52),math.radians(8),math.radians(35))
sc.collection.objects.link(su)
for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try: sc.render.engine=e; break
    except Exception: continue
sc.render.resolution_x=1100; sc.render.resolution_y=730
try: sc.eevee.taa_render_samples=24
except Exception: pass
try: sc.view_settings.view_transform='AgX'
except Exception: pass
def cam(n):
    cd=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,cd);sc.collection.objects.link(o);return o
def look(c,t):
    d=mathutils.Vector(t)-c.location;c.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
shots=[]
c1=cam("c1"); c1.location=(cx-16,cy-16,base_z+13); look(c1,(cx,cy,base_z+1)); c1.data.lens=28
shots.append((c1,"aerial_34.png"))
c2=cam("c2"); c2.data.type='ORTHO'; c2.data.ortho_scale=42; c2.location=(cx,cy,base_z+40); c2.rotation_euler=(0,0,0)
shots.append((c2,"top.png"))
c3=cam("c3"); c3.location=(cx-0.5,mn[1]-9,base_z+1.6); look(c3,(cx,cy,base_z+1.5)); c3.data.lens=30
shots.append((c3,"eye_south.png"))
c4=cam("c4"); c4.location=(mn[0]-10,cy,base_z+1.6); look(c4,(cx,cy,base_z+1.2)); c4.data.lens=30
shots.append((c4,"eye_west.png"))
for c,fn in shots:
    sc.camera=c; sc.render.filepath=os.path.join(OUT,fn); bpy.ops.render.render(write_still=True); print("R",fn)
print("CHECK_DONE")
