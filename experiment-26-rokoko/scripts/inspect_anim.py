"""Detalha onde esta a animacao: action por objeto, fcurves por bone."""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])

for o in bpy.data.objects:
    ad = o.animation_data
    if ad and ad.action:
        a = ad.action
        fr = a.frame_range
        bones = set()
        for fc in a.fcurves:
            dp = fc.data_path
            if dp.startswith("pose.bones["):
                bones.add(dp.split('"')[1])
        print(f"OBJ {o.type} {o.name!r} -> action {a.name!r} range={fr[0]:.0f}..{fr[1]:.0f} fcurves={len(a.fcurves)} bones_animados={len(bones)}")
        if bones:
            print("   bones:", ", ".join(sorted(bones)[:12]), "...")
