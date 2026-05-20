"""Gera manifest_v2.json com paths absolutos pro v1 no GCS."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = HERE / "out" / "manifest.json"
dst = HERE / "out" / "manifest_v2.json"
PREFIX = "https://st.did.lu/blender-claydoh/v1/"

items = json.loads(src.read_text())
for it in items:
    if it.get("glb"): it["glb"] = PREFIX + it["glb"]
    if it.get("render"): it["render"] = PREFIX + it["render"]

dst.write_text(json.dumps(items, indent=2))
print(f"wrote {dst}")
