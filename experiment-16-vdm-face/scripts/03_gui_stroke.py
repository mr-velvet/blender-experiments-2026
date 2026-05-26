"""03: aplica VDM stroke real com janela GUI inicializada (dirigida por timer).

Rodar SEM --background:
  blender.exe scripts/03_gui_stroke.py  (via --python)

A janela abre, um timer dispara depois que o VIEW_3D ja foi desenhado (rv3d valido),
faz o stroke, salva um .blend de resultado e fecha o Blender. O user nao toca em nada.
"""
import bpy
import os
import sys
from mathutils import Vector

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF = os.path.join(OUT, "03_log.txt")

logbuf = []
def log(*a):
    s = " ".join(str(x) for x in a)
    logbuf.append(s)
    try:
        with open(LOGF, "w", encoding="utf-8") as f:
            f.write("\n".join(logbuf))
    except Exception:
        pass


def make_target():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Target"
    m = obj.modifiers.new("sub", "SUBSURF")
    m.levels = 6
    bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"[target] verts={len(obj.data.vertices)}")
    return obj


def load_brush(idx):
    fname = f"Human Face VDM {idx:02d}.asset.blend"
    path = os.path.join(BRUSH_DIR, fname)
    before = set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.brushes = list(df.brushes); dt.textures = list(df.textures); dt.images = list(df.images)
    new = set(bpy.data.brushes.keys()) - before
    brush = bpy.data.brushes[list(new)[0]]
    if brush.texture and brush.texture.image:
        brush.texture.image.colorspace_settings.name = 'Non-Color'
    log(f"[brush] {brush.name} tool={brush.sculpt_tool} stroke={brush.stroke_method}")
    return brush


def get_view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                rv3d = area.spaces.active.region_3d
                return win, area, region, rv3d
    return None, None, None, None


def world_to_region(region, rv3d, co):
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    return location_3d_to_region_2d(region, rv3d, Vector(co))


_done = False

def do_work():
    global _done
    if _done:
        return None
    _done = True
    log("=== timer fired ===")

    obj = make_target()
    brush = load_brush(1)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='SCULPT')
    ts = bpy.context.scene.tool_settings.sculpt
    ts.brush = brush
    try:
        brush.texture_slot.map_mode = 'AREA_PLANE'
    except Exception as e:
        log("[warn] map_mode", e)

    win, area, region, rv3d = get_view3d()
    log(f"[view3d] area={area} region={region} rv3d={rv3d}")
    if rv3d is None:
        log("RESULT: NO_RV3D")
        bpy.ops.wm.quit_blender()
        return None

    # apontar a camera de viewport pra +X (olhar a face +X do cubo de frente)
    # face +X esta em x=1. Vamos carimbar no centro dessa face: world (1, 0, 0)
    # com a vista olhando ao longo de -X.
    rv3d.view_rotation = (0.5, 0.5, 0.5, 0.5)  # placeholder; ajustamos depois
    rv3d.view_perspective = 'ORTHO'

    # ponto alvo na superficie (face +X)
    target_world = Vector((1.0, 0.0, 0.0))
    p2d = world_to_region(region, rv3d, target_world)
    log(f"[proj] target {target_world} -> 2d {p2d}")
    if p2d is None:
        log("RESULT: PROJ_FAIL")
        bpy.ops.wm.quit_blender()
        return None

    cx, cy = p2d.x, p2d.y
    stroke = [
        {"name": "", "mouse": (cx, cy), "mouse_event": (cx, cy), "pen_flip": False,
         "is_start": True, "location": tuple(target_world), "size": 80.0,
         "pressure": 1.0, "time": 0.0, "x_tilt": 0, "y_tilt": 0},
        {"name": "", "mouse": (cx + 80, cy), "mouse_event": (cx + 80, cy), "pen_flip": False,
         "is_start": False, "location": tuple(target_world), "size": 80.0,
         "pressure": 1.0, "time": 0.1, "x_tilt": 0, "y_tilt": 0},
    ]
    ov = {'window': win, 'area': area, 'region': region}
    with bpy.context.temp_override(**ov):
        try:
            bpy.ops.sculpt.brush_stroke(stroke=stroke, mode='NORMAL')
            log("RESULT: STROKE_OK")
        except Exception as e:
            log(f"RESULT: STROKE_FAIL {type(e).__name__}: {e}")

    bpy.ops.object.mode_set(mode='OBJECT')
    outblend = os.path.join(OUT, "03_result.blend")
    bpy.ops.wm.save_as_mainfile(filepath=outblend)
    log(f"[saved] {outblend}")
    bpy.ops.wm.quit_blender()
    return None


# registrar timer com delay pra garantir que a janela ja desenhou
bpy.app.timers.register(do_work, first_interval=2.0)
log("[init] timer registrado")
