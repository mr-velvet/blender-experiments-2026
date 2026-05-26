"""Abre o house.blend e reporta bbox final de cada handle H_*. Roda no Blender."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import scene_lib as L

bpy.ops.wm.open_mainfile(filepath=str(L.EXP / "output" / "house.blend"))

print(f"{'handle':24s} {'cx':>6} {'cy':>6} {'cz':>6} {'W':>6} {'D':>6} {'H':>6} {'zmin':>6} {'zmax':>6}")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if not o.name.startswith("H_"):
        continue
    mn, mx = L.world_bbox(o)
    c = (mn + mx) / 2
    d = mx - mn
    print(f"{o.name:24s} {c.x:6.2f} {c.y:6.2f} {c.z:6.2f} {d.x:6.2f} {d.y:6.2f} {d.z:6.2f} {mn.z:6.2f} {mx.z:6.2f}")
