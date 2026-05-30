# -*- coding: utf-8 -*-
"""
experiment-28 / 09_find_deck.py
A porta principal tem um DECK de madeira saindo dela. O deck e o marcador
inequivoco da porta: e geometria que se projeta ALEM do footprint das paredes,
rente ao chao. Acho o deck assim:
  - footprint das paredes = bbox dos Cube* em XY
  - varro uma grade XY ampla rente ao piso (z = base_z+0.1) e faço raycast pra
    baixo curto; onde acerta casa FORA do footprint das paredes = deck.
  - o centroide desses pontos (e qual borda eles encostam) revela a porta.

Tambem identifico, entre os Cube*, qual mesh e o deck (o que tem bbox mais
plano e mais baixo, projetando-se pra fora).

Roda: blender --background <blend> --python 09_find_deck.py -- <out_json>
"""
import bpy, sys, os, json, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0] if argv else "out/deck.json"

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc
dg=bpy.context.evaluated_depsgraph_get()
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])

cubes=[o for o in sc.objects if o.type=='MESH' and o.name.lower().startswith('cube')]
mn=[1e9]*3;mx=[-1e9]*3
for o in cubes:
    a,b=wbb(o)
    for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
base_z=mn[2]; top_z=mx[2]
print("WALLS bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(mn[0],mx[0],mn[1],mx[1],base_z,top_z))

# Por-mesh: achar candidatos a deck = bbox baixo (topo perto do chao) e largo em XY
print("--- per-cube bbox (low/flat = deck candidate) ---")
deck_candidates=[]
for o in sorted(cubes,key=lambda x:x.name):
    a,b=wbb(o)
    h=b[2]-a[2]; ztop=b[2]
    flat = (ztop < base_z+0.6)   # quase no chao
    area=(b[0]-a[0])*(b[1]-a[1])
    if flat and area>1.0:
        deck_candidates.append((o.name,a,b,area))
        print("  DECK? %-8s x[%.2f,%.2f] y[%.2f,%.2f] ztop=%.2f area=%.1f"%(o.name,a[0],b[0],a[1],b[1],ztop,area))

# Footprint "nucleo" das paredes: usar mediana dos cubes altos (paredes reais)
walls=[wbb(o) for o in cubes if (wbb(o)[1][2]-wbb(o)[0][2])>1.5]
wx0=min(a[0] for a,b in walls); wx1=max(b[0] for a,b in walls)
wy0=min(a[1] for a,b in walls); wy1=max(b[1] for a,b in walls)
print("WALL CORE footprint x[%.2f,%.2f] y[%.2f,%.2f]"%(wx0,wx1,wy0,wy1))

# grade rente ao chao: acha geometria de casa que se projeta alem do nucleo (=deck)
out_pts=[]
step=0.15
x=mn[0]-2
while x<=mx[0]+2:
    y=mn[1]-3
    while y<=mx[1]+3:
        hit,loc,nrm,idx,obj,m=sc.ray_cast(dg,mathutils.Vector((x,y,base_z+1.0)),mathutils.Vector((0,0,-1)),distance=2.0)
        if hit and obj and obj.name.lower().startswith('cube'):
            # esta fora do nucleo das paredes em Y? (deck sai pra frente)
            outside = (y<wy0-0.2) or (y>wy1+0.2) or (x<wx0-0.2) or (x>wx1+0.2)
            if outside and loc.z < base_z+0.6:
                out_pts.append((loc.x,loc.y,loc.z))
        y+=step
    x+=step
print("DECK projecting points:",len(out_pts))
res={"walls_bbox":{"min":[round(v,3) for v in mn],"max":[round(v,3) for v in mx]},
     "wall_core":{"x":[round(wx0,3),round(wx1,3)],"y":[round(wy0,3),round(wy1,3)]},
     "base_z":round(base_z,3),"top_z":round(top_z,3)}
if out_pts:
    xs=[p[0] for p in out_pts]; ys=[p[1] for p in out_pts]
    res["deck"]={"x":[round(min(xs),3),round(max(xs),3)],"y":[round(min(ys),3),round(max(ys),3)],
                 "cx":round(sum(xs)/len(xs),3),"cy":round(sum(ys)/len(ys),3),"n":len(out_pts)}
    # qual borda o deck encosta -> porta
    if res["deck"]["y"][0] < wy0:  side="S(-Y)"
    elif res["deck"]["y"][1] > wy1: side="N(+Y)"
    elif res["deck"]["x"][0] < wx0: side="W(-X)"
    else: side="E(+X)"
    res["door_side"]=side
    # X (ou Y) da porta = centro do deck na direcao paralela a parede
    if side.startswith("S") or side.startswith("N"):
        res["door_axis_pos"]={"x":res["deck"]["cx"]}
    else:
        res["door_axis_pos"]={"y":res["deck"]["cy"]}
    print("DECK bbox x",res["deck"]["x"],"y",res["deck"]["y"],"center",res["deck"]["cx"],res["deck"]["cy"])
    print("DOOR SIDE:",side,"door pos:",res["door_axis_pos"])
else:
    print("NO DECK PTS")

os.makedirs(os.path.dirname(os.path.abspath(OUT)),exist_ok=True)
with open(OUT,"w",encoding="utf-8") as f: json.dump(res,f,indent=2)
print("FIND_DECK_DONE")
print(json.dumps(res))
