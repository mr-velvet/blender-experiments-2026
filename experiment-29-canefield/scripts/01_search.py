# -*- coding: utf-8 -*-
"""
experiment-29 / 01_search.py
Busca no BlenderKit (API publica de search) por assets de PLANTACAO ALTA tipo
canavial: sugarcane, cane, wheat, corn/maize, reed, tall grass, bamboo, millet.
Filtra por modelos FREE e baixaveis. Salva candidatos + thumbnails pra eu
escolher visualmente.

Roda com python normal (so HTTP, nao precisa do Blender):
  python 01_search.py <api_key> <out_dir>
"""
import sys, os, json, urllib.request, urllib.parse

API_KEY = sys.argv[1] if len(sys.argv)>1 else ""
OUT = sys.argv[2] if len(sys.argv)>2 else "out/search"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT,"thumbs"), exist_ok=True)

QUERIES = [
    "sugarcane", "sugar cane", "cane field", "wheat field", "wheat",
    "corn plant", "maize", "reed", "tall grass", "bamboo plant",
    "millet", "sorghum", "rice plant", "crop field", "grass field",
    "pampas grass", "cattail", "rye", "barley", "cane",
]

def search(q):
    params = {
        "query": f"{q} asset_type:model",
        "dict_parameters": "1",
        "page_size": "20",
    }
    url = "https://www.blenderkit.com/api/v1/search/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("  ERR", q, e)
        return {"results": []}

seen = {}
rows = []
for q in QUERIES:
    data = search(q)
    res = data.get("results", [])
    print(f"[{q}] {len(res)} results")
    for a in res:
        bid = a.get("assetBaseId") or a.get("asset_base_id")
        if not bid or bid in seen:
            continue
        is_free = a.get("isFree", False) or (a.get("isPrivate") is False and a.get("price",0)==0)
        can_dl = a.get("canDownload", False)
        # so free
        if not is_free:
            continue
        thumb = a.get("thumbnailMiddleUrl") or a.get("thumbnailSmallUrl") or ""
        rec = {
            "query": q,
            "name": a.get("name"),
            "assetBaseId": bid,
            "assetType": a.get("assetType"),
            "isFree": is_free,
            "canDownload": can_dl,
            "category": a.get("category"),
            "author": (a.get("author") or {}).get("fullName") if isinstance(a.get("author"),dict) else None,
            "thumbnail": thumb,
            "score": a.get("score"),
            "rating_quality": a.get("ratingsAverage",{}).get("quality") if isinstance(a.get("ratingsAverage"),dict) else None,
        }
        seen[bid] = rec
        rows.append(rec)

print(f"\nTOTAL unique free model candidates: {len(rows)}")
# baixa thumbnails
import re
for i, rec in enumerate(rows):
    t = rec["thumbnail"]
    if not t: continue
    safe = re.sub(r'[^a-zA-Z0-9_-]','_', (rec["name"] or "x"))[:40]
    fn = os.path.join(OUT,"thumbs", f"{i:02d}_{safe}.jpg")
    try:
        urllib.request.urlretrieve(t, fn)
        rec["thumb_file"] = fn
    except Exception as e:
        print("  thumb err", rec["name"], e)

with open(os.path.join(OUT,"candidates.json"),"w",encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)
print("WROTE", os.path.join(OUT,"candidates.json"))
for rec in rows:
    print(f"  - {rec['name'][:45]:45s} free={rec['isFree']} dl={rec['canDownload']} q='{rec['query']}' id={rec['assetBaseId'][:8]}")
print("SEARCH_DONE")
