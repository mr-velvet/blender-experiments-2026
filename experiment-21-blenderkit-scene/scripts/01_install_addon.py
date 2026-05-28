"""
01_install_addon.py — instala o addon BlenderKit v3.19.2 num Blender headless,
habilita, seta a api_key nas preferences e salva as prefs.

Roda via: blender --background --python 01_install_addon.py -- <zip_path> <api_key>

BlenderKit v3.x e addon "legacy" (tem bl_info), entao usa addon_install/addon_enable
e NAO o sistema de extensions. Depois do enable, o modulo fica em
bpy.context.preferences.addons['blenderkit'].preferences.
"""
import bpy
import sys
import os
import addon_utils

argv = sys.argv
argv = argv[argv.index("--") + 1:]
zip_path = argv[0]
api_key = argv[1]

print(f"[install] zip={zip_path}")
print(f"[install] api_key=***{api_key[-4:]}")

# instala o addon a partir do zip
bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
print("[install] addon_install OK")

# habilita
bpy.ops.preferences.addon_enable(module="blenderkit")
print("[install] addon_enable OK")

# confirma registro
loaded_default, loaded_state = addon_utils.check("blenderkit")
print(f"[install] addon_utils.check -> default={loaded_default} state={loaded_state}")

prefs = bpy.context.preferences.addons["blenderkit"].preferences
print(f"[install] prefs class = {type(prefs).__name__}")

# seta a api_key e marca como logado manualmente
prefs.api_key = api_key
# em algumas versoes ha api_key_refresh / login_attempt; setar o minimo
if hasattr(prefs, "enable_oauth"):
    print(f"[install] enable_oauth field exists = {prefs.enable_oauth}")
print(f"[install] api_key set -> ***{prefs.api_key[-4:]}")
print(f"[install] global_dir = {prefs.global_dir}")

# salva as preferences do usuario pra persistir entre execucoes headless
bpy.ops.wm.save_userpref()
print("[install] save_userpref OK")
print("[install] DONE")
