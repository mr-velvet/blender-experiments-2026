"""Lista os sockets de input do node group do cardboard + nodes do material Clay."""
import bpy

CARDBOARD = r"C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\assets\easy-cardboard-3.1.blend"
CLAY = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"

with bpy.data.libraries.load(CARDBOARD, link=False) as (df, dt):
    dt.node_groups = ['\U0001F4E6 Easy Cardboard 3.0']
ng = bpy.data.node_groups['\U0001F4E6 Easy Cardboard 3.0']
print("=== CARDBOARD INPUTS ===")
for item in ng.interface.items_tree:
    if getattr(item, 'in_out', None) == 'INPUT':
        st = getattr(item, 'socket_type', '?')
        dv = getattr(item, 'default_value', None)
        print(f"  [{item.identifier}] {item.name!r}  type={st}  default={dv}")

with bpy.data.libraries.load(CLAY, link=False) as (df, dt):
    dt.materials = ['Modeling Clay', 'Clay Doh']
for mn in ['Modeling Clay', 'Clay Doh']:
    m = bpy.data.materials[mn]
    print(f"=== CLAY MAT {mn!r} ===  displacement={m.displacement_method if hasattr(m,'displacement_method') else '?'}")
    nt = m.node_tree
    for n in nt.nodes:
        print(f"  node {n.type} {n.name!r}")
