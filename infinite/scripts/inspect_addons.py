"""Lista addons disponiveis (built-in) no Blender e tenta habilitar os uteis pra escadas/geometria."""
import bpy
import addon_utils
import json
import sys

WANTED_KEYWORDS = ["mesh", "stair", "archi", "extra", "tree", "sapling", "ant", "scatter", "node"]

info = []
for mod in addon_utils.modules():
    bl = mod.bl_info if hasattr(mod, "bl_info") else {}
    name = bl.get("name", mod.__name__)
    category = bl.get("category", "")
    mod_id = mod.__name__
    enabled = addon_utils.check(mod_id)[1]
    interesting = any(k in (name + " " + category + " " + mod_id).lower() for k in WANTED_KEYWORDS)
    if interesting:
        info.append({
            "id": mod_id,
            "name": name,
            "category": category,
            "enabled": enabled,
        })

print(json.dumps(info, indent=2))

CANDIDATES = [
    "add_mesh_extra_objects",
    "archimesh",
    "add_curve_extra_objects",
    "node_arrange",
    "ant_landscape",
    "add_curve_sapling",
]

print("\n=== Tentando habilitar candidatos ===")
for cid in CANDIDATES:
    try:
        loaded_default, loaded_state = addon_utils.check(cid)
        if not loaded_state:
            addon_utils.enable(cid, default_set=True, persistent=True)
            print(f"OK enabled: {cid}")
        else:
            print(f"ja estava: {cid}")
    except Exception as e:
        print(f"FAIL {cid}: {e}")

print("\n=== Estado final ===")
for cid in CANDIDATES:
    print(f"  {cid}: enabled={addon_utils.check(cid)[1]}")

# checar operadores de stair (archimesh)
print("\n=== bpy.ops.mesh.archimesh_stairs disponivel? ===")
try:
    op = bpy.ops.mesh.archimesh_stairs
    print(f"  poll: {op.poll()}")
except Exception as e:
    print(f"  nao disponivel: {e}")

# extra mesh objects: ha gear/honeycomb/etc
print("\n=== bpy.ops.mesh.primitive_*_add (extras) ===")
ops_to_test = [
    "primitive_gear",
    "primitive_torusknot_add",
    "primitive_honeycomb_add",
    "primitive_round_cube_add",
    "primitive_steppyramid_add",
]
for op_name in ops_to_test:
    try:
        op = getattr(bpy.ops.mesh, op_name, None)
        if op:
            print(f"  mesh.{op_name}: existe")
        else:
            print(f"  mesh.{op_name}: nao encontrado")
    except Exception as e:
        print(f"  mesh.{op_name}: erro {e}")
