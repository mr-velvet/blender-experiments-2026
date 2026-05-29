"""
Pipeline de retarget headless: mocap Rokoko (GLB) -> personagem Quaternius (FBX).
Usa o plugin oficial Rokoko Studio Live (operadores rsl.*), 100% Python, sem GUI.

Uso:
  blender --background --python 01_retarget.py -- <source.glb> <target.fbx> <out.blend> <addon_module>
"""
import bpy, sys, addon_utils

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, OUT_BLEND, ADDON = argv[0], argv[1], argv[2], argv[3]
USE_POSE = argv[4] if len(argv) > 4 else 'REST'  # REST ou CURRENT


def log(*a):
    print("[retarget]", *a)


# -------------------------------------------------- 1. cena limpa + addon
bpy.ops.wm.read_factory_settings(use_empty=True)
log("habilitando addon", ADDON)
addon_utils.enable(ADDON, default_set=True, persistent=True)

# o plugin carrega as listas de deteccao no register; garante carregadas
from importlib import import_module
mod = import_module(ADDON)
try:
    mod.core.detection_manager.load_detection_lists()
    log("listas de deteccao de bones carregadas")
except Exception as e:
    log("aviso load_detection_lists:", e)

# -------------------------------------------------- 2. importa SOURCE (mocap Rokoko)
log("importando source GLB:", SRC_GLB)
bpy.ops.import_scene.gltf(filepath=SRC_GLB)
source = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
source.name = "SOURCE_Rokoko"
log("source armature:", source.name, "bones:", len(source.data.bones),
    "action:", source.animation_data.action.name if source.animation_data else None)

# -------------------------------------------------- 3. importa TARGET (Quaternius)
log("importando target FBX:", TGT_FBX)
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=TGT_FBX)
new = [o for o in bpy.context.scene.objects if o not in before]
target = next(o for o in new if o.type == 'ARMATURE')
target.name = "TARGET_Quaternius"
log("target armature:", target.name, "bones:", len(target.data.bones),
    "rot_euler_deg:", tuple(round(__import__('math').degrees(a), 1) for a in target.rotation_euler))

# normaliza orientacao do alvo: aplica rotacao/escala do objeto (zera o facing 180deg)
bpy.ops.object.select_all(action='DESELECT')
target.select_set(True)
bpy.context.view_layer.objects.active = target
for m in [o for o in bpy.data.objects if o.type == 'MESH' and o.parent == target]:
    m.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
log("target rot aplicada ->", tuple(round(__import__('math').degrees(a), 1) for a in target.rotation_euler))

# -------------------------------------------------- 4. seta props do plugin
sc = bpy.context.scene
sc.rsl_retargeting_armature_source = source
sc.rsl_retargeting_armature_target = target
sc.rsl_retargeting_auto_scaling = True
sc.rsl_retargeting_use_pose = USE_POSE
log("use_pose =", USE_POSE)

# -------------------------------------------------- 5. build bone list (auto-detect)
log("rodando rsl.build_bone_list (auto-detect)")
bpy.ops.rsl.build_bone_list()

mapped = []
unmapped_src = []
for it in sc.rsl_retargeting_bone_list:
    if it.bone_name_source and it.bone_name_target:
        mapped.append((it.bone_name_source, it.bone_name_target))
    elif it.bone_name_source:
        unmapped_src.append(it.bone_name_source)

log(f"auto-detect: {len(mapped)} pares mapeados, {len(unmapped_src)} source sem alvo")
for s, t in mapped:
    print(f"    {s:24} -> {t}")
if unmapped_src:
    print("  SOURCE sem alvo:", ", ".join(unmapped_src))

# -------------------------------------------------- 6. retarget
log("rodando rsl.retarget_animation")
res = bpy.ops.rsl.retarget_animation()
log("retarget resultado:", res)

# -------------------------------------------------- 7. valida que o target ganhou animacao
tgt_act = target.animation_data.action if target.animation_data else None
if tgt_act:
    fr = tgt_act.frame_range
    nb = len({fc.data_path.split('"')[1] for fc in tgt_act.fcurves if 'pose.bones[' in fc.data_path})
    log(f"OK target animado: action={tgt_act.name!r} range={fr[0]:.0f}..{fr[1]:.0f} "
        f"fcurves={len(tgt_act.fcurves)} bones={nb}")
else:
    log("FALHA: target sem animacao apos retarget")

# -------------------------------------------------- 8. salva
sc.frame_start = int(source.animation_data.action.frame_range[0])
sc.frame_end = int(source.animation_data.action.frame_range[1])
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log("salvo:", OUT_BLEND)
