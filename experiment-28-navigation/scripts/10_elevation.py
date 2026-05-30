# -*- coding: utf-8 -*-
"""
experiment-28 / 10_elevation.py
Elevacao ortografica da fachada SUL (camera olhando +Y, reta, sem perspectiva),
com regua de X (linhas verticais a cada 1m, rotuladas) sobreposta na frente da
casa. Leio o X da porta direto na regua. Tambem faco a fachada NORTE.

Roda: blender --background <blend> --python 10_elevation.py -- <out_dir>
"""
import bpy, sys, os, math, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0] if argv else "out/elev"
os.makedirs(OUT,exist_ok=True)

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
print("BBOX x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(mn[0],mx[0],mn[1],mx[1],base_z,top_z))

for o in sc.objects:
    if any(o.name.startswith(p) for p in ("clouds","mist","Landscape")) or o.name=="FlatGround":
        o.hide_render=True

# luz + world claro
w=bpy.data.worlds.new("W"); w.use_nodes=True
bg=w.node_tree.nodes.get("Background")
if bg: bg.inputs["Color"].default_value=(0.7,0.74,0.8,1); bg.inputs["Strength"].default_value=1.4
sc.world=w
sd=bpy.data.lights.new("S",'SUN'); sd.energy=4.0
su=bpy.data.objects.new("S",sd); su.rotation_euler=(math.radians(50),0,math.radians(20))
sc.collection.objects.link(su)

# regua de X: linhas verticais (no plano XZ) na frente de cada fachada
red=bpy.data.materials.new("red"); red.use_nodes=False; red.diffuse_color=(1,0.1,0.1,1)
def vline(x,y,z0,z1,wdt=0.025):
    me=bpy.data.meshes.new("VL"); ob=bpy.data.objects.new("VL",me); sc.collection.objects.link(ob)
    verts=[(x-wdt,y,z0),(x+wdt,y,z0),(x+wdt,y,z1),(x-wdt,y,z1)]
    me.from_pydata(verts,[],[(0,1,2,3)]); me.update(); ob.data.materials.append(red); return ob
def label(txt,x,y,z,size=0.4):
    cu=bpy.data.curves.new("t",'FONT'); cu.body=txt; cu.size=size
    ob=bpy.data.objects.new("t",cu); sc.collection.objects.link(ob)
    ob.location=(x,y,z); ob.data.materials.append(red); return ob

gx0=math.floor(mn[0]-1); gx1=math.ceil(mx[0]+1)

# regua na fachada sul (y um pouco a frente, -Y) e norte (+Y)
rulers=[]
y_south=mn[1]-0.5; y_north=mx[1]+0.5
for x in range(gx0,gx1+1):
    rulers.append(vline(x,y_south,base_z,base_z+0.8,0.04 if x%5 else 0.07))
    rulers.append(label(str(x),x-0.12,y_south,base_z-0.6))

sc.render.engine='BLENDER_WORKBENCH'
try:
    sh=sc.display.shading; sh.light='STUDIO'; sh.color_type='TEXTURE'; sh.show_shadows=True
except Exception as e: print("shade",e)
sc.render.resolution_x=1300; sc.render.resolution_y=900
sc.render.image_settings.file_format='PNG'

def make_cam(name):
    cd=bpy.data.cameras.new(name); cam=bpy.data.objects.new(name,cd); sc.collection.objects.link(cam)
    cam.data.type='ORTHO'; cam.data.ortho_scale=(gx1-gx0)+2
    return cam

# fachada SUL: camera ao sul olhando +Y (norte)
cs=make_cam("ELEV_S")
cs.location=(cx, mn[1]-15, base_z+ (top_z-base_z)*0.45)
cs.rotation_euler=(math.radians(90),0,0)  # olha +Y
sc.camera=cs; sc.render.filepath=os.path.join(OUT,"south.png")
bpy.ops.render.render(write_still=True); print("RENDERED south (fachada -Y, com regua de X)")

# fachada NORTE: camera ao norte olhando -Y. Move a regua pra frente do norte.
for r in rulers:
    try: bpy.data.objects.remove(r,do_unlink=True)
    except Exception: pass
rulers=[]
for x in range(gx0,gx1+1):
    rulers.append(vline(x,y_north,base_z,base_z+0.8,0.04 if x%5 else 0.07))
    rulers.append(label(str(x),x-0.12,y_north,base_z-0.6))
cn=make_cam("ELEV_N")
cn.location=(cx, mx[1]+15, base_z+ (top_z-base_z)*0.45)
cn.rotation_euler=(math.radians(90),0,math.radians(180))  # olha -Y
sc.camera=cn; sc.render.filepath=os.path.join(OUT,"north.png")
bpy.ops.render.render(write_still=True); print("RENDERED north (fachada +Y, com regua de X)")

print("ELEV_DONE")
