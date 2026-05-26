"""
Reabre house.blend, melhora iluminacao e renderiza vistas boas.
Roda no Blender:  blender --background --python render_views.py

As cameras de close foram recalibradas: cada comodo eh visto de uma
posicao alta, na borda externa do comodo, olhando pra dentro e pra baixo,
de modo que as paredes nao bloqueiem a vista (teto eh aberto).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import scene_lib as L

OUT = L.EXP / "output"
bpy.ops.wm.open_mainfile(filepath=str(OUT / "house.blend"))

# ---- reforca iluminacao: remove sun/fills antigos e recria mais fortes
for o in list(bpy.data.objects):
    if o.type == "LIGHT":
        bpy.data.objects.remove(o, do_unlink=True)

L.world_background(color=(0.95, 0.96, 0.98, 1.0), strength=1.2)
sun = L.add_sun(energy=3.5, angle=(0.5, 0.15, 0.6))
# fills altos por comodo (acima do teto aberto, iluminam de cima)
for (lx, ly) in [(-3.2, -2.6), (3.2, -2.6), (-3.5, 2.8), (3.5, 1.8)]:
    L.add_area_light(f"Fill_{lx}_{ly}", (lx, ly, 3.6), size=3.0, energy=400)

L.setup_render(samples=160, res=(1700, 1080))

# ---- cameras
# Paredes tem 2.8m. Para os closes nao serem bloqueados, a camera fica ACIMA
# das paredes (Z ~4.6) e deslocada para o lado externo do comodo, olhando para
# baixo num angulo picado (vista "dollhouse") com lente aberta (24mm) -> ve o
# comodo inteiro por cima da parede sem corte.
# Centros dos comodos (HX=6.5, HY=4.5, divisoria em X=0 e Y=0):
#   sala       X<0,Y<0  centro (-3.25,-2.25)
#   cozinha    X>0,Y<0  centro ( 3.25,-2.25)
#   quarto     X<0,Y>0  centro (-3.25, 2.25)
#   escritorio X>0,Y>0  centro ( 3.25, 2.25)
CAMS = {
    # overviews altos de canto (corte da casa toda)
    "overview_sw": ((-9.5, -8.5, 8.5), (-0.5, -0.5, 0.6), 35),
    "overview_se": ((9.5, -8.5, 8.5), (0.5, -0.5, 0.6), 35),
    "overview_top": ((0.01, -0.01, 16.0), (0, 0, 0.6), 55),  # planta baixa
    # closes dollhouse: cam alta no canto externo do comodo, olha p/ o centro
    "living":  ((-5.6, -4.0, 4.7), (-3.0, -2.4, 0.5), 24),
    "kitchen": (( 5.6, -4.0, 4.7), ( 3.0, -2.4, 0.5), 24),
    "bedroom": ((-5.6,  4.0, 4.7), (-3.2,  2.4, 0.6), 24),
    "office":  (( 5.6,  4.0, 4.7), ( 3.2,  2.0, 0.6), 24),
}

rdir = OUT / "renders"
rdir.mkdir(exist_ok=True)
for name, (loc, look, lens) in CAMS.items():
    L.add_camera(loc, look, lens=lens)
    L.render_to(rdir / f"{name}.png")
    print(f"render {name} OK")
print("DONE")
