# -*- coding: utf-8 -*-
"""
exp-30 / 02_search_soil.py (v2) — PolyHaven texturas de solo/terreno (CC0).
A API /assets retorna dict slug->meta; categories/tags as vezes ausentes.
Aqui filtro pelo SLUG e pelo name, que sao confiaveis.
python 02_search_soil.py <out_dir>
"""
import sys, os, json, urllib.request
OUT=sys.argv[1]; os.makedirs(os.path.join(OUT,"thumbs"),exist_ok=True)
def get(u):
    try:
        with urllib.request.urlopen(u,timeout=40) as r: return json.loads(r.read().decode())
    except Exception as e: print("ERR",u,e); return {}
allt=get("https://api.polyhaven.com/assets?type=textures")
print("total textures:",len(allt or {}))
TERMS=("soil","dirt","ground","mud","grass","field","forest","meadow","rocky",
       "gravel","sand","terrain","leaves","farm","clay","aerial_grass","aerial_rocks",
       "brown_mud","cracked","rock_ground")
rows=[]
for slug,meta in (allt or {}).items():
    hay=(slug+" "+(meta.get("name") or "")).lower()
    if any(t in hay for t in TERMS):
        rows.append({"slug":slug,"name":meta.get("name") or slug})
print("soil/ground candidates:",len(rows))
for i,r in enumerate(rows[:50]):
    url=f"https://cdn.polyhaven.com/asset_img/thumbs/{r['slug']}.png?width=256&height=256"
    try: urllib.request.urlretrieve(url,os.path.join(OUT,"thumbs",f"{i:02d}_{r['slug']}.png")); r["thumb"]=1
    except Exception: pass
json.dump(rows,open(os.path.join(OUT,"soil.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
for r in rows[:50]: print("  ",r["slug"],"|",r["name"])
print("SOIL_DONE")
