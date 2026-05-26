"""08: inspeciona as propriedades de orientacao de um brush VDM, pra entender
como controlar a rotacao do stamp (resolver o '90 graus girado').

Carrega brush 01 e dumpa: texture_slot (angle, map_mode), brush.texture,
stroke_method, e qualquer prop que afete orientacao do carimbo.
"""
import bpy, os

BRUSH_DIR = r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT = r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF = os.path.join(OUT, "08_inspect.txt")
buf=[]
def log(*a):
    buf.append(" ".join(str(x) for x in a))
    open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

def load_brush(idx):
    fname=f"Human Face VDM {idx:02d}.asset.blend"
    before=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,fname),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    nw=set(bpy.data.brushes.keys())-before
    return bpy.data.brushes[list(nw)[0]]

for idx in (1, 5, 15, 23):
    b=load_brush(idx)
    log(f"\n=== brush {idx:02d}: {b.name} ===")
    log(f"  sculpt_tool={getattr(b,'sculpt_tool',None)}")
    log(f"  stroke_method={getattr(b,'stroke_method',None)}")
    log(f"  direction={getattr(b,'direction',None)}")
    ts=b.texture_slot
    if ts:
        log(f"  texture_slot.map_mode={getattr(ts,'map_mode',None)}")
        log(f"  texture_slot.angle={getattr(ts,'angle',None)}")
        log(f"  texture_slot.use_rake={getattr(ts,'use_rake',None)}")
        log(f"  texture_slot.use_random={getattr(ts,'use_random',None)}")
        log(f"  texture_slot.tex_paint_map_mode={getattr(ts,'tex_paint_map_mode',None)}")
    tex=b.texture
    if tex:
        log(f"  texture={tex.name} type={tex.type}")
        if getattr(tex,'image',None):
            img=tex.image
            log(f"    image={img.name} size={tuple(img.size)} colorspace={img.colorspace_settings.name}")
    # props que existem
    for p in ('use_anchor','cursor_overlay_alpha','texture_overlay_alpha'):
        if hasattr(b,p): log(f"  {p}={getattr(b,p)}")

log("\nDONE")
bpy.ops.wm.quit_blender()
