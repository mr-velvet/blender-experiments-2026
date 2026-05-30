# -*- coding: utf-8 -*-
"""baixa mapas PBR de texturas PolyHaven (diffuse/nor/rough) em 2k.
python 05_download_soil.py <out_dir> <slug1> <slug2> ..."""
import sys, os, json, urllib.request
OUT=sys.argv[1]; SLUGS=sys.argv[2:]
os.makedirs(OUT,exist_ok=True)
def get(u):
    with urllib.request.urlopen(u,timeout=40) as r: return json.loads(r.read().decode())
saved={}
for slug in SLUGS:
    try:
        files=get(f"https://api.polyhaven.com/files/{slug}")
    except Exception as e:
        print("ERR files",slug,e); continue
    d=os.path.join(OUT,slug); os.makedirs(d,exist_ok=True)
    got={}
    # mapas: Diffuse/diff, nor_gl, rough/Rough, displacement opcional
    for mapkey in ("Diffuse","diff","nor_gl","Rough","rough","arm","AO"):
        node=files.get(mapkey)
        if not node: continue
        # estrutura: {res: {format: {url,...}}}
        res=node.get("2k") or node.get("1k") or next(iter(node.values()),None)
        if not res: continue
        # prefere jpg, depois png/exr
        fmt=res.get("jpg") or res.get("png") or next(iter(res.values()),None)
        if not fmt or "url" not in fmt: continue
        ext=fmt["url"].split(".")[-1].split("?")[0]
        fn=os.path.join(d,f"{mapkey}.{ext}")
        try: urllib.request.urlretrieve(fmt["url"],fn); got[mapkey]=fn
        except Exception as e: print("  dl err",slug,mapkey,e)
    saved[slug]=got
    print(slug,"->",list(got.keys()))
json.dump(saved,open(os.path.join(OUT,"soil_files.json"),"w"),indent=2)
print("SOIL_DL_DONE")
