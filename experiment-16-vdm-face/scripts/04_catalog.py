"""04 (v2): catalogo visual dos 30 VDM brushes — sem read_factory_settings no loop.

Limpa objetos manualmente entre brushes (mantem a window/area viva, pra nao
invalidar o contexto da view3d que o timer precisa). Carimba cada brush no centro
de um plano denso, renderiza levemente em perspectiva com luz rasante, salva PNG.
"""
import bpy
import os
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\catalog"
LOGF = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output\04_log.txt"

os.makedirs(OUT, exist_ok=True)
logbuf = []
def log(*a):
    logbuf.append(" ".join(str(x) for x in a))
    with open(LOGF, "w", encoding="utf-8") as f:
        f.write("\n".join(logbuf))


def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                return win, area, region, area.spaces.active.region_3d
    return None, None, None, None


def wipe_objects(ov):
    """Remove todos os objetos sem resetar a window."""
    with bpy.context.temp_override(**ov):
        if bpy.context.mode != 'OBJECT':
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except Exception: pass
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    # limpar brushes carregados anteriormente pra nao acumular
    for b in list(bpy.data.brushes):
        if b.name.startswith("Human Face VDM") and b.users == 0:
            bpy.data.brushes.remove(b)


def load_brush(idx):
    fname = f"Human Face VDM {idx:02d}.asset.blend"
    before = set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR, fname), link=False) as (df, dt):
        dt.brushes = list(df.brushes); dt.textures = list(df.textures); dt.images = list(df.images)
    new = set(bpy.data.brushes.keys()) - before
    brush = bpy.data.brushes[list(new)[0]]
    if brush.texture and brush.texture.image:
        brush.texture.image.colorspace_settings.name = 'Non-Color'
    return brush


def ensure_render_scene():
    sc = bpy.context.scene
    if "C" not in bpy.data.objects:
        cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d)
        cam_d.type = 'ORTHO'; cam_d.ortho_scale = 2.4
        cam.location = (0, -1.9, 1.9)  # vista 3/4 frontal, le volume melhor
        d = cam.location - Vector((0, 0, 0.1))
        cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        sc.collection.objects.link(cam); sc.camera = cam
    if "S" not in bpy.data.objects:
        sun_d = bpy.data.lights.new("S", type='SUN'); sun_d.energy = 2.6; sun_d.angle = 0.05
        sun = bpy.data.objects.new("S", sun_d); sun.rotation_euler = (0.9, 0.1, 0.35)
        sc.collection.objects.link(sun)
    if sc.world is None:
        w = bpy.data.worlds.new("W"); w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.52, 0.55, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
        sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24
    sc.render.resolution_x = 320; sc.render.resolution_y = 320


def process_brush(i, ov, region, rv3d):
    wipe_objects(ov)
    with bpy.context.temp_override(**ov):
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
        obj = bpy.context.view_layer.objects.active
        obj.name = "P"
        m = obj.modifiers.new("s", "SUBSURF"); m.levels = 7
        bpy.ops.object.modifier_apply(modifier=m.name)

    rv3d.view_rotation = (1, 0, 0, 0)   # topo
    rv3d.view_perspective = 'ORTHO'
    bpy.context.view_layer.update()

    brush = load_brush(i)
    z0 = max(v.co.z for v in obj.data.vertices)

    with bpy.context.temp_override(**ov):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='SCULPT')
        ts = bpy.context.scene.tool_settings.sculpt
        ts.brush = brush
        try: brush.texture_slot.map_mode = 'AREA_PLANE'
        except Exception: pass

        from bpy_extras.view3d_utils import location_3d_to_region_2d
        c = location_3d_to_region_2d(region, rv3d, Vector((0, 0, 0)))
        # variante C calibrada: drag zero (carimbo limpo sem rastro cometa)
        stroke = [
            {"name": "", "mouse": (c.x, c.y), "mouse_event": (c.x, c.y), "pen_flip": False,
             "is_start": True, "location": (0, 0, 0), "size": 110.0, "pressure": 1.0,
             "time": 0.0, "x_tilt": 0, "y_tilt": 0},
            {"name": "", "mouse": (c.x, c.y), "mouse_event": (c.x, c.y), "pen_flip": False,
             "is_start": False, "location": (0, 0, 0), "size": 110.0, "pressure": 1.0,
             "time": 0.02, "x_tilt": 0, "y_tilt": 0},
        ]
        bpy.ops.sculpt.brush_stroke(stroke=stroke, mode='NORMAL')
        bpy.ops.object.mode_set(mode='OBJECT')

    z1 = max(v.co.z for v in obj.data.vertices)
    ensure_render_scene()
    obj.data.materials.clear()
    mat = bpy.data.materials.new("clay"); mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    if b: b.inputs["Base Color"].default_value = (0.8, 0.73, 0.64, 1); b.inputs["Roughness"].default_value = 0.6
    obj.data.materials.append(mat)
    with bpy.context.temp_override(**ov):
        obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()

    outp = os.path.join(OUT, f"brush_{i:02d}.png")
    bpy.context.scene.render.filepath = outp
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    with bpy.context.temp_override(**ov):
        bpy.ops.render.render(write_still=True)
    log(f"[{i}] {brush.name}  d={z1-z0:.3f}")


_idx = [0]; _done = [False]

def tick():
    if _done[0]:
        return None
    i = _idx[0] + 1
    if i > 30:
        _done[0] = True; log("=== DONE ==="); bpy.ops.wm.quit_blender(); return None
    _idx[0] = i
    win, area, region, rv3d = get_view3d()
    if rv3d is None:
        log(f"[{i}] NO_RV3D"); _idx[0] = i - 1; return 0.5
    ov = {'window': win, 'area': area, 'region': region}
    try:
        process_brush(i, ov, region, rv3d)
    except Exception as e:
        log(f"[{i}] ERR {type(e).__name__}: {e}")
    return 0.1


bpy.app.timers.register(tick, first_interval=2.0)
log("[init] catalogo v2 iniciado")
