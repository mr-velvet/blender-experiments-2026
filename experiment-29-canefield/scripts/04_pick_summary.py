# -*- coding: utf-8 -*-
"""resumo enxuto dos candidatos da busca 2, ordenado por relevancia de canavial."""
import json, sys, os
out = sys.argv[1]
rows = json.load(open(os.path.join(out,"candidates.json"), encoding="utf-8"))
# pontua: campo/wheat/corn/reed/cane alto > grass generico
PRIO = {"wheat":5,"cane":6,"sugarcane":7,"corn":5,"maize":5,"reed":4,
        "field":3,"miscanthus":4,"phragmites":4,"sorghum":5,"grain":4,
        "grass":1,"sedge":2,"foxtail":3}
def score(r):
    nm=(r.get("name") or "").lower(); s=0
    for k,v in PRIO.items():
        if k in nm: s=max(s,v)
    if "field" in nm: s+=1
    if "wind" in nm: s+=1   # "on the wind" = animado, bonus
    return s
rows.sort(key=score, reverse=True)
for r in rows:
    print("%2d  %-38s thumb=%s" % (score(r), (r.get("name") or "")[:38], os.path.basename(r.get("thumb_file","") or "-")))
# escreve top com paths
top = [r for r in rows if score(r)>=3][:12]
json.dump(top, open(os.path.join(out,"top.json"),"w",encoding="utf-8"), indent=2, ensure_ascii=False)
print("\nTOP THUMBS:")
for r in top:
    print(r.get("thumb_file",""))
