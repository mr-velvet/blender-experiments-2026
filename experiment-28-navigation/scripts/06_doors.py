# -*- coding: utf-8 -*-
"""
experiment-28 / 06_doors.py
Detecta os VAOS (portas) nas paredes sul (-Y) e norte (+Y) da casa por raycast
HORIZONTAL. Pra cada parede, varro X numa faixa de alturas e lanco um raio na
direcao da parede; onde os raios PASSAM DIRETO (nao batem na casa) ao longo de
uma faixa vertical de altura de porta = vao. Acho o centro X do maior vao
continuo em cada parede. Coordenadas exatas, sem ler imagem.

Tambem mede o piso interno (z do chao interno) e a profundidade util em Y.
Salva doors.json.

Roda: blender --background <blend> --python 06_doors.py -- <out_json>
"""
import bpy, sys, os, json, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/doors.json"

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
house=set(o.name for o in sc.objects if o.type=='MESH' and o.name.lower().startswith('cube'))
print("BBOX x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(mn[0],mx[0],mn[1],mx[1],base_z,top_z))

def hits_house(origin, direction, dist):
    hit,loc,nrm,idx,obj,m = sc.ray_cast(dg, mathutils.Vector(origin), mathutils.Vector(direction), distance=dist)
    return hit and obj and obj.name in house

# alturas de "porta": de um pouco acima do chao ate ~2m
door_zs = [base_z+z for z in (0.4, 0.8, 1.2, 1.6, 2.0)]
# faixa X varrida (so dentro do footprint)
xs = [mn[0] + i*0.15 for i in range(int((mx[0]-mn[0])/0.15)+1)]
span_y = (mx[1]-mn[1]) + 2.0  # raio cruza a casa inteira

def open_fraction(px, shoot_from_y, direction_y):
    # fracao das alturas de porta em que o raio NAO bate em parede ao cruzar
    free=0
    for z in door_zs:
        origin=(px, shoot_from_y, z)
        if not hits_house(origin,(0,direction_y,0), span_y):
            free+=1
    return free/len(door_zs)

def find_gap(wall):
    # wall='S' (-Y): atira de fora do sul (y=mn-1) pra +Y
    # wall='N' (+Y): atira de fora do norte (y=mx+1) pra -Y
    if wall=='S':
        from_y=mn[1]-1.0; dir_y=1.0
    else:
        from_y=mx[1]+1.0; dir_y=-1.0
    profile=[(px, open_fraction(px, from_y, dir_y)) for px in xs]
    # maior corrida continua de open_fraction alto (>=0.6 = vao real, nao so fresta)
    best=None; cur=[]
    for px,f in profile:
        if f>=0.6:
            cur.append(px)
        else:
            if len(cur)>0:
                if best is None or len(cur)>len(best): best=cur
                cur=[]
    if len(cur)>0 and (best is None or len(cur)>len(best)): best=cur
    if not best: return None,profile
    return (best[0]+best[-1])/2.0, profile, (best[0],best[-1])

res={"bbox":{"min":[round(v,3) for v in mn],"max":[round(v,3) for v in mx]},
     "center":[round(cx,3),round(cy,3)],"base_z":round(base_z,3),"top_z":round(top_z,3)}
for wall,ylabel in (('S',mn[1]),('N',mx[1])):
    out=find_gap(wall)
    if out[0] is None:
        print("WALL",wall,"-> NO GAP FOUND")
        res[wall]={"found":False}
    else:
        gx,prof,(x0,x1)=out
        print("WALL",wall,"gap center x=%.2f  span x[%.2f,%.2f]  at y=%.2f"%(gx,x0,x1,ylabel))
        res[wall]={"found":True,"door_x":round(gx,3),"door_y":round(ylabel,3),
                   "span_x":[round(x0,3),round(x1,3)]}

# z do piso interno: raycast pra baixo do centro
hit,loc,nrm,idx,obj,m = sc.ray_cast(dg, mathutils.Vector((cx,cy,top_z+1)), mathutils.Vector((0,0,-1)), distance=top_z-base_z+5)
res["floor_z_inside"]=round(loc.z,3) if hit else round(base_z,3)
print("FLOOR_Z_INSIDE",res["floor_z_inside"])

os.makedirs(os.path.dirname(os.path.abspath(OUT)),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f: json.dump(res,f,indent=2)
print("DOORS_DONE",OUT)
print(json.dumps(res))
