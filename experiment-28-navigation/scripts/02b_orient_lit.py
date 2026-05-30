# -*- coding: utf-8 -*-
"""
experiment-28 / 02b_orient_lit.py
Vistas de orientacao BEM ILUMINADAS pra achar as portas. 8 azimutes ao redor
da casa, nivel do olho, + um top ortografico. Sol forte + world ambiente claro
(temporario, so pra leitura). Esconde set-dressing gigante.
Roda: blender --background <blend> --python 02b_orient_lit.py -- <out_dir>
"""
import bpy, sys, os, math, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/orient2"
os.makedirs(OUT, exist_ok=True)

SCENE = "The Lonely Outpost"
sc = next((s for s in bpy.data.scenes if s.name == SCENE),
          max(bpy.data.scenes, key=lambda s: len(s.objects)))
bpy.context.window.scene = sc

def wbb(o):
    cs=[o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],
            [max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3; mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]); mx[i]=max(mx[i],b[i])
cx,cy,cz=[(mn[i]+mx[i])/2 for i in range(3)]
sx,sy,sz=[mx[i]-mn[i] for i in range(3)]
base_z=mn[2]
print("CENTER",round(cx,2),round(cy,2),round(cz,2),"SIZE",round(sx,2),round(sy,2),round(sz,2),"BASE_Z",round(base_z,2))

# esconder set-dressing
for o in sc.objects:
    if any(o.name.startswith(p) for p in ("clouds","mist","Landscape")):
        o.hide_render = True

# world ambiente claro temporario
w = bpy.data.worlds.new("OrientWorld")
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.6,0.65,0.72,1.0)
    bg.inputs["Strength"].default_value = 1.2
sc.world = w

# sol forte
sd = bpy.data.lights.new("OSun",'SUN'); sd.energy=5.0
su = bpy.data.objects.new("OSun", sd)
su.rotation_euler=(math.radians(50),math.radians(10),math.radians(35))
sc.collection.objects.link(su)

for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=960; sc.render.resolution_y=720
sc.render.image_settings.file_format='PNG'
try: sc.eevee.taa_render_samples=16
except Exception: pass

def cam(name):
    cd=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,cd)
    sc.collection.objects.link(o); return o
def look(c,t):
    d=mathutils.Vector(t)-c.location
    c.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
def shot(c,p):
    sc.camera=c; sc.render.filepath=p; bpy.ops.render.render(write_still=True); print("RENDERED",p)

# TOP
tc=cam("T"); tc.data.type='ORTHO'; tc.data.ortho_scale=max(sx,sy)*1.6
tc.location=(cx,cy,base_z+max(sx,sy)*2.0); tc.rotation_euler=(0,0,0)
shot(tc, os.path.join(OUT,"top.png"))

# 8 azimutes, eye level, mirando o meio da casa
radius=max(sx,sy)*1.25
mid=(cx,cy,base_z+sz*0.4)
eyez=base_z+1.7
import math as m
for i in range(8):
    ang=m.radians(i*45)
    c=cam(f"A{i}")
    c.location=(cx+m.cos(ang)*radius, cy+m.sin(ang)*radius, eyez)
    look(c,mid); c.data.lens=24
    # rotulo do azimute em graus pra eu mapear: 0=+X(E),90=+Y(N),180=-X(W),270=-Y(S)
    shot(c, os.path.join(OUT,f"az{i*45:03d}.png"))

print("ORIENT2_DONE")
