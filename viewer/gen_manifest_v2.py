"""Gera manifest_v2.json com paths absolutos pro v1 do cardboard no GCS."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "out" / "manifest.json"
dst = ROOT / "out" / "manifest_v2.json"
PREFIX = "https://st.did.lu/blender-cardboard/v1/"

items = json.loads(src.read_text())
for it in items:
    if it.get("glb"):
        it["glb_url"] = PREFIX + it["glb"]
    if it.get("render"):
        it["render_url"] = PREFIX + it["render"]

dst.write_text(json.dumps(items, indent=2))
print(f"wrote {dst}")
