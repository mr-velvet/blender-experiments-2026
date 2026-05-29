# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse
import time
import os

API_KEY = "4aa76c6fa07bf65742b44f3506b5e9336176e224"
OUT_DIR = r"C:\Users\manu\ved\blender-experiments-2026\experiment-22-dollhouse\out"

# slot -> list of query terms to try (first that yields valid candidates wins,
# but we aggregate all results across terms for the slot)
SLOTS = [
    ("sofa", ["sofa"]),
    ("coffee_table", ["coffee table"]),
    ("tv", ["tv", "television"]),
    ("bookshelf", ["bookshelf", "shelf"]),
    ("armchair", ["armchair"]),
    ("rug", ["rug", "carpet"]),
    ("floor_lamp", ["floor lamp"]),
]

def search(term):
    q = "{} asset_type:model is_free:true".format(term)
    params = urllib.parse.urlencode({
        "query": q,
        "dict_parameters": 1,
        "page_size": 30,
    })
    url = "https://www.blenderkit.com/api/v1/search/?" + params
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + API_KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("results", []) or []

def _tags(t):
    out = []
    for x in (t or []):
        if isinstance(x, dict):
            out.append(x.get("name", ""))
        else:
            out.append(str(x))
    return [s for s in out if s]

def _quality(d):
    # ratingsAverage / ratingsCount come as dicts keyed by quality/workingHours/...
    if isinstance(d, dict):
        v = d.get("quality")
        return v if isinstance(v, (int, float)) else 0
    if isinstance(d, (int, float)):
        return d
    return 0

def norm(item):
    return {
        "name": item.get("name", ""),
        "assetBaseId": item.get("assetBaseId", ""),
        "isFree": item.get("isFree", False),
        "canDownload": item.get("canDownload", False),
        "category": item.get("category", ""),
        "tags": _tags(item.get("tags")),
        "rating": round(float(_quality(item.get("ratingsAverage"))), 2),
        "ratingsCount": int(_quality(item.get("ratingsCount"))),
        "thumb": item.get("thumbnailMiddleUrl", "") or item.get("thumbnailSmallUrl", "") or "",
    }

BAD_NAME_TOKENS = ["kit", " set", "set ", "collection", "pack", "bundle", "scene", "room", "interior", "living room"]

def name_penalty(name):
    n = name.lower()
    pen = 0
    for t in BAD_NAME_TOKENS:
        if t in n:
            pen += 1
    return pen

def score(c):
    # higher is better
    s = 0.0
    s += float(c["rating"]) * 2.0
    if c["ratingsCount"] >= 1:
        s += 5.0
    s += min(c["ratingsCount"], 10) * 0.2
    s -= name_penalty(c["name"]) * 3.0
    return s

result = []
report = {}

for slot, terms in SLOTS:
    agg = {}
    for term in terms:
        try:
            res = search(term)
        except Exception as e:
            print("ERR slot={} term={}: {}".format(slot, term, e))
            res = []
        for it in res:
            c = norm(it)
            if c["assetBaseId"]:
                agg[c["assetBaseId"]] = c
        time.sleep(0.5)
    # filter valid: free + downloadable
    valid = [c for c in agg.values() if c["isFree"] and c["canDownload"]]
    # TV slot: we want an actual television, not computer monitors / stands
    if slot == "tv":
        def is_real_tv(c):
            n = c["name"].lower()
            cat = (c["category"] or "").lower()
            if "monitor" in n or cat == "monitor":
                return False
            if cat in ("video", "household-appliances", "technology"):
                return True
            return ("tv" in n or "television" in n) and "cabinet" not in n and "table" not in n and "stand" not in n
        filtered = [c for c in valid if is_real_tv(c)]
        if filtered:
            valid = filtered
    # prefer rated ones but keep all
    valid.sort(key=score, reverse=True)
    print("slot={} total={} valid_free_dl={}".format(slot, len(agg), len(valid)))
    if valid:
        best = valid[0]
        backup = valid[1] if len(valid) > 1 else None
        result.append({
            "slot": slot,
            "name": best["name"],
            "assetBaseId": best["assetBaseId"],
            "rating": best["rating"],
            "ratingsCount": best["ratingsCount"],
            "tags": best["tags"],
            "thumb": best["thumb"],
            "backup_id": backup["assetBaseId"] if backup else None,
            "backup_name": backup["name"] if backup else None,
        })
        report[slot] = "OK ({} valid)".format(len(valid))
        print("   BEST: {} | rating={} count={} | backup={}".format(
            best["name"], best["rating"], best["ratingsCount"],
            backup["name"] if backup else "none"))
    else:
        report[slot] = "NO valid free+downloadable candidate"
        print("   NO valid candidate")

os.makedirs(OUT_DIR, exist_ok=True)
out_path = os.path.join(OUT_DIR, "furniture_livingroom.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\nWROTE", out_path)
print("SLOTS FILLED:", len(result), "/", len(SLOTS))
for slot, _ in SLOTS:
    print("  ", slot, "->", report.get(slot))
