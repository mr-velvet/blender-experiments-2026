# -*- coding: utf-8 -*-
"""
experiment-28 / 11_tour.py
Camera animada: walkthrough entrando pela porta SUL, atravessando o interior,
saindo pela abertura NORTE. Coordenadas cravadas nas etapas anteriores:
  linha de trajeto x ~= 3.1 (centro das duas portas)
  porta sul y ~= 21 (com deck), abertura norte y ~= 31
  piso interno z ~= -1.73 ; altura do olho = piso + 1.6
Movimento suave (bezier, ease in/out via auto handles).

Modos:
  --test : renderiza so 3 frames-chave (inicio/meio/fim) p/ validar enquadramento
  default: anima e renderiza o MP4 inteiro

Roda:
  blender --background <blend> --python 11_tour.py -- <out_dir> [test|full] [engine] [secs] [fps] [resx]
"""
import bpy, sys, os, math, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT   = argv[0] if len(argv)>0 else "out/tour"
MODE  = argv[1] if len(argv)>1 else "full"
ENGINE= argv[2] if len(argv)>2 else "EEVEE"
SECS  = float(argv[3]) if len(argv)>3 else 14.0
FPS   = int(argv[4]) if len(argv)>4 else 30
RESX  = int(argv[5]) if len(argv)>5 else 1280
os.makedirs(OUT,exist_ok=True)

SCENE="The Lonely Outpost"
sc=next((s for s in bpy.data.scenes if s.name==SCENE),max(bpy.data.scenes,key=lambda s:len(s.objects)))
bpy.context.window.scene=sc

# As cascas 'clouds'/'mist' envolvem a cena inteira e deixam a camera por dentro
# (frames pretos). Esconde do render. Mantem 'Landscape' (montanhas ao fundo,
# visiveis pelas portas) e mantem o world/luz originais do asset.
hidden=[]
for o in sc.objects:
    if o.name.startswith("clouds") or o.name.startswith("mist"):
        o.hide_render=True; hidden.append(o.name)
print("HIDDEN set-dressing:",hidden)

# garante iluminacao: o asset tem uma Spot; adiciono um sol suave de apoio
import math as _m
_sd=bpy.data.lights.new("TourSun",'SUN'); _sd.energy=2.5
_su=bpy.data.objects.new("TourSun",_sd)
_su.rotation_euler=(_m.radians(52),_m.radians(8),_m.radians(35))
sc.collection.objects.link(_su)
# garante um world minimamente claro caso o original esteja escuro
if sc.world is None:
    _w=bpy.data.worlds.new("TourSky"); _w.use_nodes=True
    sc.world=_w
try:
    _bg=sc.world.node_tree.nodes.get("Background")
    if _bg and _bg.inputs["Strength"].default_value < 0.3:
        _bg.inputs["Strength"].default_value=0.6
except Exception as _e:
    print("world warn",_e)

# medidas (recalcula pra robustez)
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
mn=[1e9]*3;mx=[-1e9]*3
for o in sc.objects:
    if o.type=='MESH' and o.name.lower().startswith('cube'):
        a,b=wbb(o)
        for i in range(3): mn[i]=min(mn[i],a[i]);mx[i]=max(mx[i],b[i])
base_z=mn[2]
DOOR_X=3.1
Y_SOUTH=mn[1]        # ~21
Y_NORTH=mx[1]        # ~31
FLOOR_Z=-1.73
EYE=FLOOR_Z+1.55
print("TRAJ x=%.2f y[%.2f->%.2f] eye_z=%.2f"%(DOOR_X,Y_SOUTH,Y_NORTH,EYE))

# interpolacao default das proximas keyframes = bezier suave (ease in/out)
try:
    bpy.context.preferences.edit.keyframe_new_interpolation_type='BEZIER'
    bpy.context.preferences.edit.keyframe_new_handle_type='AUTO_CLAMPED'
except Exception as e:
    print("kf pref warn",e)

# camera nova
cd=bpy.data.cameras.new("TourCam"); cam=bpy.data.objects.new("TourCam",cd)
sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=24  # levemente grande-angular, sensacao de interior
cam.data.clip_start=0.02
cam.data.clip_end=2000

# keyframes de posicao: (frame_frac, x, y, z) e alvo (olhar)
total_frames=int(SECS*FPS)
sc.frame_start=1; sc.frame_end=total_frames
# pontos do percurso ao longo de +Y. leve curva em X e leve subida/descida pra dar vida
pts=[
 # frac    x          y              z
 (0.00, DOOR_X-0.2, Y_SOUTH-6.5, EYE+0.15),  # fora, encarando o deck/porta sul
 (0.18, DOOR_X,     Y_SOUTH-2.2, EYE),       # subindo o deck
 (0.32, DOOR_X,     Y_SOUTH+0.3, EYE-0.05),  # cruzando a soleira da porta sul
 (0.55, DOOR_X+0.15,(Y_SOUTH+Y_NORTH)/2, EYE),# meio do interior
 (0.78, DOOR_X,     Y_NORTH-0.3, EYE-0.05),  # cruzando a abertura norte
 (1.00, DOOR_X-0.1, Y_NORTH+6.0, EYE+0.1),   # fora, do lado norte
]
def set_kf(frame, loc):
    cam.location=loc
    cam.keyframe_insert("location", frame=frame)

# olhar: sempre um pouco a frente no caminho (look-ahead), com leve panoramica
def look_target(frac):
    # alvo = ponto adiante em +Y, na linha x, altura do olho (olhar levemente p/ baixo no interior)
    ahead = 4.0
    y = (Y_SOUTH-6.5) + frac*((Y_NORTH+6.0)-(Y_SOUTH-6.5)) + ahead
    z = EYE - 0.15
    x = DOOR_X
    return mathutils.Vector((x,y,z))

# usa um Empty como alvo + Track To, animando o Empty (olhar suave)
tgt_data=None
tgt=bpy.data.objects.new("TourTarget",None); sc.collection.objects.link(tgt)
con=cam.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'

for frac,x,y,z in pts:
    f=max(1,int(frac*total_frames))
    set_kf(f,(x,y,z))
    tgt.location=look_target(frac)
    tgt.keyframe_insert("location",frame=f)

# suavizar: ja inserido como BEZIER/AUTO_CLAMPED via preferences acima.
# (No Blender 5.1 Action.fcurves foi removido em favor de slotted actions;
#  setar a interpolacao default antes de inserir e o caminho robusto.)

# --- engine / qualidade ---
if ENGINE.upper().startswith("CYCLES"):
    sc.render.engine='CYCLES'
    sc.cycles.samples=64
    try: sc.cycles.use_denoising=True
    except Exception: pass
else:
    for e in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE'):
        try: sc.render.engine=e; break
        except Exception: continue
    try:
        sc.eevee.taa_render_samples=32
        sc.eevee.use_gtao=True
    except Exception as ex: print("eevee opt warn",ex)
print("ENGINE",sc.render.engine)

sc.render.resolution_x=RESX
sc.render.resolution_y=int(RESX*9/16)
sc.render.fps=FPS
# AgX look (bom default do asset)
try: sc.view_settings.view_transform='AgX'
except Exception: pass

if MODE=="test":
    sc.render.image_settings.file_format='PNG'
    for frac in (0.0,0.32,0.55,0.78,1.0):
        f=max(1,int(frac*total_frames))
        sc.frame_set(f)
        sc.render.filepath=os.path.join(OUT,f"test_{int(frac*100):03d}.png")
        bpy.ops.render.render(write_still=True)
        print("TEST FRAME",f,"frac",frac)
    print("TOUR_TEST_DONE")
else:
    # Blender 5.1 deste build nao expoe FFMPEG no enum de saida -> renderizo
    # SEQUENCIA PNG e encodo o MP4 fora (imageio-ffmpeg). Robusto e portavel.
    frames_dir=os.path.join(OUT,"frames")
    os.makedirs(frames_dir,exist_ok=True)
    sc.render.image_settings.file_format='PNG'
    sc.render.filepath=os.path.join(frames_dir,"f_")  # f_0001.png ...
    print("RENDERING",total_frames,"PNG frames ->",frames_dir)
    bpy.ops.render.render(animation=True)
    print("TOUR_FRAMES_DONE",frames_dir)
