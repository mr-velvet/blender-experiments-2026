"""Inspeciona um GLB do Rokoko Create: objetos, armature, bones, animacao, frames."""
import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)

print("=== OBJETOS ===")
for o in bpy.data.objects:
    print(f"  {o.type:10} {o.name!r}  verts={len(o.data.vertices) if o.type=='MESH' else '-'}")

arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm:
    print(f"\n=== ARMATURE {arm.name!r} — {len(arm.data.bones)} bones ===")
    for b in arm.data.bones:
        print(f"  {b.name}")
else:
    print("\n!! SEM ARMATURE")

print("\n=== ACTIONS ===")
for a in bpy.data.actions:
    fr = a.frame_range
    print(f"  {a.name!r}  range={fr[0]:.0f}..{fr[1]:.0f}  fcurves={len(a.fcurves)}")

print(f"\nscene fps={bpy.context.scene.render.fps}  frame_start={bpy.context.scene.frame_start} end={bpy.context.scene.frame_end}")
