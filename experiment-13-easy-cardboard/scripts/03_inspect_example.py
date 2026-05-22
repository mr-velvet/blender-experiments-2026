"""
Inspect the example 'Plane' object in the original asset blend — see exactly
how they configured the Easy Cardboard modifier (socket values + UV mapping).
We copy those values verbatim instead of guessing.
"""
import bpy

print("=" * 60)
print("EXAMPLE OBJECT INSPECTION")
print("=" * 60)

for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    print(f"\n--- Object: '{obj.name}' ---")
    print(f"  Vertices: {len(obj.data.vertices)}")
    print(f"  Polygons: {len(obj.data.polygons)}")
    print(f"  Dimensions (m): {tuple(round(d, 4) for d in obj.dimensions)}")
    print(f"  Scale: {tuple(round(s, 4) for s in obj.scale)}")
    print(f"  UV layers: {[l.name for l in obj.data.uv_layers]}")

    # UV bounding box of layer 0
    if obj.data.uv_layers:
        uvs = obj.data.uv_layers[0].data
        us = [uv.uv[0] for uv in uvs]
        vs = [uv.uv[1] for uv in uvs]
        print(f"  UV range: u=[{min(us):.3f}, {max(us):.3f}] v=[{min(vs):.3f}, {max(vs):.3f}]")

    print(f"  Modifiers ({len(obj.modifiers)}):")
    for mod in obj.modifiers:
        print(f"    [{mod.type}] '{mod.name}'")
        if mod.type == 'NODES' and mod.node_group:
            ng = mod.node_group
            print(f"      node_group: '{ng.name}'")
            for item in ng.interface.items_tree:
                if getattr(item, 'in_out', None) == 'INPUT':
                    ident = item.identifier
                    try:
                        val = mod[ident]
                    except KeyError:
                        val = '<unset>'
                    socket_type = getattr(item, 'socket_type', '?')
                    print(f"        {item.name!r:40s} ({socket_type:30s}) = {val}")

    # material slots
    print(f"  Materials: {[m.name if m else None for m in obj.data.materials]}")

print("\n=== DONE ===")
