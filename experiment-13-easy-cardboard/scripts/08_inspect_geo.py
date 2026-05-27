"""
Passo 1 — inspecao dirigida.

Abre o .blend do Easy Cardboard 3.1 Plus e imprime, pros dois node groups
que vamos usar (Simple Box Creator + Easy Cardboard 3.0):
  - cada socket de input: nome exato, tipo, default, min/max, descricao
  - lista de subgrupos internos que contenham termos geometricos
    (solidify, displace, split, extrude, mesh, points, fuzz, hairs, fibers)

Saida:
  - print no terminal
  - output/sockets.json com os dados estruturados pra eu te apresentar
"""
import bpy
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NG_BOX = "Simple Box Creator"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"

GEO_HINTS = (
    "solidify", "displace", "split", "extrude", "subdivide",
    "mesh", "points", "fuzz", "hair", "fiber", "fibre",
    "edge", "bevel", "wear", "damage", "noise", "boolean",
)

def log(m): print(f"[INSPECT] {m}", flush=True)

log(f"Loading asset: {ASSET_BLEND}")
with bpy.data.libraries.load(ASSET_BLEND, link=False) as (data_from, data_to):
    data_to.node_groups = list(data_from.node_groups)
log(f"Loaded {len(bpy.data.node_groups)} node groups total")

def describe_socket(item):
    info = {
        "name": item.name,
        "identifier": getattr(item, "identifier", None),
        "in_out": getattr(item, "in_out", None),
        "socket_type": getattr(item, "socket_type", None),
        "default": None,
        "min": None,
        "max": None,
        "description": getattr(item, "description", "") or "",
    }
    for attr in ("default_value",):
        if hasattr(item, attr):
            try:
                v = getattr(item, attr)
                if hasattr(v, "__iter__") and not isinstance(v, str):
                    info["default"] = list(v)
                else:
                    info["default"] = v
            except Exception:
                pass
    for attr_name, key in (("min_value", "min"), ("max_value", "max")):
        if hasattr(item, attr_name):
            try:
                info[key] = getattr(item, attr_name)
            except Exception:
                pass
    return info

def dump_node_group(name):
    if name not in bpy.data.node_groups:
        log(f"  !! node group '{name}' NOT FOUND")
        return None
    ng = bpy.data.node_groups[name]
    out = {
        "name": name,
        "bl_idname": ng.bl_idname,
        "type": ng.type,
        "inputs": [],
        "outputs": [],
        "internal_nodes_total": len(ng.nodes),
        "internal_node_types": {},
        "internal_subgroups_geo_hint": [],
    }
    # interface
    if hasattr(ng, "interface"):
        for item in ng.interface.items_tree:
            io = getattr(item, "in_out", None)
            if io == "INPUT":
                out["inputs"].append(describe_socket(item))
            elif io == "OUTPUT":
                out["outputs"].append(describe_socket(item))
    # nodes internos
    for n in ng.nodes:
        out["internal_node_types"][n.bl_idname] = out["internal_node_types"].get(n.bl_idname, 0) + 1
        nname_low = (n.name or "").lower()
        # subgrupos que parecem geo
        if n.bl_idname == "GeometryNodeGroup" and n.node_tree:
            sub_name = n.node_tree.name
            if any(h in sub_name.lower() for h in GEO_HINTS):
                out["internal_subgroups_geo_hint"].append(sub_name)
    out["internal_subgroups_geo_hint"] = sorted(set(out["internal_subgroups_geo_hint"]))
    return out

def print_group(g):
    if not g:
        return
    print()
    print("=" * 80)
    print(f"NODE GROUP: {g['name']}  ({g['bl_idname']})")
    print("=" * 80)
    print(f"Internal nodes: {g['internal_nodes_total']}")
    print(f"Node type histogram (top 15):")
    items = sorted(g["internal_node_types"].items(), key=lambda x: -x[1])[:15]
    for k, v in items:
        print(f"  {v:4d}  {k}")
    print(f"Internal subgroups with geo-hint names ({len(g['internal_subgroups_geo_hint'])}):")
    for s in g["internal_subgroups_geo_hint"]:
        print(f"  - {s}")
    print(f"\nINPUTS ({len(g['inputs'])}):")
    for s in g["inputs"]:
        ident = s["identifier"]
        desc = (s["description"] or "").replace("\n", " ")[:80]
        rng = ""
        if s["min"] is not None or s["max"] is not None:
            rng = f"  [min={s['min']}  max={s['max']}]"
        print(f"  - '{s['name']}'  type={s['socket_type']}  default={s['default']}{rng}")
        if desc:
            print(f"      desc: {desc}")
    print(f"\nOUTPUTS ({len(g['outputs'])}):")
    for s in g["outputs"]:
        print(f"  - '{s['name']}'  type={s['socket_type']}")

dump = {}
for name in (NG_BOX, NG_CARDBOARD):
    g = dump_node_group(name)
    if g:
        dump[name] = g
        print_group(g)

# Tambem listar TODOS os subgrupos que tem nome com hint, pra eu ver subsistemas escondidos
print()
print("=" * 80)
print("TODOS os node groups carregados com nome contendo geo-hint:")
print("=" * 80)
all_hits = []
for ng in bpy.data.node_groups:
    low = ng.name.lower()
    hits = [h for h in GEO_HINTS if h in low]
    if hits:
        all_hits.append((ng.name, hits))
for n, h in sorted(all_hits):
    print(f"  - {n}    (hints: {','.join(h)})")
dump["_all_geo_named_groups"] = [n for n, _ in all_hits]

out_path = os.path.join(OUTPUT_DIR, "sockets.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(dump, f, indent=2, ensure_ascii=False, default=str)
log(f"Wrote {out_path}")
print("\n[INSPECT] === DONE ===", flush=True)
