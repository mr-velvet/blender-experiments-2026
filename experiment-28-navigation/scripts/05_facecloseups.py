# -*- coding: utf-8 -*-
"""
experiment-28 / 05_facecloseups.py
Close-ups das fachadas pra achar a porta (vao). 12 azimutes, camera perto,
nivel do olho, lente media, leve picada pra baixo, mirando a base da parede.
Bem iluminado. Set-dressing escondido.
Roda: blender --background <blend> --python 05_facecloseups.py -- <out_dir>
"""
import bpy, sys, os, math, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0] if argv else "out/faces"
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
cx,cy=(mn[0]+mx[0])/2,(mn[1]+mx[1])/2
sx,sy=mx[0]-mn[0],mx[1]-mn[1]; base_z=mn[2]
print("CENTER",round(cx,2),round(cy,2),"BASE_Z",round(base_z,2))

for o in sc.objects:
    if any(o.name.startswith(p) for p in ("clouds","mist","Landscape")): o.hide_render=True

w=bpy.data.worlds.new("W"); w.use_nodes=True
bg=w.node_tree.nodes.get("Background")
if bg: bg.inputs["Color"].default_value=(0.62,0.67,0.74,1); bg.inputs["Strength"].default_value=1.3
sc.world=w
sd=bpy.data.lights.new("S",'SUN'); sd.energy=4.0
su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(55),math.radians(10),math.radians(30))
sc.collection.objects.link(su)

for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try: sc.render.engine=eng;break
    except Exception: continue
sc.render.resolution_x=800;sc.render.resolution_y=800
sc.render.image_settings.file_format='PNG'
try: sc.eevee.taa_render_samples=16
except Exception: pass

def cam(n):
    cd=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,cd);sc.collection.objects.link(o);return o
def look(c,t):
    d=mathutils.Vector(t)-c.location;c.rotation_euler=d.to_track_quat('-Z','Y').to_euler()

radius=max(sx,sy)*0.85
target=(cx,cy,base_z+1.2)
for i in range(12):
    ang=math.radians(i*30)
    c=cam(f"F{i}")
    c.location=(cx+math.cos(ang)*radius, cy+math.sin(ang)*radius, base_z+1.9)
    look(c,target); c.data.lens=20
    sc.camera=c; sc.render.filepath=os.path.join(OUT,f"face{i*30:03d}.png")
    bpy.ops.render.render(write_still=True); print("RENDERED",i*30)
print("FACES_DONE")
