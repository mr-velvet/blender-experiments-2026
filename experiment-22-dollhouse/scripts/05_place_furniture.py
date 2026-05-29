"""
05_place_furniture.py — abre a estrutura da casa e mobilia: faz append da collection
de cada movel baixado, mede o bbox combinado, escala pra um tamanho alvo, rotaciona,
posiciona no comodo (coords locais u,v do layout) e assenta no chao.

  blender --background --python 05_place_furniture.py

Saida: out/dollhouse_furnished.blend  (+ atualiza placements.json com o que entrou)
"""
import bpy
import sys
import os
import json
import math
from mathutils import Vector

sys.path.append(os.path.dirname(__file__))
import layout as LAY

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))


def log(*a):
    print("[place]", *a, flush=True)


meta = json.load(open(os.path.join(OUT_DIR, "rooms.json"), encoding="utf-8"))
manifest = json.load(open(os.path.join(OUT_DIR, "downloads.json"), encoding="utf-8"))

# rooms indexados por (floor, side)
rooms = {(r["floor"], r["side"]): r for r in meta["rooms"]}


def load_furn(src):
    p = os.path.join(OUT_DIR, f"furniture_{src}.json")
    return {it["slot"]: it for it in json.load(open(p, encoding="utf-8"))}

furn = {src: load_furn(src) for src in {it["src"] for it in LAY.LAYOUT}}


def resolve_id(src, slot):
    ov = LAY.OVERRIDE_IDS.get((src, slot))
    if ov:
        return ov[1], ov[0]
    rec = furn[src].get(slot)
    if not rec:
        return None, None
    return rec["assetBaseId"], rec.get("name", slot)


# abre a estrutura
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, "dollhouse_structure.blend"))
scene = bpy.context.scene


def obj_world_bbox(objs, robust=False):
    """bbox em mundo. Se robust=True, usa percentil 1-99 dos VERTICES reais (avaliados
    via depsgraph) -> imune a empties/luzes/geometria espuria que poluem bound_box.
    Senao, usa bound_box (rapido)."""
    if not robust:
        mins = Vector((1e9,)*3); maxs = Vector((-1e9,)*3); found = False
        for o in objs:
            if o.type not in {'MESH','CURVE','SURFACE','FONT','META'}: continue
            try: bb = o.bound_box
            except Exception: continue
            for c in bb:
                wc = o.matrix_world @ Vector(c)
                for i in range(3):
                    mins[i]=min(mins[i],wc[i]); maxs[i]=max(maxs[i],wc[i])
                found = True
        return (mins, maxs) if found else (None, None)

    # robusto: coleta todos os vertices em mundo, percentil 1-99 por eixo
    deps = bpy.context.evaluated_depsgraph_get()
    xs, ys, zs = [], [], []
    for o in objs:
        if o.type != 'MESH':
            continue
        oe = o.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        mw = oe.matrix_world
        for v in me.vertices:
            w = mw @ v.co
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
        oe.to_mesh_clear()
    if not xs:
        return obj_world_bbox(objs, robust=False)

    def pct(arr, p):
        arr = sorted(arr)
        i = max(0, min(len(arr)-1, int(p*(len(arr)-1))))
        return arr[i]
    mins = Vector((pct(xs,0.01), pct(ys,0.01), pct(zs,0.01)))
    maxs = Vector((pct(xs,0.99), pct(ys,0.99), pct(zs,0.99)))
    return mins, maxs


def append_collection(path, coll_name):
    """append a collection; retorna lista de objetos novos (top-level + filhos)."""
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        names = [c for c in df.collections if c == coll_name] or df.collections[:1]
        dt.collections = names
    new_objs = []
    for c in dt.collections:
        if not c:
            continue
        # liga os objetos da collection na cena (sem instanciar empty)
        for o in c.objects:
            if o.name not in scene.collection.objects:
                scene.collection.objects.link(o)
            new_objs.append(o)
    # dedup e pega tambem objetos novos que vieram como users
    after = set(bpy.data.objects)
    for o in (after - before):
        if o not in new_objs:
            if o.name not in scene.collection.objects:
                try:
                    scene.collection.objects.link(o)
                except Exception:
                    pass
            new_objs.append(o)
    return new_objs


def place_item(item, asset_objs, room, cache_w=None):
    """transforma o grupo de objetos do asset pra dentro do comodo.
    Usa bbox ROBUSTO (percentil de vertices) pra escala/assento -> imune a
    geometria espuria dos assets (luzes, empties, outliers)."""
    mins, maxs = obj_world_bbox(asset_objs, robust=True)
    if mins is None:
        log("   sem bbox, pula"); return None
    size = maxs - mins
    center = (mins + maxs) / 2.0

    # empty pivot no centro-base do asset
    pivot = bpy.data.objects.new(f"piv_{item['slot']}_{item['floor']}{item['side']}", None)
    scene.collection.objects.link(pivot)
    pivot.location = Vector((center.x, center.y, mins.z))  # base no chao do asset
    for o in asset_objs:
        if o.parent is None:
            o.parent = pivot
            o.matrix_parent_inverse = pivot.matrix_world.inverted()

    # escala uniforme: prioriza target_h (altura) se dado, senao target_w (maior lado XY)
    target_h = item.get("target_h")
    target_w = item.get("target_w")
    s = None
    if target_h and size.z > 1e-5:
        s = target_h / size.z
    elif target_w:
        cur = max(size.x, size.y)
        if cur > 1e-5:
            s = target_w / cur
    if s:
        pivot.scale = (s, s, s)
    bpy.context.view_layer.update()

    # rotaciona em Z
    pivot.rotation_euler.z = math.radians(item.get("rot_z", 0))
    bpy.context.view_layer.update()

    # recomputa bbox robusto apos escala+rot pra reassentar
    mins2, maxs2 = obj_world_bbox(asset_objs, robust=True)
    if mins2 is None:
        mins2, maxs2 = mins, maxs
    # posicao alvo em mundo a partir de (u,v) do comodo
    u = item["u"]; v = item["v"]
    wx = room["x0"] + u * (room["x1"] - room["x0"])
    wy = room["y0"] + v * (room["y1"] - room["y0"])
    z_floor = room["z"]

    # apoio
    apoio = item.get("apoio", "floor")
    if apoio == "on_desk":
        z_target = z_floor + 0.75  # cima de uma mesa tipica
    elif apoio == "rug":
        z_target = z_floor + 0.005
    elif isinstance(apoio, (int, float)):
        z_target = z_floor + float(apoio)
    else:
        z_target = z_floor

    # delta: leva o centro-XY do bbox atual pra (wx,wy) e a base pra z_target
    cx_now = (mins2.x + maxs2.x) / 2.0
    cy_now = (mins2.y + maxs2.y) / 2.0
    base_now = mins2.z
    pivot.location.x += (wx - cx_now)
    pivot.location.y += (wy - cy_now)
    pivot.location.z += (z_target - base_now)
    bpy.context.view_layer.update()
    return pivot


placements = []
chair_cache = None  # pra reuse da cadeira

for item in LAY.LAYOUT:
    src, slot = item["src"], item["slot"]
    abid, name = resolve_id(src, slot if not item.get("reuse") else item["reuse"])
    room = rooms.get((item["floor"], item["side"]))
    if room is None:
        log("comodo inexistente", item["floor"], item["side"]); continue
    rec = manifest.get(abid)
    if rec is None:
        log("WARN asset nao baixado:", slot, abid); continue

    # nome da collection = nome do asset (BlenderKit empacota assim)
    log(f"{item['floor']}{item['side']:5s} {slot:14s} <- {rec['name'][:30]}")
    coll_name = None
    # descobre o nome da collection no .blend
    with bpy.data.libraries.load(rec["path"], link=False) as (df, dt):
        if df.collections:
            coll_name = df.collections[0]
    objs = append_collection(rec["path"], coll_name)
    if not objs:
        log("   append vazio, pula"); continue

    pivot = place_item(item, objs, room)
    if pivot:
        placements.append({
            "slot": slot, "floor": item["floor"], "side": item["side"],
            "name": rec["name"], "asset_id": abid,
        })

log(f"colocados {len(placements)} moveis")
with open(os.path.join(OUT_DIR, "placements.json"), "w", encoding="utf-8") as f:
    json.dump(placements, f, indent=2, ensure_ascii=False)

out = os.path.join(OUT_DIR, "dollhouse_furnished.blend")
bpy.ops.wm.save_as_mainfile(filepath=out)
log("saved", out)
log("DONE")
