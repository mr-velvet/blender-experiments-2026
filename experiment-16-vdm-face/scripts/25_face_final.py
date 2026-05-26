"""25: rosto final no plano. Tudo no mesmo objeto, sequencial (carimbo funciona
assim). Tamanho controlado por ts.unprojected_radius (NAO so size px) -> cada
feature sai no tamanho que eu pedir, independente da ordem.

Como nao da pra rotacionar o stamp via API (encolhe), uso o size pra controlar
escala e POSICIONO cada feature respeitando sua orientacao natural:
  - nariz (b28): grande, centro, leve diagonal natural
  - olhos (b25): menores, BEM afastados e ACIMA, fora do alcance do nariz
  - boca (b17): media, embaixo
"""
import bpy, os, sys, math
from mathutils import Vector
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
TAG=sys.argv[-1] if len(sys.argv)>1 and not sys.argv[-1].endswith(".py") else "f1"
LOGF=os.path.join(OUT,f"25_{TAG}.txt")
buf=[]
def log(*a): buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

import json
# permite passar o plano via env BUILD_PLAN (json); senao usa default
_default=[
    ["olho_esq",25,-0.52, 0.42, 0.30],
    ["olho_dir",25, 0.52, 0.42, 0.30],
    ["nariz",   28, 0.00, 0.00, 0.26],
    ["boca",    17, 0.00,-0.58, 0.32],
]
FACE_PLAN=json.loads(os.environ.get("BUILD_PLAN", json.dumps(_default)))
def gv():
    for win in bpy.context.window_manager.windows:
        for a in win.screen.areas:
            if a.type=='VIEW_3D':
                r=next((x for x in a.regions if x.type=='WINDOW'),None)
                return win,a,r,a.spaces.active.region_3d
    return None,None,None,None
def load_brush(idx):
    f=f"Human Face VDM {idx:02d}.asset.blend"; b0=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,f),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    b=bpy.data.brushes[list(set(bpy.data.brushes.keys())-b0)[0]]
    if b.texture and b.texture.image: b.texture.image.colorspace_settings.name='Non-Color'
    return b
def build():
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov): bpy.ops.wm.read_factory_settings(use_empty=True)
    win,area,region,rv3d=gv(); ov={'window':win,'area':area,'region':region}
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2)
        obj=bpy.context.view_layer.objects.active; obj.name="Face"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=8; bpy.ops.object.modifier_apply(modifier=m.name)
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'; rv3d.view_distance=2.6; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt
        ups=bpy.context.scene.tool_settings.unified_paint_settings
        # usa raio em unidades de mundo (nao trava em pixels/zoom)
        ups.use_locked_size='SCENE'; ups.use_unified_size=True
        for name,bidx,x,y,rad in FACE_PLAN:
            brush=load_brush(bidx); ts.brush=brush
            try: brush.texture_slot.map_mode='AREA_PLANE'
            except: pass
            ups.unprojected_radius=rad
            brush.unprojected_radius=rad
            c=location_3d_to_region_2d(region,rv3d,Vector((x,y,0)))
            st=[{"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":True,"location":(x,y,0),"size":120.0,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
                {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,"is_start":False,"location":(x,y,0),"size":120.0,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0}]
            z0=max(v.co.z for v in obj.data.vertices)
            bpy.ops.sculpt.brush_stroke(stroke=st,mode='NORMAL')
            z1=max(v.co.z for v in obj.data.vertices)
            log(f"[{name}] b{bidx} @({x},{y}) rad={rad} zmax {z0:.3f}->{z1:.3f}")
        bpy.ops.object.mode_set(mode='OBJECT'); bpy.ops.object.shade_smooth()
    mat=bpy.data.materials.new("clay"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.86,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.6
    obj.data.materials.clear(); obj.data.materials.append(mat)
    sc=bpy.context.scene
    cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
    cd.type='ORTHO'; cd.ortho_scale=2.1; cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
    sc.collection.objects.link(cam); sc.camera=cam
    kd=bpy.data.lights.new("K",type='SUN'); kd.energy=4.0; kd.angle=0.04
    k=bpy.data.objects.new("K",kd); k.rotation_euler=(math.radians(58),0,math.radians(20)); sc.collection.objects.link(k)
    fd=bpy.data.lights.new("F",type='SUN'); fd.energy=1.1; fd.angle=0.6
    f=bpy.data.objects.new("F",fd); f.rotation_euler=(math.radians(35),0,math.radians(-150)); sc.collection.objects.link(f)
    w=bpy.data.worlds.new("W"); w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.07,0.07,0.08,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.3; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=64; sc.render.resolution_x=800; sc.render.resolution_y=800
    sc.render.filepath=os.path.join(OUT,f"face_{TAG}_front.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[front] ok")
    cam.location=(1.1,-2.4,3.4); cam.rotation_euler=(cam.location-Vector((0,0,0))).to_track_quat('Z','Y').to_euler()
    sc.render.filepath=os.path.join(OUT,f"face_{TAG}_3q.png")
    with bpy.context.temp_override(**ov): bpy.ops.render.render(write_still=True)
    log("[3q] ok")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,f"face_{TAG}.blend")); log("[saved]")
_d=[False]
def tick():
    if _d[0]: return None
    _d[0]=True
    try: build()
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender(); return None
bpy.app.timers.register(tick,first_interval=2.0); log(f"[init] {TAG}")
