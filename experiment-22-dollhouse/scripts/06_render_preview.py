"""06_render_preview.py — preview Eevee rapido da casa mobiliada (vista frontal).
  blender --background --python 06_render_preview.py -- [out_name]
"""
import bpy, sys, os, json
sys.path.append(os.path.dirname(__file__))
import render_lib as rl

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out_name = argv[0] if argv else "furnished_front"

meta = json.load(open(os.path.join(OUT_DIR, "rooms.json"), encoding="utf-8"))
W, D = meta["W"], meta["D"]
total_h = meta["floor_pitch"] * meta["n_floors"]

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, "dollhouse_furnished.blend"))

# material neutro so nas paredes/lajes (objetos sem material). Moveis ja tem material.
structural = [o for o in bpy.context.scene.objects
              if o.type == 'MESH' and len(o.data.materials) == 0]
rl.apply_neutral_material(structural)

rl.setup_world(strength=0.8)
rl.add_sun(energy=2.0)
# luzes de area na frente, uma por andar, iluminando o interior aberto
for i in range(meta["n_floors"]):
    z = i * meta["floor_pitch"] + meta["ceil_h"] / 2
    rl.add_area_fill(location=(W / 2, -3.0, z + 0.3), size=8, energy=500,
                     name=f"Fill_{i}")

cx, cz = W / 2, total_h / 2
cam_y = -max(W, total_h) * 1.35
rl.add_camera(location=(cx, cam_y, cz), target=(cx, D / 2, cz), lens=42)

out = os.path.join(OUT_DIR, "preview", f"{out_name}.png")
rl.render(out, engine='BLENDER_EEVEE', samples=24, res=(1100, 1100))
print("[prev] saved", out, flush=True)
