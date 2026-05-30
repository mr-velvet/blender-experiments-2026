# -*- coding: utf-8 -*-
"""
exp-30 / 03_download_plants.py — baixa uma lista de modelos BlenderKit (headless,
daemon+api_key). Para cada id baixa e registra o file_path REAL. Reusa exp-21.
blender --background --python 03_download_plants.py -- <out_json> <name1>=<id1> <name2>=<id2> ...
"""
import bpy, sys, os, time, json
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
OUT=argv[0]; PAIRS=argv[1:]
PKG="blenderkit"
def log(*a): print("[dl]",*a,flush=True)
import addon_utils
addon_utils.enable(PKG, default_set=False, persistent=True)
from blenderkit import client_lib, download
import requests
prefs=bpy.context.preferences.addons[PKG].preferences
try: client_lib.start_blenderkit_client()
except Exception as e: log("start",e)
pid=os.getpid(); ok=False
for i in range(60):
    try: client_lib.get_reports(pid); ok=True; break
    except Exception: time.sleep(0.5)
if not ok: log("daemon down"); sys.exit(2)

def fetch(bid):
    for q in (f"asset_base_id:{bid}+asset_type:model", f"asset_base_id:{bid}"):
        u=f"https://www.blenderkit.com/api/v1/search/?query={q}&dict_parameters=1"
        try:
            r=requests.get(u,headers={"Authorization":f"Bearer {prefs.api_key}"},timeout=30); r.raise_for_status()
            res=r.json().get("results",[])
            if res: return res[0]
        except Exception as e: log("fetch err",e)
    return None

def dl(bid):
    ad=fetch(bid)
    if not ad: return None
    download.download(ad,resolution="blend",model_location=(0,0,0),model_rotation=(0,0,0))
    tids=list(download.download_tasks.keys())
    if not tids: return None
    tid=tids[-1]; last=-1
    for i in range(900):
        try: rep=client_lib.get_reports(pid)
        except Exception: time.sleep(0.5); continue
        for t in (rep if isinstance(rep,list) else rep.get("tasks",rep)):
            if not isinstance(t,dict) or t.get("task_id")!=tid: continue
            st=t.get("status"); pr=t.get("progress",0)
            if pr!=last: log("  ",ad.get("name"),st,pr); last=pr
            if st=="finished":
                fps=t.get("result",{}).get("file_paths",[]); return (ad.get("name"), fps[-1] if fps else None)
            if st=="error": return None
        time.sleep(0.5)
    return None

results={}
for pair in PAIRS:
    name,bid=pair.split("=",1)
    log("=== downloading",name,bid,"===")
    try: r=dl(bid)
    except Exception as e: log("exc",e); r=None
    if r and r[1] and os.path.exists(r[1]):
        results[name]={"id":bid,"name":r[0],"blend":r[1],"size":os.path.getsize(r[1])}
        log("OK",name,"->",r[1])
    else:
        results[name]={"id":bid,"blend":None}
        log("FAIL",name)
json.dump(results,open(OUT,"w",encoding="utf-8"),indent=2)
log("DOWNLOAD_BATCH_DONE")
log(json.dumps(results))
