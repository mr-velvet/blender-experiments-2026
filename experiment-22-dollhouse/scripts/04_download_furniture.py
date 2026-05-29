"""
04_download_furniture.py — baixa todos os moveis (asset_type:model) do BlenderKit
de forma headless, deduplicando por assetBaseId. Salva manifesto out/downloads.json
mapeando assetBaseId -> caminho do .blend baixado.

Reaproveita o pipeline validado no exp21 (daemon + download.download + polling de
get_reports), adaptado pra MODELS em vez de SCENE.

  blender --background --python 04_download_furniture.py
"""
import bpy
import sys
import os
import time
import json
import glob
import importlib

sys.path.append(os.path.dirname(__file__))
import layout as LAY

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
PKG = "blenderkit"


def log(*a):
    print("[dl]", *a, flush=True)


import addon_utils
addon_utils.enable(PKG, default_set=False, persistent=True)
from blenderkit import client_lib, download, append_link  # type: ignore
import requests

prefs = bpy.context.preferences.addons[PKG].preferences
log("api_key ***" + (prefs.api_key[-4:] if prefs.api_key else "NONE"))

# ---------------------------------------------------------------------------
# monta lista unica de assetBaseIds a baixar (a partir do layout + furniture jsons)
# ---------------------------------------------------------------------------
def load_furn(src):
    p = os.path.join(OUT_DIR, f"furniture_{src}.json")
    return {it["slot"]: it for it in json.load(open(p, encoding="utf-8"))}

furn = {src: load_furn(src) for src in {it["src"] for it in LAY.LAYOUT}}

# resolve cada item do layout -> (assetBaseId, name)
wanted = {}  # assetBaseId -> name
for item in LAY.LAYOUT:
    if item.get("reuse"):
        continue  # mesma cadeira reusada, nao baixa de novo
    src, slot = item["src"], item["slot"]
    ov = LAY.OVERRIDE_IDS.get((src, slot))
    if ov:
        name, abid = ov
    else:
        rec = furn[src].get(slot)
        if not rec:
            log("WARN slot sem registro:", src, slot)
            continue
        name, abid = rec.get("name", slot), rec["assetBaseId"]
    wanted[abid] = name

log(f"{len(wanted)} assets unicos a baixar")

# ---------------------------------------------------------------------------
# sobe daemon
# ---------------------------------------------------------------------------
log("starting daemon...")
try:
    client_lib.start_blenderkit_client()
except Exception as e:
    log("start raised:", e)

pid = os.getpid()
for i in range(60):
    try:
        client_lib.get_reports(pid)
        log(f"daemon up after {i*0.5:.1f}s")
        break
    except Exception:
        time.sleep(0.5)
else:
    log("ERROR daemon never up"); sys.exit(2)

headers = {"Authorization": f"Bearer {prefs.api_key}"}


def search_asset(abid):
    url = ("https://www.blenderkit.com/api/v1/search/"
           f"?query=asset_base_id:{abid}+asset_type:model&dict_parameters=1")
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    res = r.json().get("results", [])
    return res[0] if res else None


def download_one(asset_data, timeout_s=180):
    """dispara download e faz polling ate finished; retorna caminho do .blend."""
    download.download(
        asset_data,
        resolution="resolution_0_5K",  # textura leve; cai pro que existir
        model_location=(0.0, 0.0, 0.0),
        model_rotation=(0.0, 0.0, 0.0),
    )
    task_ids = list(download.download_tasks.keys())
    if not task_ids:
        return None
    tid = task_ids[-1]
    last = -1
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            rep = client_lib.get_reports(pid)
        except Exception:
            time.sleep(0.5); continue
        tasks = rep if isinstance(rep, list) else rep.get("tasks", [])
        for t in tasks:
            if not isinstance(t, dict) or t.get("task_id") != tid:
                continue
            st = t.get("status"); pr = t.get("progress", 0)
            if pr != last:
                log(f"   {st} {pr}%"); last = pr
            if st == "finished":
                fps = t.get("result", {}).get("file_paths", [])
                return fps[-1] if fps else None
            if st == "error":
                log("   ERROR:", t.get("message")); return None
        time.sleep(0.5)
    return None


# ---------------------------------------------------------------------------
# baixa cada um; limpa download_tasks entre iteracoes
# ---------------------------------------------------------------------------
manifest = {}
for i, (abid, name) in enumerate(wanted.items(), 1):
    log(f"[{i}/{len(wanted)}] {name[:34]} ({abid[:8]})")
    try:
        ad = search_asset(abid)
        if not ad:
            log("   no search result"); continue
        log("   free:", ad.get("isFree"), "canDl:", ad.get("canDownload"))
        download.download_tasks.clear()
        path = download_one(ad)
        if path and os.path.exists(path):
            manifest[abid] = {"name": name, "path": path,
                              "size": os.path.getsize(path)}
            log("   OK ->", os.path.basename(path), f"{manifest[abid]['size']/1e6:.1f}MB")
        else:
            log("   FAILED (no path)")
    except Exception as e:
        log("   EXC:", e)

log(f"baixados {len(manifest)}/{len(wanted)}")
with open(os.path.join(OUT_DIR, "downloads.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
log("downloads.json salvo")
log("DONE")
