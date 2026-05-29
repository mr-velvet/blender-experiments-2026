"""baixa os backups dos assets suspeitos, renderiza principal vs backup isolados
lado a lado pra decidir a troca. Usa o daemon do BlenderKit.
  blender --background --python check_swaps.py
"""
import bpy, sys, os, time, json, math
sys.path.append(os.path.dirname(__file__))
import render_lib as rl
from mathutils import Vector

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
PKG = "blenderkit"

import addon_utils
addon_utils.enable(PKG, default_set=False, persistent=True)
from blenderkit import client_lib, download
import requests
prefs = bpy.context.preferences.addons[PKG].preferences

# assets a comparar: (label, assetBaseId)
CANDIDATES = {
    "floorlamp_main":   "40123399-aea5-48ad-9e09-0d63bb605986",
    "floorlamp_backup": "cdfbf38a-9001-4c95-a8ab-50fe55e098e0",
    "bed_main":         "639721f0-b1dc-410f-9232-d1b99b27ba76",
    "bed_backup":       "5cba3cb3-9cc2-4204-8725-bf9efc35bb04",
    "armchair_backup":  "2104acb8-e3bf-4a3d-8f26-f72f260b14e3",
}


def log(*a): print("[swap]", *a, flush=True)

client_lib.start_blenderkit_client()
pid = os.getpid()
for i in range(60):
    try: client_lib.get_reports(pid); break
    except Exception: time.sleep(0.5)
headers = {"Authorization": f"Bearer {prefs.api_key}"}

def get_asset(abid):
    url=("https://www.blenderkit.com/api/v1/search/"
         f"?query=asset_base_id:{abid}+asset_type:model&dict_parameters=1")
    r=requests.get(url, headers=headers, timeout=30); r.raise_for_status()
    res=r.json().get("results",[]); return res[0] if res else None

def dl(ad, t=180):
    download.download_tasks.clear()
    download.download(ad, resolution="resolution_0_5K",
                      model_location=(0,0,0), model_rotation=(0,0,0))
    tid=list(download.download_tasks.keys())[-1]
    dl_end=time.time()+t
    while time.time()<dl_end:
        try: rep=client_lib.get_reports(pid)
        except Exception: time.sleep(0.5); continue
        for tk in (rep if isinstance(rep,list) else []):
            if isinstance(tk,dict) and tk.get("task_id")==tid:
                if tk.get("status")=="finished":
                    fp=tk.get("result",{}).get("file_paths",[]); return fp[-1] if fp else None
                if tk.get("status")=="error": return None
        time.sleep(0.5)
    return None

paths={}
for label, abid in CANDIDATES.items():
    ad=get_asset(abid)
    if not ad: log(label,"no asset"); continue
    p=dl(ad)
    paths[label]={"path":p,"name":ad.get("name"),"abid":abid}
    log(label, ad.get("name"), "->", os.path.basename(p) if p else "FAIL")

# render cada um isolado
for label, info in paths.items():
    if not info["path"]: continue
    bpy.ops.wm.read_homefile(use_empty=True)
    with bpy.data.libraries.load(info["path"], link=False) as (df, dt):
        dt.collections=[df.collections[0]] if df.collections else []
    objs=[]
    for c in dt.collections:
        if c:
            for o in c.objects:
                bpy.context.scene.collection.objects.link(o); objs.append(o)
    mn,mx=rl.world_bbox(objs); ctr=(mn+mx)/2; sz=mx-mn; r=max(sz)*1.7+0.5
    rl.setup_world(strength=1.0); rl.add_sun(energy=3)
    rl.add_camera(location=(ctr.x+r,ctr.y-r,ctr.z+r*0.5), target=ctr, lens=45)
    out=os.path.join(OUT_DIR,"preview",f"swap_{label}.png")
    rl.render(out, engine='BLENDER_EEVEE', samples=16, res=(420,420))
    log(label, "dim", [round(x,2) for x in sz], "rendered")

# salva os paths/abids dos backups baixados pro manifest principal
extra=json.load(open(os.path.join(OUT_DIR,"downloads.json"),encoding="utf-8"))
for label,info in paths.items():
    if info["path"] and "backup" in label:
        extra[info["abid"]]={"name":info["name"],"path":info["path"],
                             "size":os.path.getsize(info["path"])}
json.dump(extra, open(os.path.join(OUT_DIR,"downloads.json"),"w",encoding="utf-8"),
          indent=2, ensure_ascii=False)
log("DONE")
