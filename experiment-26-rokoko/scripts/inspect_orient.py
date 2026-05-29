"""Orientacao: rotacao do objeto armature, direcao de bones-chave (hips up, spine up, foot forward)."""
import bpy, sys, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
path = argv[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
if path.lower().endswith(".glb"):
    bpy.ops.import_scene.gltf(filepath=path)
else:
    bpy.ops.import_scene.fbx(filepath=path)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
print("ARMATURE", arm.name, "obj_rot_euler(deg)=", tuple(round(__import__('math').degrees(a),1) for a in arm.rotation_euler), "scale=", tuple(round(s,3) for s in arm.scale))
# direcao up de hips/pelvis e spine, e forward do pe
keys = ['hips','pelvis','spine','head','foot','toe','ball','thigh','upleg']
for bn in arm.data.bones:
    n = bn.name.lower()
    if any(n.startswith(k) or k in n for k in ['hips','pelvis']) or n in ('spine1','spine_01','head'):
        v = (bn.tail_local - bn.head_local).normalized()
        # converte pro mundo
        wv = (arm.matrix_world.to_3x3() @ v).normalized()
        print(f"  {bn.name:12} local_dir=({v.x:+.2f},{v.y:+.2f},{v.z:+.2f}) world_dir=({wv.x:+.2f},{wv.y:+.2f},{wv.z:+.2f})")
