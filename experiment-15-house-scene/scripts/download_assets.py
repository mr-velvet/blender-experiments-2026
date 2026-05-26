"""
Downloader de assets do PolyHaven (CC0).

Para cada model slug, baixa a variante gltf na resolucao escolhida:
o .gltf, o .bin e todas as texturas .jpg associadas, preservando a
estrutura de pastas relativa que o .gltf espera (textures/...).

Uso:
    python download_assets.py            # baixa todos os slugs do MANIFEST
    python download_assets.py Sofa_01    # baixa so um

Saida: assets/<slug>/<slug>.gltf + .bin + textures/*.jpg
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
RES = "1k"  # resolucao das texturas: 1k mantem peso baixo p/ cena com muitos assets
HEADERS = {"User-Agent": "house-scene-experiment"}

# Slugs por comodo. So entram aqui assets que existem na API do PolyHaven.
MANIFEST = [
    # --- sala de estar ---
    "Sofa_01", "sofa_02", "ArmChair_01", "CoffeeTable_01",
    "Television_01", "wooden_bookshelf_worn", "modern_ceiling_lamp_01",
    "potted_plant_01", "ClassicConsole_01",
    # --- quarto ---
    "GothicBed_01", "ClassicNightstand_01", "vintage_cabinet_01",
    "desk_lamp_arm_01",
    # --- cozinha / jantar ---
    "round_wooden_table_01", "dining_chair_02", "WoodenChair_01",
    "electric_stove", "pot_enamel_01", "wooden_bowl_01", "tea_set_01",
    "steel_frame_shelves_01",
    # --- escritorio ---
    "metal_office_desk", "SchoolChair_01", "desk_lamp_arm_01",
    "potted_plant_04",
    # --- decoracao geral ---
    "Chandelier_01", "wine_bottles_01", "brass_vase_04",
]


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return False  # ja baixado
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return True


def get_asset(slug):
    files = fetch_json(f"https://api.polyhaven.com/files/{slug}")
    if "gltf" not in files:
        print(f"  [SKIP] {slug}: sem variante gltf")
        return None
    gltf_node = files["gltf"]
    res = RES if RES in gltf_node else sorted(gltf_node.keys())[0]
    bundle = gltf_node[res]["gltf"]
    out_dir = ASSETS / slug

    # 1) o proprio .gltf
    main_url = bundle["url"]
    main_name = main_url.split("/")[-1]
    n = download(main_url, out_dir / main_name)
    # 2) includes: .bin + texturas (paths relativos preservados)
    n_inc = 0
    for rel_path, info in bundle.get("include", {}).items():
        if download(info["url"], out_dir / rel_path):
            n_inc += 1
    print(f"  [OK] {slug} ({res}) gltf={main_name} +{n_inc} includes")
    return out_dir / main_name


def main():
    slugs = sys.argv[1:] or MANIFEST
    # dedup preservando ordem
    seen, uniq = set(), []
    for s in slugs:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    print(f"Baixando {len(uniq)} assets (res {RES}) do PolyHaven...")
    results = {}
    for slug in uniq:
        try:
            p = get_asset(slug)
            results[slug] = str(p.relative_to(ROOT)) if p else None
        except Exception as e:
            print(f"  [ERR] {slug}: {e}")
            results[slug] = None
    (ASSETS / "_manifest.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    ok = sum(1 for v in results.values() if v)
    print(f"\nConcluido: {ok}/{len(uniq)} assets disponiveis.")


if __name__ == "__main__":
    main()
