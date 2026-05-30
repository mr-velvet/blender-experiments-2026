# -*- coding: utf-8 -*-
"""
experiment-29 / 06_download_model.py
Baixa um MODELO do BlenderKit headless (daemon + api_key) e salva o .blend
baixado pra eu apendar depois. Tenta uma lista de asset_base_id em ordem;
para no primeiro que baixar de verdade. Reusa a arquitetura provada no exp-21.

Roda (com BLENDER_USER_RESOURCES = bl_config_51 do exp-21):
  blender --background --python 06_download_model.py -- <out_dir> <id1> [id2] [id3] ...
"""
import bpy, sys, os, time, json

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT_DIR = argv[0]
IDS = argv[1:]
os.makedirs(OUT_DIR, exist_ok=True)
PKG="blenderkit"

def log(*a): print("[dl]",*a,flush=True)

import addon_utils
addon_utils.enable(PKG, default_set=False, persistent=True)
from blenderkit import client_lib, download  # type: ignore
import requests
prefs = bpy.context.preferences.addons[PKG].preferences
log("api_key:", "***"+(prefs.api_key[-4:] if prefs.api_key else "NONE"))

log("starting daemon...")
try: client_lib.start_blenderkit_client()
except Exception as e: log("start raised:",e)
pid=os.getpid(); ok=False
for i in range(60):
    try: client_lib.get_reports(pid); ok=True; log(f"daemon up {i*0.5:.1f}s"); break
    except Exception: time.sleep(0.5)
if not ok: log("daemon never up"); sys.exit(2)

def fetch_assetdata(bid):
    # tenta com filtro de tipo e, se vazio, sem filtro (alguns nao casam asset_type)
    for q in (f"asset_base_id:{bid}+asset_type:model", f"asset_base_id:{bid}"):
        url=f"https://www.blenderkit.com/api/v1/search/?query={q}&dict_parameters=1"
        try:
            r=requests.get(url, headers={"Authorization":f"Bearer {prefs.api_key}"}, timeout=30)
            r.raise_for_status()
            res=r.json().get("results",[])
            if res:
                log("  fetched via query:",q,"->",res[0].get("name"))
                return res[0]
        except Exception as e:
            log("  fetch err",q,e)
    return None

def try_download(bid):
    ad=fetch_assetdata(bid)
    if not ad:
        log("no asset_data for",bid); return None
    log("asset:",ad.get("name"),"free=",ad.get("isFree"),"canDl=",ad.get("canDownload"))
    download.download(ad, resolution="blend",
                      model_location=(0,0,0), model_rotation=(0,0,0))
    tids=list(download.download_tasks.keys())
    if not tids: log("no task registered"); return None
    tid=tids[-1]
    last=-1
    for i in range(600):
        try: rep=client_lib.get_reports(pid)
        except Exception: time.sleep(0.5); continue
        tasks=rep if isinstance(rep,list) else rep.get("tasks",rep)
        for t in tasks:
            if not isinstance(t,dict) or t.get("task_id")!=tid: continue
            st=t.get("status"); pr=t.get("progress",0)
            if pr!=last: log(f"  {st} {pr}% {t.get('message','')}"); last=pr
            if st=="finished":
                fps=t.get("result",{}).get("file_paths",[])
                log("FINISHED",fps); return (ad, fps[-1] if fps else None)
            if st=="error":
                log("error:",t.get("message")); return None
        time.sleep(0.5)
    log("timeout"); return None

result=None
for bid in IDS:
    log("=== trying",bid,"===")
    try:
        r=try_download(bid)
    except Exception as e:
        log("exc:",e); r=None
    if r and r[1] and os.path.exists(r[1]):
        result=(bid,)+r; break

if not result:
    log("ALL DOWNLOADS FAILED"); sys.exit(5)

bid, ad, blend = result
info={"asset_base_id":bid,"name":ad.get("name"),"blend":blend,
      "size":os.path.getsize(blend)}
json.dump(info, open(os.path.join(OUT_DIR,"downloaded.json"),"w",encoding="utf-8"), indent=2)
log("DOWNLOADED_OK",json.dumps(info))
log("DONE")
