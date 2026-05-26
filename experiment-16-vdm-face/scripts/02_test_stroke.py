"""02: testa aplicar UM VDM brush stroke de verdade num cubo, headless.

VDM brush = sculpt_tool DRAW + stroke ANCHORED + use_color_as_displacement.
O stroke ANCHORED: 1o ponto ancora a posicao, o arrasto define raio/rotacao.

Headless: sculpt.brush_stroke precisa de override de contexto com uma area
VIEW_3D temporaria (region + region_data). Criamos via window/screen existente
do --background? Em background nao ha window_manager.windows normalmente.
Estrategia: usar bpy.context.temp_override com uma area sintetica.

Se nao der via ops, o plano B documentado e o sculpt via gpu offscreen — mas
primeiro tentamos o caminho real.
"""
import bpy
import os
import sys
from mathutils import Vector

def log(*a):
    __builtins__.print(*a) if hasattr(__builtins__, 'print') else __import__('builtins').print(*a)
    sys.stdout.flush()

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_target():
    # cubo denso pra ter geometria pra deformar
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Target"
    # subdividir via multires? VDM brushes funcionam melhor com multires ou dyntopo.
    # Vamos usar subsurf aplicado denso.
    m = obj.modifiers.new("sub", "SUBSURF")
    m.levels = 6
    bpy.ops.object.modifier_apply(modifier=m.name)
    log(f"[target] cubo subdividido -> {len(obj.data.vertices)} verts")
    return obj


def load_brush(idx):
    fname = f"Human Face VDM {idx:02d}.asset.blend"
    path = os.path.join(BRUSH_DIR, fname)
    before = set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        dt.brushes = list(df.brushes)
        dt.textures = list(df.textures)
        dt.images = list(df.images)
    new = set(bpy.data.brushes.keys()) - before
    brush = bpy.data.brushes[list(new)[0]]
    # garantir EXR carregado em float
    if brush.texture and brush.texture.image:
        brush.texture.image.colorspace_settings.name = 'Non-Color'
    log(f"[brush] carregado {brush.name!r} tool={brush.sculpt_tool} stroke={brush.stroke_method}")
    return brush


def find_view3d_override():
    """Em background nao ha screens com VIEW_3D. Tentamos achar/forjar."""
    wm = bpy.context.window_manager
    log(f"[ctx] windows={len(wm.windows)}")
    for win in wm.windows:
        scr = win.screen
        for area in scr.areas:
            log(f"   area {area.type}")
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        return {'window': win, 'screen': scr, 'area': area, 'region': region}
    return None


def main():
    reset()
    obj = make_target()
    brush = load_brush(1)

    # entrar em sculpt mode
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='SCULPT')

    ts = bpy.context.scene.tool_settings.sculpt
    ts.brush = brush
    # configurar texture mapping pra VDM: AREA_PLANE costuma ser o modo
    try:
        brush.texture_slot.map_mode = 'AREA_PLANE'
    except Exception as e:
        log(f"[warn] map_mode: {e}")
    log(f"[sculpt] brush ativo = {ts.brush.name}")

    ov = find_view3d_override()
    log(f"[override] {ov}")

    if ov is None:
        log("RESULT: SEM_VIEW3D — nao da pra usar brush_stroke direto em background")
        return

    # stroke ANCHORED: 2 pontos (press no centro, drag pra fora define raio)
    stroke = [
        {"name": "", "mouse": (ov['region'].width/2, ov['region'].height/2),
         "mouse_event": (0.0, 0.0), "pen_flip": False, "is_start": True,
         "location": (0, 0, 1), "size": 50.0, "pressure": 1.0, "time": 0.0, "x_tilt": 0, "y_tilt": 0},
        {"name": "", "mouse": (ov['region'].width/2 + 60, ov['region'].height/2),
         "mouse_event": (0.0, 0.0), "pen_flip": False, "is_start": False,
         "location": (0.3, 0, 1), "size": 50.0, "pressure": 1.0, "time": 0.1, "x_tilt": 0, "y_tilt": 0},
    ]
    with bpy.context.temp_override(**ov):
        try:
            bpy.ops.sculpt.brush_stroke(stroke=stroke, mode='NORMAL')
            log("RESULT: STROKE_OK")
        except Exception as e:
            log(f"RESULT: STROKE_FAIL {type(e).__name__}: {e}")


main()
