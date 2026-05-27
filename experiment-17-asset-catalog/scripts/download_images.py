"""Baixa todas as imagens dos assets validos localmente (img/<slug>.<ext>).
Hospedar local evita hotlink/CORS/referer no browser. Reescreve image_url
para caminho relativo ./img/... e grava assets_final.json.
Se o download da imagem inteira falhar, descarta o asset (regra: sem imagem -> pula)."""
import json, os, re, sys, urllib.request, urllib.error, ssl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMGDIR = os.path.join(ROOT, "img")
os.makedirs(IMGDIR, exist_ok=True)

valid = json.load(open(os.path.join(HERE, "assets_valid.json"), encoding="utf-8"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]

def ext_from(ct, data):
    if data[:3] == b"\xff\xd8\xff": return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"): return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP": return "webp"
    if "webp" in ct: return "webp"
    if "png" in ct: return "png"
    if "gif" in ct: return "gif"
    return "jpg"

final = []
seen = {}
for a in valid:
    s = slug(a["name"])
    # evita colisao de slug
    if s in seen:
        seen[s] += 1; s = f"{s}-{seen[s]}"
    else:
        seen[s] = 0
    try:
        req = urllib.request.Request(a["image_url"], headers=HEADERS)
        with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
            data = r.read()
            ct = r.headers.get("Content-Type", "").lower()
        if len(data) < 1500:
            raise ValueError(f"muito pequeno ({len(data)}b)")
        ext = ext_from(ct, data)
        fn = f"{s}.{ext}"
        open(os.path.join(IMGDIR, fn), "wb").write(data)
        a["image"] = f"./img/{fn}"
        a["src_image_url"] = a.pop("image_url")
        final.append(a)
        print(f"[OK ] {a['name'][:40]:40} -> {fn} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"[DROP] {a['name'][:40]:40} {type(e).__name__}: {e}")
    sys.stdout.flush()

json.dump(final, open(os.path.join(HERE, "assets_final.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"\n=== {len(final)} assets com imagem baixada ===")
