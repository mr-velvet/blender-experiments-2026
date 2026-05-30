# -*- coding: utf-8 -*-
"""
experiment-28 / 03_floorplan.py
Planta baixa REAL via corte horizontal. Camera ortografica de cima com clip_start
ajustado pra fatiar a casa numa altura Z dada — corta o telhado e mostra as
paredes cortadas; os vaos nas paredes = portas/passagens. Sem ambiguidade.

Fatia em varias alturas (perto do chao ate meia altura) pra eu mapear as
aberturas. Render Workbench flat com cores por objeto, alto contraste.

Roda: blender --background <blend> --python 03_floorplan.py -- <out_dir>
"""
import bpy, sys, os, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/floorplan"
os.makedirs(OUT, exist_ok=True)

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),
        max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc

def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],
            [max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3; mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]); mx[i]=max(mx[i],b[i])
cx,cy=(mn[0]+mx[0])/2,(mn[1]+mx[1])/2
sx,sy=mx[0]-mn[0],mx[1]-mn[1]
base_z=mn[2]; top_z=mx[2]
print("CENTER",round(cx,2),round(cy,2),"BASE_Z",round(base_z,2),"TOP_Z",round(top_z,2))

# esconder set-dressing
for o in sc.objects:
    if any(o.name.startswith(p) for p in ("clouds","mist","Landscape")):
        o.hide_render=True
# esconder o chao plano pra ele nao virar um retangulo cheio cobrindo o corte
for o in sc.objects:
    if o.name=="FlatGround":
        o.hide_render=True

# Workbench flat, alto contraste
sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=1000; sc.render.resolution_y=1000
sc.render.image_settings.file_format='PNG'
try:
    sh=sc.display.shading
    sh.light='FLAT'; sh.color_type='RANDOM'; sh.show_xray=False
    sh.show_cavity=True
except Exception as e: print("shading warn",e)

# camera ortografica de cima
cd=bpy.data.cameras.new("PLAN"); cam=bpy.data.objects.new("PLAN",cd)
sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'
cam.data.ortho_scale=max(sx,sy)*1.5
cam_z=base_z+30.0
cam.location=(cx,cy,cam_z)
cam.rotation_euler=(0,0,0)

# fatias: alturas onde quero cortar (acima do chao, na faixa de porta)
slices = {
    "slice_lo": base_z+0.3,   # rente ao chao -> vaos completos
    "slice_mid": base_z+1.2,  # meia porta
    "slice_hi": base_z+2.2,   # acima das portas, pega janelas/estrutura
}
for name,zc in slices.items():
    # clip_start corta tudo entre a camera e a altura zc (incl. telhado)
    cam.data.clip_start = cam_z - zc
    cam.data.clip_end = cam_z - (base_z-0.5)  # ate um pouco abaixo da base
    sc.render.filepath=os.path.join(OUT,name+".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED",name,"z=",round(zc,2),"clip_start=",round(cam.data.clip_start,2))

print("FLOORPLAN_DONE")
