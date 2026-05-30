# -*- coding: utf-8 -*-
"""
experiment-29 / 03_search2.py
Busca focada em PLANTA ALTA tipo canavial. Coleta TODOS os free (mesmo
canDownload=false na search publica — o download real via daemon+api_key
autoriza free assets, como provado no exp-21). Guarda dimensoes (pra saber se
e planta alta de verdade ou item de mesa) e thumbnails grandes.

python 03_search2.py <api_key> <out_dir>
"""
import sys, os, json, urllib.request, urllib.parse, re

API_KEY = sys.argv[1] if len(sys.argv)>1 else ""
OUT = sys.argv[2] if len(sys.argv)>2 else "out/search2"
os.makedirs(os.path.join(OUT,"thumbs"), exist_ok=True)

# queries focadas em campo/plantacao alta de exterior
QUERIES = [
    "sugarcane plant","cornfield","corn field","wheat plant","wheat stalk",
    "reed plant","river reed","tall grass plant","miscanthus","phragmites",
    "elephant grass","crop plant","grain field","field plant","savanna grass",
    "ornamental grass","feather grass","foxtail","sedge","plume grass",
]

def search(q):
    params={"query":f"{q} asset_type:model","dict_parameters":"1","page_size":"24"}
    url="https://www.blenderkit.com/api/v1/search/?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url, headers={"Authorization":f"Bearer {API_KEY}"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("ERR",q,e); return {"results":[]}

NEG=("vase","bouquet","sofa","chair","bread","candy","whiskey","ornament",
     "dresser","nightstand","console","settee","planter","desk","bottle",
     "armchair","rug","pillow","decor","wreath","pot ","potted")
PLANT=("grass","cane","wheat","corn","maize","reed","bamboo","millet",
       "sorghum","rice","crop","grain","sedge","foxtail","miscanthus",
       "phragmites","field","plume","feather","savanna","stalk","plant")

seen={}; rows=[]
for q in QUERIES:
    for a in search(q).get("results",[]):
        bid=a.get("assetBaseId") or a.get("asset_base_id")
        nm=(a.get("name") or "").lower()
        if not bid or bid in seen: continue
        is_free=a.get("isFree",False)
        if not is_free: continue
        if any(n in nm for n in NEG): continue
        if not any(p in nm for p in PLANT): continue
        dim=a.get("dimensions") or a.get("bbox") or {}
        rec={"query":q,"name":a.get("name"),"assetBaseId":bid,
             "isFree":is_free,"canDownload":a.get("canDownload",False),
             "category":a.get("category"),
             "author":(a.get("author") or {}).get("fullName") if isinstance(a.get("author"),dict) else None,
             "thumbnail":a.get("thumbnailMiddleUrl") or a.get("thumbnailSmallUrl") or "",
             "dimensions":dim,
             "rating_quality":(a.get("ratingsAverage") or {}).get("quality") if isinstance(a.get("ratingsAverage"),dict) else None,
             "downloadsCount":a.get("downloadsCount")}
        seen[bid]=rec; rows.append(rec)

print("unique tall-plant free candidates:",len(rows))
for i,rec in enumerate(rows):
    t=rec["thumbnail"]
    if t:
        safe=re.sub(r'[^a-zA-Z0-9_-]','_',(rec["name"] or "x"))[:38]
        fn=os.path.join(OUT,"thumbs",f"{i:02d}_{safe}.jpg")
        try: urllib.request.urlretrieve(t,fn); rec["thumb_file"]=fn
        except Exception as e: print("thumb err",e)
json.dump(rows, open(os.path.join(OUT,"candidates.json"),"w",encoding="utf-8"), indent=2, ensure_ascii=False)
for rec in rows:
    d=rec.get("dimensions")
    print(f"  {rec['name'][:40]:40s} dl={rec['canDownload']} dims={d} q='{rec['query']}' id={rec['assetBaseId'][:8]}")
print("SEARCH2_DONE", os.path.join(OUT,"candidates.json"))
