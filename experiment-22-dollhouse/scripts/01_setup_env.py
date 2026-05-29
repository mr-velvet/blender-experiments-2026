"""
01_setup_env.py — prepara o ambiente headless do exp22 com OS DOIS addons no
mesmo BLENDER_USER_RESOURCES:

  - BlenderKit (legacy addon, ja copiado em bl_config/scripts/addons/blenderkit) -> habilita + api_key
  - Home Builder 5 (extension de extensions.blender.org) -> instala + habilita

Roda via:
  blender --background --python 01_setup_env.py -- <api_key>

Reaproveita os padroes validados nos exp18 (HB via package_install) e exp21 (BlenderKit legacy).
"""
import bpy
import sys
import addon_utils

argv = sys.argv
argv = argv[argv.index("--") + 1:]
api_key = argv[0]


def log(*a):
    print("[setup]", *a, flush=True)


# ---------------------------------------------------------------------------
# 1. BlenderKit (legacy addon ja presente em scripts/addons/blenderkit)
# ---------------------------------------------------------------------------
try:
    bpy.ops.preferences.addon_enable(module="blenderkit")
    log("blenderkit addon_enable OK")
except Exception as e:
    log("blenderkit enable raised:", e)

bk_default, bk_state = addon_utils.check("blenderkit")
log(f"blenderkit check default={bk_default} state={bk_state}")

prefs = bpy.context.preferences.addons["blenderkit"].preferences
prefs.api_key = api_key
log("blenderkit api_key set ***" + api_key[-4:])
log("blenderkit global_dir:", prefs.global_dir)

# habilita online access (necessario pro daemon do BlenderKit baixar depois)
try:
    bpy.context.preferences.system.use_online_access = True
    log("use_online_access = True")
except Exception as e:
    log("use_online_access raised:", e)

# ---------------------------------------------------------------------------
# 2. Home Builder 5 (extension ja copiada em bl_config/extensions/blender_org)
# ---------------------------------------------------------------------------
HB = "home_builder_5"
HB_MOD = f"bl_ext.blender_org.{HB}"

# habilita
try:
    bpy.ops.preferences.addon_enable(module=HB_MOD)
    log("home_builder_5 addon_enable OK")
except Exception as e:
    log("home_builder_5 enable raised:", e)

# confirma import das classes internas que vamos dirigir
try:
    import importlib
    hb_types = importlib.import_module(f"{HB_MOD}.hb_types")
    log("hb_types import OK ->", [n for n in dir(hb_types) if "Wall" in n or "Cage" in n])
except Exception as e:
    log("hb_types import FAIL:", e)

# ---------------------------------------------------------------------------
# 3. salva userpref pra persistir os dois addons habilitados
# ---------------------------------------------------------------------------
bpy.ops.wm.save_userpref()
log("save_userpref OK")
log("DONE")
