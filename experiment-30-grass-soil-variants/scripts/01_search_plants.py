# -*- coding: utf-8 -*-
"""
exp-30 / 01_search_plants.py — busca BlenderKit por plantas altas/mato alto free.
Coleta candidatos baixaveis, baixa thumbnails. So HTTP.
python 01_search_plants.py <api_key> <out_dir>
"""
import sys, os, json, urllib.request, urllib.parse, re
API=sys.argv[1]; OUT=sys.argv[2]
os.makedirs(os.path.join(OUT,"thumbs"),exist_ok=True)
Q=["tall grass","wild grass","meadow grass","reed plant","bulrush","miscanthus",
   "ornamental grass","fountain grass","grass clump","prairie grass","sedge plant",
   "bamboo plant","wheat plant field","savanna grass","dry grass","weeds plant",
   "bush plant","shrub","fern plant","cattail plant","grass patch","nature grass"]
def search(q):
    p={"query":f"{q} asset_type:model","dict_parameters":"1","page_size":"24"}
    u="https://www.blenderkit.com/api/v1/search/?"+urllib.parse.urlencode(p)
    r=urllib.request.Request(u,headers={"Authorization":f"Bearer {API}"})
    try:
        with urllib.request.urlopen(r,timeout=30) as x: return json.loads(x.read().decode())
    except Exception as e: print("ERR",q,e); return {"results":[]}
NEG=("vase","bouquet","sofa","chair","bread","candy","whiskey","ornament","dresser",
     "nightstand","console","settee","planter","desk","bottle","armchair","rug",
     "pillow","wreath","pot ","potted","cup","bowl","sack","bag","loaf","painting",
     "boulder","rock","stadium","boots","cooker","sushi")
POS=("grass","reed","bulrush","miscanthus","sedge","bamboo","wheat","savanna",
     "cattail","fern","bush","shrub","weed","meadow","prairie","fountain","plant","grasses")
seen={}; rows=[]
for q in Q:
    for a in search(q).get("results",[]):
        bid=a.get("assetBaseId") or a.get("asset_base_id"); nm=(a.get("name") or "").lower()
        if not bid or bid in seen: continue
        if not a.get("isFree",False): continue
        if any(n in nm for n in NEG): continue
        if not any(p in nm for p in POS): continue
        rec={"q":q,"name":a.get("name"),"id":bid,"canDownload":a.get("canDownload",False),
             "category":a.get("category"),
             "author":(a.get("author") or {}).get("fullName") if isinstance(a.get("author"),dict) else None,
             "thumb":a.get("thumbnailMiddleUrl") or a.get("thumbnailSmallUrl") or "",
             "rating":(a.get("ratingsAverage") or {}).get("quality") if isinstance(a.get("ratingsAverage"),dict) else None}
        seen[bid]=rec; rows.append(rec)
print("unique free plant candidates:",len(rows))
for i,r in enumerate(rows):
    if r["thumb"]:
        safe=re.sub(r'[^a-zA-Z0-9_-]','_',(r["name"] or "x"))[:34]
        fn=os.path.join(OUT,"thumbs",f"{i:02d}_{safe}.jpg")
        try: urllib.request.urlretrieve(r["thumb"],fn); r["thumb_file"]=fn
        except Exception: pass
json.dump(rows,open(os.path.join(OUT,"plants.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
for r in rows: print(f"  {r['name'][:38]:38s} dl={r['canDownload']} rat={r['rating']} q='{r['q']}' id={r['id']}")
print("PLANTS_DONE")
