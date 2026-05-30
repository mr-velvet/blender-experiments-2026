# -*- coding: utf-8 -*-
"""
exp-30 / 06_make_variant.py — monta UMA variante de grama/mato em volta da casa.
Duas camadas:
  GROUND COVER: scatter denso de um asset baixo (grama rasteira) cobrindo todo o
                terreno em volta da casa -> vira "solo gramado" de verdade.
  TALL LAYER:   touceiras altas (pampas/bambu/...) esparsas por cima.
Material do chao: deixa um verde-terra fosco por baixo (caso apareca entre a grama).
Preserva corredor das portas + clareira da casa.

Config via JSON inline no argv:
blender --background <house_blend> --python 06_make_variant.py -- <out_blend> <cfg_json>

cfg = {
  "name": "v2_wildgrass_pampas",
  "ground": {"blend": "<path>", "step": 0.55, "scale": [1.0,1.6], "clear_corridor": true},
  "tall":   {"blend": "<path>", "step": 1.4,  "scale_target_h": 2.4, "density": 0.6},
  "ground_color": [0.18,0.22,0.10]
}
'tall' pode ser null (so cobertura). 'ground' pode ser null (so alto).
"""
import bpy, sys, os, math, mathutils, json
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT_BLEND=argv[0]; CFG=json.loads(argv[1])
os.makedirs(os.path.dirname(OUT_BLEND),exist_ok=True)
def log(*a): print("[var]",*a,flush=True)

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc

def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])

# footprint casa
mn=[1e9]*3;mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
hx0,hx1,hy0,hy1=mn[0],mx[0],mn[1],mx[1]; base_z=mn[2]
hcx,hcy=(hx0+hx1)/2,(hy0+hy1)/2
RING=12.0; gz=base_z
halfx=(hx1-hx0)/2+RING; halfy=(hy1-hy0)/2+RING
ground=next((o for o in sc.objects if o.name=="FlatGround"),None)
if ground is not None:
    me=ground.data; me.clear_geometry()
    verts=[(hcx-halfx,hcy-halfy,gz),(hcx+halfx,hcy-halfy,gz),(hcx+halfx,hcy+halfy,gz),(hcx-halfx,hcy+halfy,gz)]
    me.from_pydata(verts,[],[(0,1,2,3)]); me.update()
    ground.location=(0,0,0); ground.rotation_euler=(0,0,0); ground.scale=(1,1,1)
    # material de solo fosco verde-terra
    gc=CFG.get("ground_color",[0.18,0.2,0.1])
    m=bpy.data.materials.new("SoilMat"); m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(gc[0],gc[1],gc[2],1)
        if "Roughness" in bsdf.inputs: bsdf.inputs["Roughness"].default_value=0.95
    ground.data.materials.clear(); ground.data.materials.append(m)
gmn=[hcx-halfx,hcy-halfy]; gmx=[hcx+halfx,hcy+halfy]
log("ground x[%.2f,%.2f] y[%.2f,%.2f]"%(gmn[0],gmx[0],gmn[1],gmx[1]))

DOOR_X=3.1; CORR_HALF=2.0; MARGIN=1.0
def blocked(x,y,corridor=True):
    if (hx0-MARGIN)<=x<=(hx1+MARGIN) and (hy0-MARGIN)<=y<=(hy1+MARGIN): return True
    if corridor and (DOOR_X-CORR_HALF)<=x<=(DOOR_X+CORR_HALF) and (hy0-7.0)<=y<=(hy1+7.0): return True
    return False
def rnd(i,s): v=math.sin(i*12.9898+s*78.233)*43758.5453; return v-math.floor(v)

def load_asset_meshes(blend):
    with bpy.data.libraries.load(blend, link=False) as (src,dst):
        dst.objects=list(src.objects)
    app=[o for o in dst.objects if o is not None]
    meshes=[o for o in app if o.type=='MESH']
    # remove vaso/base: descarta meshes muito "chatos e largos" perto do chao se houver alto junto
    return app, meshes

def asset_bbox(meshes):
    amn=[1e9]*3;amx=[-1e9]*3
    for o in meshes:
        for c in o.bound_box:
            w=o.matrix_world@mathutils.Vector(c)
            for i in range(3): amn[i]=min(amn[i],w[i]);amx[i]=max(amx[i],w[i])
    return amn,amx

def scatter(layer_cfg, layer_name, corridor, tall):
    app,meshes=load_asset_meshes(layer_cfg["blend"])
    if not meshes: log("no mesh in",layer_name); return 0
    # se for camada alta, descarta vaso/pedra/base:
    #  (a) por nome (stone/pot/vase/rock/base/ground)
    #  (b) por forma: mantem so meshes VERTICAIS (altura/largura > 0.9)
    if tall:
        log("  raw meshes:",[o.name for o in meshes])
        GOODNAME=("plant","bamboo","grass","cane","reed","stalk","leaf","flower","fern")
        BADNAME=("stone","pot","vase","rock","base","ground","soil","dirt","plate","dish")
        # 1) se algum mesh tem nome de planta, WHITELIST so esses (mais robusto)
        whitelist=[o for o in meshes if any(g in o.name.lower() for g in GOODNAME)]
        if whitelist:
            log("  whitelist por nome:",[o.name for o in whitelist])
            meshes=whitelist
        else:
            # 2) fallback: blacklist por nome
            meshes=[o for o in meshes if not any(b in o.name.lower() for b in BADNAME)] or meshes
        log("  meshes apos filtro:",[o.name for o in meshes])
    amn,amx=asset_bbox(meshes); H=amx[2]-amn[2]; abase=amn[2]
    if tall and layer_cfg.get("scale_target_h"):
        base_scale=layer_cfg["scale_target_h"]/H if H>0 else 1.0
    else:
        base_scale=1.0
    coll=bpy.data.collections.new(layer_name); sc.collection.children.link(coll)
    step=layer_cfg["step"]; smin,smax=layer_cfg.get("scale",[0.9,1.3]) if not tall else [0.8,1.25]
    dens=layer_cfg.get("density",1.0)
    n=0; i=0; x=gmn[0]+0.3
    while x<=gmx[0]-0.3:
        y=gmn[1]+0.3
        while y<=gmx[1]-0.3:
            i+=1
            if rnd(i, 7 if tall else 3) > dens: y+=step; continue
            px=x+(rnd(i,1)-0.5)*step*0.8; py=y+(rnd(i,2)-0.5)*step*0.8
            if blocked(px,py,corridor): y+=step; continue
            s=base_scale*(smin+(smax-smin)*rnd(i,3))
            parent=bpy.data.objects.new(f"{layer_name}_{n:05d}",None)
            parent.location=(px,py, gz - abase*s); parent.rotation_euler=(0,0,rnd(i,4)*math.tau); parent.scale=(s,s,s)
            coll.objects.link(parent)
            for m in meshes:
                inst=bpy.data.objects.new(f"{layer_name}_{n:05d}_{m.name[:5]}", m.data)
                inst.matrix_local=m.matrix_world; inst.parent=parent; coll.objects.link(inst)
            n+=1; y+=step
        x+=step
    # remove fontes
    for o in app:
        try:
            if o.name in bpy.context.view_layer.objects: bpy.data.objects.remove(o,do_unlink=True)
        except Exception: pass
    log(layer_name,"scattered",n)
    return n

total=0
if CFG.get("ground"):
    total+=scatter(CFG["ground"],"cover", CFG["ground"].get("clear_corridor",True), tall=False)
if CFG.get("tall"):
    total+=scatter(CFG["tall"],"tall", True, tall=True)
log("TOTAL instances",total)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log("saved",OUT_BLEND,"VARIANT_DONE",CFG.get("name"))
