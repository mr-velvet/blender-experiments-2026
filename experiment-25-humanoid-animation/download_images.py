#!/usr/bin/env python3
"""Baixa e valida (HTTP 200 + magic bytes) cada image_url do data.json.
Marca image_ok=true/false. Imagens que falham nao entram na galeria construida."""
import json, os, urllib.request, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

MAGIC = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG": "png",
    b"RIFF": "webp",  # RIFF....WEBP
    b"GIF8": "gif",
}

def sniff(data):
    for sig, ext in MAGIC.items():
        if data.startswith(sig):
            if ext == "webp" and data[8:12] != b"WEBP":
                continue
            return ext
    return None

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        if r.status != 200:
            return None, f"HTTP {r.status}"
        data = r.read()
    if len(data) < 512:
        return None, f"tiny {len(data)}b"
    ext = sniff(data)
    if not ext:
        return None, "not-image"
    return (data, ext), None

with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    data = json.load(f)

results = {"ok": [], "fail": []}
for tab in ("free", "paid"):
    for item in data[tab]:
        url = item.get("image_url")
        local = item["image"]  # ex img/foo.jpg
        if not url:
            item["image_ok"] = False
            results["fail"].append((item["id"], "no-url"))
            continue
        try:
            res, err = fetch(url)
        except Exception as e:
            res, err = None, str(e)[:60]
        if res is None:
            item["image_ok"] = False
            results["fail"].append((item["id"], err))
            print(f"FAIL {item['id']:28} {err}  <- {url[:70]}")
            continue
        blob, ext = res
        # respeita a extensao real do conteudo
        base = os.path.splitext(local)[0]  # img/foo
        local = f"{base}.{ext}"
        item["image"] = local
        item["image_ok"] = True
        with open(os.path.join(HERE, local), "wb") as out:
            out.write(blob)
        results["ok"].append((item["id"], ext, len(blob)))
        print(f"OK   {item['id']:28} {ext} {len(blob)//1024}KB")

with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n=== {len(results['ok'])} OK / {len(results['fail'])} FAIL ===")
print("FAILS:", [r[0] for r in results["fail"]])
