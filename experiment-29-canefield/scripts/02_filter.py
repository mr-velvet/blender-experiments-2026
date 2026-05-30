# -*- coding: utf-8 -*-
"""filtra candidates.json -> so canDownload=True, imprime resumo + escreve dl_list.txt"""
import json, sys, os
out = sys.argv[1] if len(sys.argv)>1 else "out/search"
rows = json.load(open(os.path.join(out,"candidates.json"), encoding="utf-8"))
dl = [r for r in rows if r.get("canDownload")]
print("total", len(rows), "| canDownload:", len(dl))
print("=== BAIXAVEIS (free + canDownload) ===")
for r in dl:
    print("NAME: %s" % r.get("name"))
    print("  query=%s  category=%s  author=%s" % (r.get("query"), r.get("category"), r.get("author")))
    print("  id=%s" % r.get("assetBaseId"))
    print("  thumb=%s" % r.get("thumb_file",""))
lines = ["%s\t%s\t%s\t%s" % (r.get("name"), r.get("query"), r.get("assetBaseId"), r.get("thumb_file","")) for r in dl]
open(os.path.join(out,"dl_list.txt"),"w",encoding="utf-8").write("\n".join(lines))
print("WROTE dl_list.txt with", len(dl), "rows")
