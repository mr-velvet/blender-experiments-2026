"""
Procurar presets de verdade dentro do .blend do Easy Cardboard.

Caminhos onde Blender guarda presets:
  1. Objetos da cena que ja tenham o Easy Cardboard modifier configurado
     (cenas de demo do asset) -> ler os valores dos sockets
  2. Asset Browser catalog (objetos/node_groups marcados como asset com tags)
  3. Cenas multiplas dentro do .blend (uma por preset)
  4. Node groups variantes (ex: "Easy Cardboard - Aged", "EC - Fresh", etc)
"""
import bpy
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
ASSET_BLEND = os.path.join(ROOT, "assets", "easy-cardboard-3.1.blend")
OUTPUT_DIR = os.path.join(ROOT, "output")

def log(m): print(f"[PRESETS] {m}", flush=True)

# Abre o .blend de verdade (nao append — quero ver as cenas/objetos do arquivo)
log(f"Opening {ASSET_BLEND}")
bpy.ops.wm.open_mainfile(filepath=ASSET_BLEND)

# 1. Cenas
print()
print("=" * 70)
print(f"[1] CENAS no arquivo ({len(bpy.data.scenes)})")
print("=" * 70)
for scn in bpy.data.scenes:
    objs = list(scn.objects)
    print(f"  - '{scn.name}' ({len(objs)} objs)")

# 2. Objetos com modifier Easy Cardboard
print()
print("=" * 70)
print(f"[2] OBJETOS com modifier Geometry Nodes que aponta pro Easy Cardboard")
print("=" * 70)
preset_objects = []
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            ng_name = mod.node_group.name
            if 'cardboard' in ng_name.lower() or 'EC' in ng_name or '\U0001F4E6' in ng_name:
                preset_objects.append((obj, mod))
                print(f"  - obj='{obj.name}'  modifier='{mod.name}'  node_group='{ng_name}'  scene_collections={[c.name for c in obj.users_collection]}")

# 3. Pra cada um, dump dos valores dos sockets de input
all_presets = {}
print()
print("=" * 70)
print(f"[3] VALORES dos sockets de cada objeto-preset")
print("=" * 70)
for obj, mod in preset_objects:
    ng = mod.node_group
    print(f"\n--- '{obj.name}' --- (using '{ng.name}')")
    preset = {}
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) != 'INPUT':
            continue
        ident = item.identifier
        name = item.name
        try:
            v = mod[ident]
            if hasattr(v, '__iter__') and not isinstance(v, str):
                v = list(v)
        except Exception:
            v = None
        preset[name] = v
        if v is not None:
            print(f"    {name!r:40s} = {v}")
    all_presets[obj.name] = {"node_group": ng.name, "values": preset}

# 4. Marker assets (Asset Browser)
print()
print("=" * 70)
print(f"[4] DATABLOCKS marcados como ASSET (Asset Browser catalog)")
print("=" * 70)
for collection_type in ('objects', 'node_groups', 'materials', 'meshes'):
    coll = getattr(bpy.data, collection_type, None)
    if not coll:
        continue
    for db in coll:
        if hasattr(db, 'asset_data') and db.asset_data is not None:
            tags = [t.name for t in db.asset_data.tags] if db.asset_data.tags else []
            cat = db.asset_data.catalog_id
            print(f"  - {collection_type}.'{db.name}'  tags={tags}  catalog={cat}")

# 5. Salva
out_path = os.path.join(OUTPUT_DIR, "presets_found.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_presets, f, indent=2, ensure_ascii=False, default=str)
log(f"Salvo: {out_path}")

print()
print(f"[PRESETS] Total de objetos-preset encontrados: {len(preset_objects)}")
print("[PRESETS] === DONE ===")
