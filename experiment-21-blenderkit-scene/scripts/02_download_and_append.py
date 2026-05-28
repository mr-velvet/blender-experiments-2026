"""
02_download_and_append.py — pipeline headless completo do BlenderKit:

  1. sobe o client daemon do BlenderKit
  2. busca o asset-scene "The Lonely Outpost" via API do addon
  3. dispara o download (sem operador modal / sem asset bar)
  4. faz polling dos reports do daemon ate o download terminar
  5. append_scene() do proprio addon -> scene na cena
  6. salva o .blend resultante e renderiza um still

Roda via:
  blender --background --python 02_download_and_append.py -- <asset_base_id> <out_dir>

Depende do addon ja instalado/habilitado e api_key salva (ver 01_install_addon.py),
rodando com o MESMO BLENDER_USER_RESOURCES.
"""
import bpy
import sys
import os
import time
import json
import traceback

argv = sys.argv
argv = argv[argv.index("--") + 1:]
ASSET_BASE_ID = argv[0]
OUT_DIR = argv[1]
os.makedirs(OUT_DIR, exist_ok=True)

PKG = "blenderkit"


def log(*a):
    print("[dl]", *a, flush=True)


# garante addon habilitado nesta sessao
import addon_utils
addon_utils.enable(PKG, default_set=False, persistent=True)

bk = sys.modules[PKG]
from blenderkit import client_lib, download, append_link, paths, search, global_vars  # type: ignore

prefs = bpy.context.preferences.addons[PKG].preferences
log("api_key:", "***" + (prefs.api_key[-4:] if prefs.api_key else "NONE"))
log("global_dir:", prefs.global_dir)

# ---------------------------------------------------------------------------
# 1. sobe o client daemon
# ---------------------------------------------------------------------------
log("starting blenderkit client daemon...")
try:
    client_lib.start_blenderkit_client()
except Exception as e:
    log("start_blenderkit_client raised:", e)

# espera o daemon responder ao /report
pid = os.getpid()
daemon_ok = False
for i in range(60):
    try:
        rep = client_lib.get_reports(pid)
        daemon_ok = True
        log(f"daemon responding after {i*0.5:.1f}s")
        break
    except Exception as e:
        time.sleep(0.5)
if not daemon_ok:
    log("ERROR: daemon never responded. abort.")
    sys.exit(2)

# ---------------------------------------------------------------------------
# 2. busca o asset via API publica do servidor (formato que o daemon espera)
# ---------------------------------------------------------------------------
import requests

search_url = (
    "https://www.blenderkit.com/api/v1/search/"
    f"?query=asset_base_id:{ASSET_BASE_ID}+asset_type:scene&dict_parameters=1"
)
log("searching:", search_url)
headers = {"Authorization": f"Bearer {prefs.api_key}"}
r = requests.get(search_url, headers=headers, timeout=30)
r.raise_for_status()
results = r.json().get("results", [])
if not results:
    log("ERROR: no search results")
    sys.exit(3)
asset_data = results[0]
log("asset:", asset_data.get("name"), "| type:", asset_data.get("assetType"))
log("canDownload:", asset_data.get("canDownload"), "| isFree:", asset_data.get("isFree"))

# salva o asset_data pra inspecao
with open(os.path.join(OUT_DIR, "asset_data.json"), "w", encoding="utf-8") as f:
    json.dump(asset_data, f, indent=2)

# ---------------------------------------------------------------------------
# 3. dispara o download (scene -> precisa model_location/rotation nos kwargs)
# ---------------------------------------------------------------------------
resolution = "blend"  # scene baixa o .blend original
log("starting download, resolution=", resolution)
download.download(
    asset_data,
    resolution=resolution,
    model_location=(0.0, 0.0, 0.0),
    model_rotation=(0.0, 0.0, 0.0),
)
task_ids = list(download.download_tasks.keys())
log("download task_ids:", task_ids)
if not task_ids:
    log("ERROR: no download task registered")
    sys.exit(4)
target_task_id = task_ids[0]

# ---------------------------------------------------------------------------
# 4. polling dos reports ate finished, sem timers modais
# ---------------------------------------------------------------------------
file_paths = None
last_progress = -1
for i in range(600):  # ate 5 min (0.5s * 600)
    try:
        rep = client_lib.get_reports(pid)
    except Exception as e:
        time.sleep(0.5)
        continue
    # rep e uma lista de tasks (dicts)
    tasks = rep if isinstance(rep, list) else rep.get("tasks", rep)
    for t in tasks:
        if not isinstance(t, dict):
            continue
        if t.get("task_id") != target_task_id:
            continue
        status = t.get("status")
        prog = t.get("progress", 0)
        if prog != last_progress:
            log(f"  download {status} {prog}% - {t.get('message','')}")
            last_progress = prog
        if status == "finished":
            file_paths = t.get("result", {}).get("file_paths", [])
            log("FINISHED. file_paths:", file_paths)
            break
        if status == "error":
            log("ERROR task:", t.get("message"))
            sys.exit(5)
    if file_paths is not None:
        break
    time.sleep(0.5)

if not file_paths:
    log("ERROR: download did not finish in time")
    sys.exit(6)

blend_path = file_paths[-1]
log("downloaded blend:", blend_path, "exists:", os.path.exists(blend_path))

# ---------------------------------------------------------------------------
# 5. append da scene via funcao do proprio addon
# ---------------------------------------------------------------------------
scenes_before = set(s.name for s in bpy.data.scenes)
log("scenes before:", scenes_before)

new_scene = append_link.append_scene(blend_path, link=False, fake_user=False)
if new_scene is None:
    log("ERROR: append_scene returned None")
    sys.exit(7)
log("APPENDED scene:", new_scene.name)

scenes_after = set(s.name for s in bpy.data.scenes)
log("scenes after:", scenes_after)
log("new scenes:", scenes_after - scenes_before)

# troca a scene ativa pra recem-importada
bpy.context.window.scene = new_scene
sc = new_scene
log("active scene:", sc.name)
log("objects in scene:", len(sc.objects))
obj_types = {}
for o in sc.objects:
    obj_types[o.type] = obj_types.get(o.type, 0) + 1
log("object types:", obj_types)
log("camera:", sc.camera.name if sc.camera else "NONE")
log("world:", sc.world.name if sc.world else "NONE")

# inventario pra relatorio
inv = {
    "asset_name": asset_data.get("name"),
    "asset_base_id": ASSET_BASE_ID,
    "blend_path": blend_path,
    "blend_size_bytes": os.path.getsize(blend_path) if os.path.exists(blend_path) else None,
    "scene_name": sc.name,
    "objects_total": len(sc.objects),
    "object_types": obj_types,
    "has_camera": bool(sc.camera),
    "has_world": bool(sc.world),
    "materials": len(bpy.data.materials),
    "images": len(bpy.data.images),
    "meshes": len(bpy.data.meshes),
}
with open(os.path.join(OUT_DIR, "scene_inventory.json"), "w", encoding="utf-8") as f:
    json.dump(inv, f, indent=2)
log("inventory:", json.dumps(inv, indent=2))

# ---------------------------------------------------------------------------
# 6. salva o .blend resultante
# ---------------------------------------------------------------------------
out_blend = os.path.join(OUT_DIR, "lonely_outpost_appended.blend")
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
log("saved blend:", out_blend)
log("PIPELINE DONE")
