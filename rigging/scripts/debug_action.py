"""Abre o .blend e inspeciona a action WalkCycle."""
import bpy
import sys
from pathlib import Path

blend = sys.argv[-1] if len(sys.argv) > 1 else None
if not blend:
    print("uso: ... debug_action.py <file.blend>")
    sys.exit(1)

bpy.ops.wm.open_mainfile(filepath=blend)

rig = bpy.data.objects.get("rig")
print(f"rig: {rig}")

if rig and rig.animation_data and rig.animation_data.action:
    a = rig.animation_data.action
    print(f"action: {a.name}")
    print(f"frame_range: {a.frame_range}")

    # Blender 5.x layered actions
    print(f"slots: {[s.name_display for s in a.slots]}")
    print(f"layers: {len(a.layers)}")

    fc_count = 0
    bone_path_set = set()
    for layer in a.layers:
        print(f"  layer: {layer.name}")
        for strip in layer.strips:
            print(f"    strip: {strip}")
            for slot in a.slots:
                cb = strip.channelbag(slot, ensure=False)
                if cb:
                    print(f"      channelbag for slot {slot.name_display}: fcurves={len(cb.fcurves)}")
                    fc_count += len(cb.fcurves)
                    for fc in cb.fcurves[:5]:
                        print(f"        fc: data_path={fc.data_path} array_index={fc.array_index}")
                    for fc in cb.fcurves:
                        # extrair bone do data_path
                        dp = fc.data_path
                        if dp.startswith('pose.bones["'):
                            bn = dp.split('"')[1]
                            bone_path_set.add(bn)
    print(f"\ntotal fcurves: {fc_count}")
    print(f"bones animados: {sorted(bone_path_set)}")

# Verificar custom property IK_FK switches
print(f"\n=== IK/FK switches ===")
for pb in rig.pose.bones:
    if pb.name.endswith("_parent.L") or pb.name.endswith("_parent.R"):
        # Listar custom props
        for k in pb.keys():
            if "IK" in k or "FK" in k:
                print(f"  {pb.name}.{k} = {pb[k]}")

# Verificar DEF bones e seus constraints
print(f"\n=== DEF bones constraints sample ===")
for name in ["DEF-thigh.L", "DEF-shin.L", "DEF-foot.L"]:
    b = rig.pose.bones.get(name)
    if b:
        print(f"  {b.name}:")
        for c in b.constraints:
            tgt = c.subtarget if hasattr(c, "subtarget") else "?"
            print(f"    {c.type} -> {tgt}")
