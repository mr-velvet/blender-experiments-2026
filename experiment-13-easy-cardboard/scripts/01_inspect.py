"""Inspect easy-cardboard-3.1.blend — list node groups, materials, collections, objects."""
import bpy
import sys

print("=" * 60)
print("BLEND INSPECTION")
print("=" * 60)

print(f"\n[NODE GROUPS] ({len(bpy.data.node_groups)})")
for ng in bpy.data.node_groups:
    print(f"  - '{ng.name}' (type={ng.type}, bl_idname={ng.bl_idname})")

print(f"\n[MATERIALS] ({len(bpy.data.materials)})")
for m in bpy.data.materials:
    print(f"  - '{m.name}'")

print(f"\n[COLLECTIONS] ({len(bpy.data.collections)})")
for c in bpy.data.collections:
    print(f"  - '{c.name}' (objects: {len(c.objects)})")

print(f"\n[OBJECTS] ({len(bpy.data.objects)})")
for o in bpy.data.objects:
    mods = [m.name for m in o.modifiers] if o.type == 'MESH' else []
    print(f"  - '{o.name}' (type={o.type}, modifiers={mods})")

print(f"\n[IMAGES] ({len(bpy.data.images)})")
for img in bpy.data.images:
    print(f"  - '{img.name}' (size={img.size[0]}x{img.size[1]}, src={img.source})")

print(f"\n[TEXTS / SCRIPTS] ({len(bpy.data.texts)})")
for t in bpy.data.texts:
    print(f"  - '{t.name}' ({len(t.as_string())} chars)")

# Look at geometry nodes inputs/outputs of any cardboard-related node group
print("\n" + "=" * 60)
print("CARDBOARD NODE GROUP DETAILS")
print("=" * 60)
for ng in bpy.data.node_groups:
    if 'cardboard' in ng.name.lower() or 'easy' in ng.name.lower() or 'cb' in ng.name.lower():
        print(f"\n--- Node Group: {ng.name} ---")
        if hasattr(ng, 'interface'):
            print("  Interface items:")
            for item in ng.interface.items_tree:
                print(f"    {item.item_type} '{item.name}' (in_out={getattr(item, 'in_out', 'N/A')}, socket_type={getattr(item, 'socket_type', 'N/A')})")
        print(f"  Nodes: {len(ng.nodes)}")
        for n in ng.nodes[:20]:
            print(f"    - {n.bl_idname} '{n.name}'")

print("\nDONE.")
