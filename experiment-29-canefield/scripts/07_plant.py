# -*- coding: utf-8 -*-
"""
experiment-29 / 07_plant.py
Apenda o asset de capim-dos-pampas (2 meshes: PAMPASS + GRASS BLADE) na cena da
casa (lonely_B_floor) e PLANTA um capinzal alto em volta da casa, sobre o
terreno liso (FlatGround recentrado), sem invadir:
  - a casa (footprint + margem)
  - o deck (sul) e o corredor das portas (faixa em x da porta), pra nao bloquear
    o walkthrough sul->norte.
Instancia LINKED (compartilha mesh) pra nao explodir memoria. Varia escala/rot.

blender --background <house_blend> --python 07_plant.py -- <asset_blend> <out_blend>
"""
import bpy, sys, os, math, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
ASSET_BLEND=argv[0]; OUT_BLEND=argv[1]
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
def log(*a): print("[plant]",*a,flush=True)

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),
        max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc
log("scene:",sc.name,"objs:",len(sc.objects))

def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])

# footprint da casa (Cube*)
mn=[1e9]*3;mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
hx0,hx1,hy0,hy1=mn[0],mx[0],mn[1],mx[1]; base_z=mn[2]
hcx,hcy=(hx0+hx1)/2,(hy0+hy1)/2
log("house x[%.2f,%.2f] y[%.2f,%.2f] base_z=%.2f"%(hx0,hx1,hy0,hy1,base_z))

# recentra + amplia o FlatGround pra envolver a casa simetricamente
RING=12.0
gz=base_z
ground=next((o for o in sc.objects if o.name=="FlatGround"),None)
halfx=(hx1-hx0)/2+RING; halfy=(hy1-hy0)/2+RING
if ground is not None:
    me=ground.data; me.clear_geometry()
    verts=[(hcx-halfx,hcy-halfy,gz),(hcx+halfx,hcy-halfy,gz),
           (hcx+halfx,hcy+halfy,gz),(hcx-halfx,hcy+halfy,gz)]
    me.from_pydata(verts,[],[(0,1,2,3)]); me.update()
    ground.location=(0,0,0); ground.rotation_euler=(0,0,0); ground.scale=(1,1,1)
gmn=[hcx-halfx,hcy-halfy,gz]; gmx=[hcx+halfx,hcy+halfy,gz]
log("ground x[%.2f,%.2f] y[%.2f,%.2f]"%(gmn[0],gmx[0],gmn[1],gmx[1]))

# --- apenda o asset (pega TODOS os meshes; eles formam 1 touceira) ---
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (src,dst):
    dst.objects=list(src.objects)
app=[o for o in dst.objects if o is not None]
src_meshes=[o for o in app if o.type=='MESH']
log("appended",len(app),"objs;",len(src_meshes),"mesh:",[o.name for o in src_meshes])

# mede bbox combinado dos meshes-fonte (sem linkar na cena: usa matrix local)
amn=[1e9]*3;amx=[-1e9]*3
for o in src_meshes:
    for c in o.bound_box:
        w=o.matrix_world@mathutils.Vector(c)
        for i in range(3): amn[i]=min(amn[i],w[i]);amx[i]=max(amx[i],w[i])
asset_h=amx[2]-amn[2]
log("asset height=%.2f"%asset_h)
target_h=2.6
base_scale=(target_h/asset_h) if asset_h>0 else 1.0
asset_base=amn[2]  # z da base do bbox combinado (no espaco do asset)

# colecao do capinzal
coll=bpy.data.collections.new("Canefield")
sc.collection.children.link(coll)

# zona proibida: casa+margem e corredor das portas (faixa x, estendida em y)
MARGIN=1.2
DOOR_X=3.1; CORR_HALF=2.0
def blocked(x,y):
    if (hx0-MARGIN)<=x<=(hx1+MARGIN) and (hy0-MARGIN)<=y<=(hy1+MARGIN): return True
    if (DOOR_X-CORR_HALF)<=x<=(DOOR_X+CORR_HALF) and (hy0-7.0)<=y<=(hy1+7.0): return True
    return False

def rnd(i,salt):
    v=math.sin(i*12.9898+salt*78.233)*43758.5453
    return v-math.floor(v)

STEP=1.25
planted=0; i=0
x=gmn[0]+0.4
while x<=gmx[0]-0.4:
    y=gmn[1]+0.4
    while y<=gmx[1]-0.4:
        i+=1
        px=x+(rnd(i,1)-0.5)*STEP*0.7
        py=y+(rnd(i,2)-0.5)*STEP*0.7
        if blocked(px,py): y+=STEP; continue
        s=base_scale*(0.8+0.45*rnd(i,3))
        rot=rnd(i,4)*math.tau
        # cria uma instancia de CADA mesh-fonte, num empty pai pra mover junto
        parent=bpy.data.objects.new(f"cane_{planted:04d}", None)
        parent.location=(px,py, gz - asset_base*s)
        parent.rotation_euler=(0,0,rot)
        parent.scale=(s,s,s)
        coll.objects.link(parent)
        for m in src_meshes:
            inst=bpy.data.objects.new(f"cane_{planted:04d}_{m.name[:6]}", m.data)
            inst.matrix_local=m.matrix_world  # posicao relativa dentro da touceira
            inst.parent=parent
            coll.objects.link(inst)
        planted+=1
        y+=STEP
    x+=STEP
log("PLANTED",planted,"clumps")

# remove os meshes-fonte originais da cena (so as instancias ficam)
for o in app:
    try:
        if o.name in bpy.context.view_layer.objects: bpy.data.objects.remove(o,do_unlink=True)
    except Exception: pass

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log("saved",OUT_BLEND)
log("PLANT_DONE planted=%d"%planted)
