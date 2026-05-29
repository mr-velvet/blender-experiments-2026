"""renderiza um asset isolado pra inspecionar geometria.
  blender --background --python render_asset_solo.py -- <assetBaseId> <outname>
"""
import bpy, sys, os, json, math
sys.path.append(os.path.dirname(__file__))
import render_lib as rl
from mathutils import Vector

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
argv = sys.argv; argv = argv[argv.index("--") + 1:]
abid = argv[0]; outname = argv[1]
manifest = json.load(open(os.path.join(OUT_DIR, "downloads.json"), encoding="utf-8"))
rec = manifest[abid]

bpy.ops.wm.read_homefile(use_empty=True)
with bpy.data.libraries.load(rec["path"], link=False) as (df, dt):
    dt.collections = [df.collections[0]] if df.collections else []
objs=[]
for c in dt.collections:
    if c:
        for o in c.objects:
            bpy.context.scene.collection.objects.link(o); objs.append(o)

mn, mx = rl.world_bbox(objs)
center = (mn+mx)/2; size=(mx-mn)
r = max(size)*1.6 + 0.5
rl.setup_world(strength=1.0)
rl.add_sun(energy=3)
rl.add_camera(location=(center.x+r, center.y-r, center.z+r*0.6), target=center, lens=45)
out = os.path.join(OUT_DIR, "preview", f"asset_{outname}.png")
rl.render(out, engine='BLENDER_EEVEE', samples=16, res=(500,500))
print(f"[solo] {rec['name']} dim={[round(x,2) for x in size]} -> {out}", flush=True)
