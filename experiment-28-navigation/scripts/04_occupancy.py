# -*- coding: utf-8 -*-
"""
experiment-28 / 04_occupancy.py
Mapa de ocupacao ASCII da casa na altura da porta, via ray casting.
Pra cada celula de uma grade no plano XY (na altura z), testo se ha parede ali
lancando um raio vertical curto pra cima e pra baixo e vendo se acerta mesh da
casa. '#' = parede/solido, '.' = vazio (interior ou exterior).
Os vaos no contorno = portas. Sem leitura de imagem, coordenadas exatas.

Roda: blender --background <blend> --python 04_occupancy.py -- <out_txt> <z>
"""
import bpy, sys, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/occ.txt"
ZSLICE = float(argv[1]) if len(argv) > 1 else None

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),
        max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc
dg=bpy.context.evaluated_depsgraph_get()

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
base_z=mn[2]; top_z=mx[2]
if ZSLICE is None: ZSLICE=base_z+1.0
print("BBOX x[%.2f,%.2f] y[%.2f,%.2f] base_z=%.2f top_z=%.2f Z=%.2f"%(mn[0],mx[0],mn[1],mx[1],base_z,top_z,ZSLICE))

# so a casa (Cube*) conta como parede; esconder o resto da deteccao via mascara
house_objs=set(o.name for o in sc.objects if o.type=='MESH' and o.name.lower().startswith('cube'))

# grade
PAD=1.5
x0,x1=mn[0]-PAD,mx[0]+PAD
y0,y1=mn[1]-PAD,mx[1]+PAD
STEP=0.25
nx=int((x1-x0)/STEP)+1
ny=int((y1-y0)/STEP)+1

def wall_at(px,py,z):
    # raio curto pra cima a partir de um pouco abaixo de z; se acertar casa perto, ha parede
    origin=mathutils.Vector((px,py,z-0.05))
    direction=mathutils.Vector((0,0,1))
    hit,loc,nrm,idx,obj,m = sc.ray_cast(dg, origin, direction, distance=0.6)
    if hit and obj and obj.name in house_objs:
        return True
    # tambem pra baixo (telhados inclinados/pisos)
    hit2,loc2,nrm2,idx2,obj2,m2 = sc.ray_cast(dg, origin, mathutils.Vector((0,0,-1)), distance=0.6)
    if hit2 and obj2 and obj2.name in house_objs:
        return True
    return False

rows=[]
# y decrescente em linhas pra ficar com +Y em cima (norte em cima)
header="    X-> x0=%.2f x1=%.2f  (step %.2f, '#'=parede)  +Y(N) em cima"%(x0,x1,STEP)
for j in range(ny):
    py=y1 - j*STEP
    line=[]
    for i in range(nx):
        px=x0 + i*STEP
        line.append('#' if wall_at(px,py,ZSLICE) else '.')
    rows.append("".join(line))

txt=header+"\n"+"\n".join(rows)
# legenda de eixos: imprime coords das bordas
txt+="\n\nLEGEND: linha0 y=%.2f (N) ... ultima y=%.2f (S); col0 x=%.2f (W) ... ultima x=%.2f (E)"%(y1,y0,x0,x1)
txt+="\ncenter=(%.2f,%.2f) STEP=%.2f nx=%d ny=%d Z=%.2f"%(cx,cy,STEP,nx,ny,ZSLICE)

import os
os.makedirs(os.path.dirname(os.path.abspath(OUT)),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f: f.write(txt)
print(txt)
print("OCC_DONE",OUT)
