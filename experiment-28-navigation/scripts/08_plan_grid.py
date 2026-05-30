# -*- coding: utf-8 -*-
"""
experiment-28 / 08_plan_grid.py
Planta baixa ortografica de cima, cortada na altura da porta (clip), com uma
GRADE de coordenadas world sobreposta (linhas a cada 1m em X e Y, rotuladas).
Leio a porta direto na regua. Inequivoco.

Desenha a grade como objetos no mundo (linhas finas + textos), na altura do
corte, alinhados ao world. Render Workbench flat, camera ORTHO de cima exata.

Roda: blender --background <blend> --python 08_plan_grid.py -- <out_png> <z_corte>
"""
import bpy, sys, os, math, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0] if argv else "out/plan_grid.png"
ZCUT=float(argv[1]) if len(argv)>1 else None

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
base_z=mn[2]; top_z=mx[2]
if ZCUT is None: ZCUT=base_z+1.0
print("BBOX x[%.2f,%.2f] y[%.2f,%.2f] ZCUT=%.2f"%(mn[0],mx[0],mn[1],mx[1],ZCUT))

# esconder set-dressing e chao
for o in sc.objects:
    if any(o.name.startswith(p) for p in ("clouds","mist","Landscape")) or o.name=="FlatGround":
        o.hide_render=True

# --- desenhar grade no plano ZCUT+pequeno offset (linhas como meshes finas) ---
gx0,gx1=math.floor(mn[0]-1),math.ceil(mx[0]+1)
gy0,gy1=math.floor(mn[1]-1),math.ceil(mx[1]+1)
zg=ZCUT+0.02
grid_mat=bpy.data.materials.new("grid"); grid_mat.use_nodes=False; grid_mat.diffuse_color=(1,0,0,1)
def line(p0,p1,w=0.02):
    me=bpy.data.meshes.new("L"); ob=bpy.data.objects.new("L",me)
    sc.collection.objects.link(ob)
    a=mathutils.Vector(p0); b=mathutils.Vector(p1)
    d=(b-a); n=mathutils.Vector((-d.y,d.x,0));
    if n.length>0: n=n.normalized()*w
    verts=[a+n,b+n,b-n,a-n]; faces=[(0,1,2,3)]
    me.from_pydata([tuple(v) for v in verts],[],faces); me.update()
    ob.data.materials.append(grid_mat)
    ob.hide_render=False
    return ob
for X in range(gx0,gx1+1):
    line((X,gy0,zg),(X,gy1,zg), 0.03 if X%5 else 0.06)
for Y in range(gy0,gy1+1):
    line((gx0,Y,zg),(gx1,Y,zg), 0.03 if Y%5 else 0.06)

# rotulos de texto a cada 1m nas bordas
def label(txt,x,y,size=0.45):
    cu=bpy.data.curves.new("t",'FONT'); cu.body=txt; cu.size=size
    ob=bpy.data.objects.new("t",cu); sc.collection.objects.link(ob)
    ob.location=(x,y,zg+0.01); ob.data.materials.append(grid_mat)
    return ob
for X in range(gx0,gx1+1):
    label(str(X), X-0.15, gy1+0.2)
    label(str(X), X-0.15, gy0-0.6)
for Y in range(gy0,gy1+1):
    label(str(Y), gx1+0.2, Y-0.2)
    label(str(Y), gx0-0.9, Y-0.2)

# Workbench flat
sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=1100; sc.render.resolution_y=1100
sc.render.image_settings.file_format='PNG'
try:
    sh=sc.display.shading; sh.light='FLAT'; sh.color_type='TEXTURE'
except Exception as e: print("shade",e)

cd=bpy.data.cameras.new("PG"); cam=bpy.data.objects.new("PG",cd)
sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
pad=2.0
span=max((gx1-gx0),(gy1-gy0))+pad
cam.data.ortho_scale=span
camz=base_z+40
cam.location=((gx0+gx1)/2,(gy0+gy1)/2,camz)
cam.rotation_euler=(0,0,0)
# corta tudo acima de ZCUT (telhado) -> ve as paredes cortadas + grade
cam.data.clip_start=camz-ZCUT
cam.data.clip_end=camz-(base_z-0.5)

os.makedirs(os.path.dirname(os.path.abspath(OUT)),exist_ok=True)
sc.render.filepath=OUT
bpy.ops.render.render(write_still=True)
print("PLAN_GRID_DONE",OUT,"  +Y=topo(N) +X=direita(E)")
