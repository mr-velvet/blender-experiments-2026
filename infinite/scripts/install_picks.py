"""Instala addons escolhidos."""
import bpy

bpy.context.preferences.system.use_online_access = True

picks = ["archimesh", "modern_primitive", "maze_generator", "sapling_tree_gen"]
for pkg in picks:
    try:
        r = bpy.ops.extensions.package_install(repo_index=0, pkg_id=pkg, enable_on_install=True)
        print(f"OK {pkg}: {r}")
    except Exception as e:
        print(f"FAIL {pkg}: {str(e)[:120]}")

# verificar ops
print("\n--- verificando ops ---")
tests = [
    ("mesh", "archimesh_stairs"),
    ("mesh", "primitive_steppyramid_add"),
    ("curve", "tree_add"),
]
for ns, op in tests:
    o = getattr(getattr(bpy.ops, ns), op, None)
    print(f"  {ns}.{op}: {'EXISTS' if o else 'missing'}")
