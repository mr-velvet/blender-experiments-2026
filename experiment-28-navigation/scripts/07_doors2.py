# -*- coding: utf-8 -*-
"""
experiment-28 / 07_doors2.py  (detector de portas correto)
Para CADA uma das 4 paredes, varro a fachada com raios horizontais vindos de
fora, mirando pra dentro, na altura de porta. Para cada amostra meco a
DISTANCIA do primeiro hit na casa.
  - parede solida  -> hit raso (raio bate na superficie externa logo)
  - vao (porta)    -> hit fundo (raio entra e so bate na parede oposta) OU nenhum hit
Acho, em cada parede, a maior corrida continua de amostras "fundas" e seu
centro. A parede com o vao mais largo e a entrada; reporto todas.

Tambem acho o piso interno de verdade: raycast pra baixo de varios pontos
internos e pega o Z mais BAIXO consistente (ignora telhado).

Roda: blender --background <blend> --python 07_doors2.py -- <out_json>
"""
import bpy, sys, os, json, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/doors2.json"

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
W=mx[0]-mn[0]; D=mx[1]-mn[1]
print("BBOX x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(mn[0],mx[0],mn[1],mx[1],base_z,top_z))

door_zs=[base_z+z for z in (0.5,0.9,1.3,1.7)]
MAXD = max(W,D)+3.0   # raio cruza a casa toda
DEEP = min(W,D)*0.5   # hit "fundo" = entrou mais que meia casa (passou da parede externa)

def first_hit_dist(origin, direction):
    hit,loc,nrm,idx,obj,m = sc.ray_cast(dg, mathutils.Vector(origin), mathutils.Vector(direction), distance=MAXD)
    if hit and obj and obj.name in house:
        return (mathutils.Vector(loc)-mathutils.Vector(origin)).length
    return None  # nenhum hit na casa = totalmente aberto

def sample_deep(origin, direction):
    # 'fundo' se a media das alturas entra alem da casca externa (ou nao bate)
    deep=0
    for z in door_zs:
        o=(origin[0],origin[1],z)
        d=first_hit_dist(o,direction)
        if d is None or d>=DEEP+ (1.5 if True else 0):  # entrou fundo
            deep+=1
    return deep/len(door_zs)

def scan_wall(axis, side):
    """axis 'x' -> parede perpendicular a X (leste/oeste); varre Y.
       axis 'y' -> parede perpendicular a Y (norte/sul); varre X.
       side +1/-1: de qual lado vem o raio."""
    samples=[]
    if axis=='y':
        from_y = (mx[1]+1.0) if side>0 else (mn[1]-1.0)
        dirv = (0,-side,0)
        coords=[mn[0]+i*0.12 for i in range(int(W/0.12)+1)]
        for px in coords:
            samples.append((px, sample_deep((px,from_y,0),dirv)))
    else:
        from_x = (mx[0]+1.0) if side>0 else (mn[0]-1.0)
        dirv = (-side,0,0)
        coords=[mn[1]+i*0.12 for i in range(int(D/0.12)+1)]
        for py in coords:
            samples.append((py, sample_deep((from_x,py,0),dirv)))
    # maior corrida com deep>=0.5 mas NAO nas pontas (porta nao e a quina aberta)
    lo=coords[0]; hi=coords[-1]
    inner=[(c,d) for c,d in samples if c>lo+0.4 and c<hi-0.4]
    best=None; cur=[]
    for c,d in inner:
        if d>=0.5:
            cur.append(c)
        else:
            if cur and (best is None or len(cur)>len(best)): best=cur
            cur=[]
    if cur and (best is None or len(cur)>len(best)): best=cur
    if not best: return None
    return {"center":round((best[0]+best[-1])/2,3),"span":[round(best[0],3),round(best[-1],3)],
            "width":round(best[-1]-best[0],3)}

walls={
 "N":("y",+1, mx[1]),
 "S":("y",-1, mn[1]),
 "E":("x",+1, mx[0]),
 "W":("x",-1, mn[0]),
}
res={"bbox":{"min":[round(v,3) for v in mn],"max":[round(v,3) for v in mx]},
     "center":[round(cx,3),round(cy,3)],"base_z":round(base_z,3),"top_z":round(top_z,3)}
for name,(axis,side,coord) in walls.items():
    g=scan_wall(axis,side)
    if g:
        if axis=='y': g["pos"]=[g["center"],round(coord,3)]
        else:         g["pos"]=[round(coord,3),g["center"]]
        print("WALL",name,"gap width=%.2f center=%.2f pos=%s"%(g["width"],g["center"],g["pos"]))
    else:
        print("WALL",name,"-> no gap")
    res[name]=g

# piso interno: amostra grade interna, raycast pra baixo, pega Z mais baixo robusto
floor_zs=[]
for i in range(5):
    for j in range(5):
        px=mn[0]+W*(0.25+0.12*i); py=mn[1]+D*(0.25+0.12*j)
        hit,loc,nrm,idx,obj,m=sc.ray_cast(dg,mathutils.Vector((px,py,base_z+0.05)),mathutils.Vector((0,0,1)),distance=top_z-base_z)
        # raio pra cima a partir de quase o chao: 1o hit e o teto/parede; em vez disso pega o piso por baixo
        hit2,loc2,nrm2,idx2,obj2,m2=sc.ray_cast(dg,mathutils.Vector((px,py,base_z+1.5)),mathutils.Vector((0,0,-1)),distance=4.0)
        if hit2 and obj2 and obj2.name in house:
            floor_zs.append(loc2.z)
if floor_zs:
    floor_zs.sort()
    res["floor_z_inside"]=round(floor_zs[len(floor_zs)//2],3)  # mediana
else:
    res["floor_z_inside"]=round(base_z,3)
print("FLOOR_Z_INSIDE",res["floor_z_inside"],"samples",len(floor_zs))

os.makedirs(os.path.dirname(os.path.abspath(OUT)),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f: json.dump(res,f,indent=2)
print("DOORS2_DONE")
print(json.dumps({k:res[k] for k in ("N","S","E","W","floor_z_inside")}))
