"""Mostra a direcao (head->tail) dos bones de braço no rest pose, pra source e target."""
import bpy, sys, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
if path.lower().endswith(".glb"):
    bpy.ops.import_scene.gltf(filepath=path)
else:
    bpy.ops.import_scene.fbx(filepath=path)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
print("ARMATURE", arm.name)
for bn in arm.data.bones:
    n = bn.name.lower()
    if any(k in n for k in ['arm', 'shoulder', 'clavicle', 'forearm', 'hand', 'upperarm', 'lowerarm']):
        v = (bn.tail_local - bn.head_local).normalized()
        print(f"  {bn.name:16} dir=({v.x:+.2f},{v.y:+.2f},{v.z:+.2f})")
