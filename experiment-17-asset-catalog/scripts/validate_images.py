"""Valida que cada image_url de assets_raw.json carrega como imagem real.
Regra do user: asset sem imagem que carregue = descartado.
Gera assets_valid.json (validos) e prints dos descartados."""
import json, os, sys, urllib.request, urllib.error, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(os.path.join(HERE, "assets_raw.json"), encoding="utf-8"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

def check(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            ct = r.headers.get("Content-Type", "").lower()
            # le um pedacinho pra confirmar que ha bytes
            chunk = r.read(512)
            ok_ct = ct.startswith("image/") or "octet-stream" in ct
            magic = (chunk[:3] == b"\xff\xd8\xff" or chunk[:8] == b"\x89PNG\r\n\x1a\n"
                     or chunk[:4] == b"RIFF" or chunk[:6] in (b"GIF87a", b"GIF89a"))
            return (r.status == 200 and (ok_ct or magic), f"{r.status} {ct} {len(chunk)}b")
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}")
    except Exception as e:
        return (False, f"ERR {type(e).__name__}: {e}")

valid, dropped = [], []
for i, a in enumerate(raw):
    ok, info = check(a["image_url"])
    tag = "OK " if ok else "DROP"
    print(f"[{tag}] {a['name'][:42]:42} {info}")
    sys.stdout.flush()
    (valid if ok else dropped).append(a)

json.dump(valid, open(os.path.join(HERE, "assets_valid.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
json.dump(dropped, open(os.path.join(HERE, "assets_dropped.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"\n=== {len(valid)} validos / {len(dropped)} descartados ===")
