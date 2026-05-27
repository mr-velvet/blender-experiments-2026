"""37: inspeciona o brush de OLHO (b25) e lista TODAS as propriedades do brush VDM
que sao candidatas a variar entre faces. Roda em --background, so dumpa texto.
Objetivo: descobrir quais propriedades existem e quais teoricamente mudam o stamp,
pra eu variar SO propriedade do pincel (nada de mexer na malha)."""
import bpy, os
BRUSH_DIR=r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes"
OUT=r"C:\Users\manu\ved\blender-experiments-2026\experiment-16-vdm-face\output"
LOGF=os.path.join(OUT,"37_inspect.txt")
buf=[]
def log(*a):
    s=" ".join(str(x) for x in a); buf.append(s)
    open(LOGF,"w",encoding="utf-8").write("\n".join(buf))

def load_brush(idx):
    f=f"Human Face VDM {idx:02d}.asset.blend"; b0=set(bpy.data.brushes.keys())
    with bpy.data.libraries.load(os.path.join(BRUSH_DIR,f),link=False) as (df,dt):
        dt.brushes=list(df.brushes); dt.textures=list(df.textures); dt.images=list(df.images)
    return bpy.data.brushes[list(set(bpy.data.brushes.keys())-b0)[0]]

b=load_brush(25)
log("=== BRUSH b25 (olho) ===")
log("name:",b.name)
for p in ("sculpt_tool","strength","normal_radius_factor","hardness","auto_smooth_factor",
          "stroke_method","use_frontface","tip_roundness","crease_pinch_factor",
          "normal_weight","use_original_normal","plane_offset","height","tilt_strength_factor"):
    log(f"  {p} = {getattr(b,p,'<n/a>')}")
log("--- texture_slot ---")
ts=b.texture_slot
for p in ("map_mode","angle","scale","offset","tex_blend_mode","use_random_rotation","random_angle"):
    log(f"  ts.{p} = {getattr(ts,p,'<n/a>')}")
log("--- texture ---")
if b.texture:
    tx=b.texture
    log("  type:",tx.type)
    if tx.image:
        img=tx.image
        log("  image:",img.name,"size:",tuple(img.size),"depth:",img.depth,"colorspace:",img.colorspace_settings.name)
log("--- todas props numericas != default candidatas (curve/falloff) ---")
log("  curve_preset:",getattr(b,"curve_preset","<n/a>"))
log("  use_custom_icon:",getattr(b,"use_custom_icon","<n/a>"))
# props que mudam INTENSIDADE/escala do stamp sem tocar a malha:
log("\n=== CANDIDATAS A VARIAR (so propriedade do pincel) ===")
log("1. unprojected_radius (via unified) -> TAMANHO do olho")
log("2. strength -> INTENSIDADE do deslocamento (relevo mais/menos saliente)")
log("3. texture_slot.scale -> escala da textura VDM dentro do stamp")
log("4. texture_slot.angle -> rotacao do stamp (sabido: encolhe; evitar)")
log("5. rotacao da MALHA antes do stroke -> orientacao sem encolher (legitimo)")
log("[done]")
print("\n".join(buf))
