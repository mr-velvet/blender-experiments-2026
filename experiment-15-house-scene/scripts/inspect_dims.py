"""Importa cada asset isoladamente e reporta dimensoes (m). Roda no Blender."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import scene_lib as L

manifest = json.loads((L.ASSETS / "_manifest.json").read_text(encoding="utf-8"))
out = {}
for slug in manifest:
    if not manifest[slug]:
        continue
    # cena limpa
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        h = L.import_gltf(slug)
        d = L.dims(h)
        out[slug] = [round(d.x, 3), round(d.y, 3), round(d.z, 3)]
        print(f"{slug:28s} W={d.x:6.2f} D={d.y:6.2f} H={d.z:6.2f}")
    except Exception as e:
        print(f"{slug:28s} ERRO: {e}")
        out[slug] = None

(L.ASSETS / "_dims.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("\ndims salvos em assets/_dims.json")
