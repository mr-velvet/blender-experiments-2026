# -*- coding: utf-8 -*-
"""imprime nome+id dos candidatos-chave pra eu pegar o asset_base_id do trigal."""
import json, sys, os
out = sys.argv[1]
rows = json.load(open(os.path.join(out,"candidates.json"), encoding="utf-8"))
want = ["wheat field on the wind","wheat field","corn","cane plant","reed",
        "grass field on the wind","field grass","wheat"]
for w in want:
    for r in rows:
        if (r.get("name") or "").lower() == w:
            print("%-30s %s  dl=%s" % (r["name"], r["assetBaseId"], r.get("canDownload")))
            break
print("--- ALL ---")
for r in rows:
    print("%-38s %s dl=%s" % ((r.get('name') or '')[:38], r["assetBaseId"], r.get("canDownload")))
