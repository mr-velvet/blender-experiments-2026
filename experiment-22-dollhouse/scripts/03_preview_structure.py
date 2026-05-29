"""03_preview_structure.py — abre a estrutura e renderiza um preview frontal
rapido (Eevee) pra validar o corte dollhouse antes de mobiliar.

  blender --background --python 03_preview_structure.py
"""
import bpy
import sys
import os
import json

sys.path.append(os.path.dirname(__file__))
import render_lib as rl

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
meta = json.load(open(os.path.join(OUT_DIR, "rooms.json"), encoding="utf-8"))
W, D = meta["W"], meta["D"]
total_h = meta["floor_pitch"] * meta["n_floors"]

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, "dollhouse_structure.blend"))

objs = list(bpy.context.scene.objects)
rl.apply_neutral_material(objs)
rl.setup_world(strength=0.7)
rl.add_sun(energy=2.5)
# luz de area na frente iluminando o interior aberto
rl.add_area_fill(location=(W / 2, -4, total_h / 2), size=10, energy=800)

# camera frontal olhando pro corte (de -Y pra +Y), centralizada
cx, cz = W / 2, total_h / 2
cam_y = -max(W, total_h) * 1.4
rl.add_camera(location=(cx, cam_y, cz), target=(cx, D / 2, cz), lens=45)

out = os.path.join(OUT_DIR, "preview", "structure_front.png")
rl.render(out, engine='BLENDER_EEVEE', samples=16, res=(1000, 1000))
print("[preview] saved", out, flush=True)
