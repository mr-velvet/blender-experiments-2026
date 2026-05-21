"""Sonda: o Rigify esta disponivel e funcional em Blender 5.1 headless?

Checa:
- Modulo bl_ext.blender_org.rigify ou addon classico 'rigify' presente
- Operadores principais (object.armature_human_metarig_add, pose.rigify_generate)
- Versao do Rigify
"""
import sys
import bpy
import addon_utils

print("=" * 60)
print("BLENDER VERSION:", bpy.app.version_string)
print("=" * 60)

# 1) Procurar Rigify em todos os addons conhecidos
print("\n[1] Procurando Rigify nos addons...")
for mod in addon_utils.modules():
    name = mod.__name__
    if "rigify" in name.lower():
        info = addon_utils.module_bl_info(mod)
        enabled, loaded = addon_utils.check(name)
        print(f"  encontrado: {name!r} version={info.get('version')} enabled={enabled} loaded={loaded}")

# 2) Tentar habilitar rigify (extension Blender 5.x)
print("\n[2] Tentando habilitar rigify via addon_utils.enable...")
candidates = ["rigify", "bl_ext.blender_org.rigify", "bl_ext.system.rigify"]
enabled_name = None
for name in candidates:
    try:
        addon_utils.enable(name, default_set=True, persistent=True)
        en, lo = addon_utils.check(name)
        print(f"  {name!r} -> enabled={en} loaded={lo}")
        if en and lo:
            enabled_name = name
            break
    except Exception as e:
        print(f"  {name!r} ERRO: {type(e).__name__}: {e}")

# 3) Se nao achou, instalar via extension repo
if not enabled_name:
    print("\n[3] Instalando via bpy.ops.extensions.package_install...")
    try:
        bpy.ops.extensions.repo_sync(repo_index=0)
        result = bpy.ops.extensions.package_install(
            repo_index=0, pkg_id="rigify", enable_on_install=True
        )
        print(f"  install result: {result}")
        for name in candidates:
            en, lo = addon_utils.check(name)
            if en and lo:
                enabled_name = name
                print(f"  habilitado: {name}")
                break
    except Exception as e:
        print(f"  ERRO no install: {type(e).__name__}: {e}")

print(f"\n[RESULT] Rigify enabled como: {enabled_name!r}")

# 4) Testar operadores criticos
print("\n[4] Testando operadores...")
ops_to_check = [
    "object.armature_human_metarig_add",
    "object.armature_basic_human_metarig_add",
    "pose.rigify_generate",
]
for op_path in ops_to_check:
    parts = op_path.split(".")
    op = bpy.ops
    for p in parts:
        op = getattr(op, p, None)
        if op is None:
            break
    if op is None:
        print(f"  {op_path}: NAO ENCONTRADO")
        continue
    try:
        # _poll precisa de contexto adequado, soh checar existencia
        print(f"  {op_path}: OK (existe)")
    except Exception as e:
        print(f"  {op_path}: ERRO {e}")

# 5) Tentar criar um metarig humanoide e ver se rola
print("\n[5] Tentando criar metarig humanoide...")
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.object.armature_human_metarig_add()
    print("  armature_human_metarig_add: OK")
    arm = bpy.context.active_object
    print(f"    -> created: {arm.name} (type={arm.type})")
    print(f"    -> bones: {len(arm.data.bones)}")
    print(f"    -> rigify version: {arm.data.get('rig_id', '?')}")
except Exception as e:
    print(f"  armature_human_metarig_add: ERRO {type(e).__name__}: {e}")
    try:
        bpy.ops.object.armature_basic_human_metarig_add()
        print("  armature_basic_human_metarig_add: OK (fallback)")
    except Exception as e2:
        print(f"  armature_basic_human_metarig_add: ERRO {type(e2).__name__}: {e2}")

# 6) Tentar gerar o rig
print("\n[6] Tentando gerar rig real (pose.rigify_generate)...")
arm = bpy.context.active_object
if arm and arm.type == "ARMATURE":
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.pose.rigify_generate()
        print("  pose.rigify_generate: OK")
        rig = bpy.context.active_object
        print(f"    -> rig: {rig.name} bones={len(rig.data.bones)}")
    except Exception as e:
        print(f"  pose.rigify_generate: ERRO {type(e).__name__}: {e}")

print("\n[DONE]")
