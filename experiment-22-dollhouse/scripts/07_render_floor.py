"""07_render_floor.py — close-up frontal de UM andar pra diagnostico.
  blender --background --python 07_render_floor.py -- <floor_idx>
"""
import bpy, sys, os, json
sys.path.append(os.path.dirname(__file__))
import render_lib as rl

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
argv = sys.argv; argv = argv[argv.index("--") + 1:]
fi = int(argv[0])
blendfile = argv[1] if len(argv) > 1 else "dollhouse_furnished.blend"

meta = json.load(open(os.path.join(OUT_DIR, "rooms.json"), encoding="utf-8"))
W, D = meta["W"], meta["D"]
pitch = meta["floor_pitch"]; ceil = meta["ceil_h"]
z0 = fi * pitch

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, blendfile))
structural = [o for o in bpy.context.scene.objects if o.type == 'MESH' and len(o.data.materials) == 0]
rl.apply_neutral_material(structural)
rl.setup_world(strength=0.85)
rl.add_sun(energy=2.0)
rl.add_area_fill(location=(W/2, -2.5, z0+ceil/2+0.2), size=7, energy=600)

cx = W/2; cz = z0 + ceil/2
cam_y = -W*0.95
rl.add_camera(location=(cx, cam_y, cz), target=(cx, D/2, cz), lens=42)

out = os.path.join(OUT_DIR, "preview", f"floor_{fi}.png")
rl.render(out, engine='BLENDER_EEVEE', samples=24, res=(1100, 700))
print("[floor]", fi, "saved", out, flush=True)
