"""10: sweep de texture_slot.angle pra achar a orientacao correta de cada VDM.

Confirmado no passo 09: orientacao do stamp NAO vem do drag, vem de
brush.texture_slot.angle. Aqui carimbo brush 23 (nariz) e 15 (boca) com
angle 0/90/180/270 e capturo OpenGL com vista 3/4 (45 graus) e brush menor,
pra a feature caber no plano com borda visivel e eu ler a orientacao.
"""
import bpy, os, math
from mathutils import Vector, Euler

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\texangle"
LOGF = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\10_log.txt"
os.makedirs(OUT, exist_ok=True)
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a)); open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type=='VIEW_3D':
                region=next((r for r in area.regions if r.type=='WINDOW'),None)
                return win,area,region,area.spaces.active.region_3d
    return None,None,None,None

def load_brush(idx):
    fname=f"Human Face VDM {idx:02d}.asset.blend"
    before=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,fname),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    b=bpy.data.brushes[list(set(bpy.data.brushes.keys())-before)[0]]
    if b.texture and b.texture.image: b.texture.image.colorspace_settings.name='Non-Color'
    return b

def setup_view(area, sp_shade=True):
    sp=area.spaces.active
    if sp_shade:
        sp.shading.type='SOLID'; sp.shading.light='STUDIO'
        sp.shading.color_type='SINGLE'; sp.shading.single_color=(0.82,0.76,0.68)
        # sombras dinamicas do viewport (revela relevo sem path-tracing)
        sp.shading.show_shadows=True
        try: sp.shading.shadow_intensity=0.85
        except: pass
        # cavity reforca os vales/cristas finos
        sp.shading.show_cavity=True; sp.shading.cavity_type='BOTH'
        sp.shading.cavity_ridge_factor=1.6; sp.shading.cavity_valley_factor=1.6
        sp.shading.curvature_ridge_factor=0.8; sp.shading.curvature_valley_factor=0.8
        sp.overlay.show_overlays=False
        # luz do studio orientada rasante: girar o studiolight
        try: sp.shading.studiolight_rotate_z=math.radians(45)
        except: pass

def run(idx, angle_deg, ov, region, rv3d):
    # top-down exato pra carimbar
    rv3d.view_rotation=(1,0,0,0); rv3d.view_perspective='ORTHO'
    rv3d.view_distance=2.0; rv3d.view_location=(0,0,0)
    bpy.context.view_layer.update()
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,0))
        obj=bpy.context.view_layer.objects.active; obj.name="P"
        m=obj.modifiers.new("s","SUBSURF"); m.levels=7
        bpy.ops.object.modifier_apply(modifier=m.name)
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    c=location_3d_to_region_2d(region,rv3d,Vector((0,0,0)))
    brush=load_brush(idx)
    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts=bpy.context.scene.tool_settings.sculpt; ts.brush=brush
        try: brush.texture_slot.map_mode='AREA_PLANE'
        except: pass
        brush.texture_slot.angle=math.radians(angle_deg)
        sz=110.0
        stroke=[
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,
             "is_start":True,"location":(0,0,0),"size":sz,"pressure":1.0,"time":0.0,"x_tilt":0,"y_tilt":0},
            {"name":"","mouse":(c.x,c.y),"mouse_event":(c.x,c.y),"pen_flip":False,
             "is_start":False,"location":(0,0,0),"size":sz,"pressure":1.0,"time":0.02,"x_tilt":0,"y_tilt":0},
        ]
        try: bpy.ops.sculpt.brush_stroke(stroke=stroke,mode='NORMAL'); res="OK"
        except Exception as e: res=f"FAIL {e}"
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()
    # material claro
    mat=bpy.data.materials.new("c"); mat.use_nodes=True
    bb=mat.node_tree.nodes.get("Principled BSDF")
    if bb: bb.inputs["Base Color"].default_value=(0.85,0.78,0.7,1); bb.inputs["Roughness"].default_value=0.7
    obj.data.materials.clear(); obj.data.materials.append(mat)
    # render EEVEE topo puro com luz rasante (real-time, nao path-tracing)
    sc=bpy.context.scene
    if "C" not in bpy.data.objects:
        cd=bpy.data.cameras.new("C"); cam=bpy.data.objects.new("C",cd)
        cd.type='ORTHO'; cd.ortho_scale=2.2; cam.location=(0,0,5); cam.rotation_euler=(0,0,0)
        sc.collection.objects.link(cam); sc.camera=cam
    if "S" not in bpy.data.objects:
        sd=bpy.data.lights.new("S",type='SUN'); sd.energy=5.0; sd.angle=0.03
        s=bpy.data.objects.new("S",sd); s.rotation_euler=(1.32,0.0,0.6)
        sc.collection.objects.link(s)
    if sc.world is None:
        w=bpy.data.worlds.new("W"); w.use_nodes=True
        w.node_tree.nodes["Background"].inputs[0].default_value=(0.03,0.03,0.04,1)
        w.node_tree.nodes["Background"].inputs[1].default_value=0.2; sc.world=w
    sc.render.engine='CYCLES'; sc.cycles.samples=24
    sc.render.resolution_x=400; sc.render.resolution_y=400
    outp=os.path.join(OUT,f"b{idx:02d}_a{angle_deg:03d}.png")
    sc.render.filepath=outp
    with bpy.context.temp_override(**ov):
        bpy.ops.render.render(write_still=True)
    log(f"[b{idx} a{angle_deg}] {res} -> {outp}")
    bpy.data.objects.remove(obj,do_unlink=True)

_done=[False]
def tick():
    if _done[0]: return None
    _done[0]=True
    try:
        win,area,region,rv3d=get_view3d()
        setup_view(area)
        ov={'window':win,'area':area,'region':region}
        for idx in (23,15,1,5):
            for ang in (0,90,180,270):
                run(idx,ang,ov,region,rv3d)
        log("DONE")
    except Exception as e:
        import traceback; log("ERR",traceback.format_exc())
    bpy.ops.wm.quit_blender()
    return None
bpy.app.timers.register(tick, first_interval=2.0)
log("[init] texangle sweep")
