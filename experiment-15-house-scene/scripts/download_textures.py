"""
Baixa texturas PBR CC0 do PolyHaven para o shell da casa (piso/parede).

Para cada slug pega: Diffuse (cor), nor_gl (normal OpenGL), Rough.
Resolucao 2k (piso/parede ocupam area grande -> vale mais resolucao).

Saida: assets/_textures/<slug>/<maps>.jpg
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "_textures"
RES = "2k"
HEADERS = {"User-Agent": "house-scene-experiment"}

TEXTURES = {
    "wood_floor": ["Diffuse", "nor_gl", "Rough"],
    "beige_wall_001": ["Diffuse", "nor_gl", "Rough"],
}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def main():
    result = {}
    for slug, maps in TEXTURES.items():
        files = fetch_json(f"https://api.polyhaven.com/files/{slug}")
        slug_maps = {}
        for m in maps:
            if m not in files:
                continue
            node = files[m]
            res = RES if RES in node else sorted(node.keys())[0]
            # cada map tem formatos (jpg/png/exr); pegar jpg se houver
            fmt_node = node[res]
            fmt = "jpg" if "jpg" in fmt_node else sorted(fmt_node.keys())[0]
            info = fmt_node[fmt]
            ext = info["url"].split(".")[-1]
            dest = OUT / slug / f"{m}.{ext}"
            download(info["url"], dest)
            slug_maps[m] = str(dest.relative_to(ROOT)).replace("\\", "/")
            print(f"  [OK] {slug}/{m} ({res}.{fmt})")
        result[slug] = slug_maps
    (OUT / "_manifest.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print("Texturas concluidas.")


if __name__ == "__main__":
    main()
