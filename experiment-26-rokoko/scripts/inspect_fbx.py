"""Inspeciona rig de um FBX alvo."""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=argv[0])
print("=== OBJETOS ===")
for o in bpy.data.objects:
    extra = f"verts={len(o.data.vertices)}" if o.type=='MESH' else ""
    print(f"  {o.type:9} {o.name!r} {extra}")
arm = next((o for o in bpy.data.objects if o.type=='ARMATURE'), None)
if arm:
    print(f"\n=== ARMATURE {arm.name!r} — {len(arm.data.bones)} bones ===")
    for b in arm.data.bones:
        print(f"  {b.name}")
    print(f"\nscale={tuple(round(s,4) for s in arm.scale)}  dims_mesh:")
    for o in bpy.data.objects:
        if o.type=='MESH':
            print(f"   {o.name}: dim={tuple(round(d,3) for d in o.dimensions)}")
