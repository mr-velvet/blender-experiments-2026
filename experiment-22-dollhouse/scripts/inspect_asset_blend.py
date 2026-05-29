"""inspeciona o conteudo de um .blend de asset BlenderKit (collections/objetos)."""
import bpy, sys, os, json

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
manifest = json.load(open(os.path.join(OUT_DIR, "downloads.json"), encoding="utf-8"))
# pega o primeiro
abid, rec = next(iter(manifest.items()))
path = rec["path"]
print("[insp] asset:", rec["name"], "| path:", os.path.basename(path), flush=True)

with bpy.data.libraries.load(path, link=False) as (df, dt):
    print("[insp] collections:", df.collections, flush=True)
    print("[insp] objects:", df.objects[:30], flush=True)
    dt.collections = list(df.collections)
print("[insp] loaded collections:", [c.name for c in dt.collections if c], flush=True)
for c in dt.collections:
    if c:
        print(f"[insp]   {c.name}: {len(c.objects)} objs, {len(c.children)} child-colls", flush=True)
