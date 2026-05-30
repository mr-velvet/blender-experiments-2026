# -*- coding: utf-8 -*-
"""
experiment-28 / 02_orient.py
Renderiza prints de ORIENTACAO pra eu (agente) achar as portas da casa, ja que
nao tenho visao em tempo real. Substitui a falta de visao: print -> analiso ->
ajusto. Esconde o set-dressing gigante (clouds/mist/Landscape) pra nao poluir.

Vistas:
  - top: ortografica de cima (planta baixa) -> mostra o footprint e os vaos
  - N/E/S/W: cameras ao nivel ~1.6m (altura de olho) afastadas, mirando o centro

Render rapido EEVEE, baixa amostragem, so pra leitura.
Roda: blender --background <blend> --python 02_orient.py -- <out_dir>
"""
import bpy, sys, os, math, mathutils

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "out/orient"
os.makedirs(OUT, exist_ok=True)

SCENE = "The Lonely Outpost"
sc = next((s for s in bpy.data.scenes if s.name == SCENE),
          max(bpy.data.scenes, key=lambda s: len(s.objects)))
bpy.context.window.scene = sc

# centro/size da casa (Cube*)
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

# esconder set-dressing gigante do render pra leitura limpa
HIDE_PREFIX = ("clouds","mist","Landscape")
for o in sc.objects:
    if any(o.name.startswith(p) for p in HIDE_PREFIX):
        o.hide_render = True

# render settings rapidos: EEVEE (nome do engine varia entre versoes)
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng
        break
    except Exception:
        continue
print("ENGINE", sc.render.engine)
sc.render.resolution_x = 960
sc.render.resolution_y = 720
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = 16
except Exception:
    pass

# luz garantida (a Spot existe, mas adiciono um sol fraco pra leitura clara)
sun_data = bpy.data.lights.new("OrientSun", 'SUN'); sun_data.energy=2.0
sun = bpy.data.objects.new("OrientSun", sun_data)
sun.rotation_euler = (math.radians(55), 0, math.radians(40))
sc.collection.objects.link(sun)

def make_cam(name):
    cd = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    return cam

def look_at(cam, target):
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()

def render_to(cam, path):
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)

radius = max(sx, sy) * 1.4
eye = base_z + 1.6

shots = []
# TOP ortografico
topcam = make_cam("ORI_TOP")
topcam.data.type='ORTHO'
topcam.data.ortho_scale = max(sx,sy)*1.6
topcam.location = (cx, cy, base_z + max(sx,sy)*2.0)
topcam.rotation_euler = (0,0,0)  # olhando reto pra baixo
shots.append((topcam, os.path.join(OUT,"top.png")))

# 4 lados (N=+Y, S=-Y, E=+X, W=-X), mirando o centro da casa na altura do meio
mid = (cx, cy, base_z + sz*0.45)
for name,dx,dy in [("N",0,1),("S",0,-1),("E",1,0),("W",-1,0)]:
    c = make_cam("ORI_"+name)
    c.location = (cx + dx*radius, cy + dy*radius, eye + 0.8)
    look_at(c, mid)
    c.data.lens = 28  # grande angular pra pegar a fachada inteira
    shots.append((c, os.path.join(OUT, name+".png")))

for cam, path in shots:
    render_to(cam, path)

print("ORIENT_DONE")
