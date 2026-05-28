"""Instala o Home Builder 5 via extensions.blender.org (headless).

Padrao reaproveitado dos experimentos anteriores (archimesh, cell_fracture, rigify):
package_install do repo blender_org + enable. Depois verifica que o modulo
bl_ext.blender_org.home_builder_5 importa e que hb_types existe.
"""
import bpy
import addon_utils
import importlib

PKG_ID = "home_builder_5"
MODULE = f"bl_ext.blender_org.{PKG_ID}"


def main():
    # Garante repo de extensions sincronizado
    try:
        bpy.ops.extensions.repo_sync_all()
    except Exception as e:
        print(f"[sync] aviso: {e}")

    # Acha o repo blender_org
    prefs = bpy.context.preferences
    repo_index = None
    for i, repo in enumerate(prefs.extensions.repos):
        print(f"[repo {i}] {repo.module} enabled={repo.enabled}")
        if repo.module == "blender_org":
            repo_index = i
    if repo_index is None:
        repo_index = 0
    print(f"[install] usando repo_index={repo_index}")

    try:
        bpy.ops.extensions.package_install(
            repo_index=repo_index,
            pkg_id=PKG_ID,
            enable_on_install=True,
        )
        print("[install] package_install OK")
    except Exception as e:
        print(f"[install] erro package_install: {e}")

    # Garante enable
    try:
        addon_utils.enable(MODULE, default_set=True, persistent=True)
    except Exception as e:
        print(f"[enable] erro: {e}")

    state = addon_utils.check(MODULE)
    print(f"[check] {MODULE} -> {state}")

    # Importa modulo e confere hb_types
    try:
        mod = importlib.import_module(MODULE)
        print(f"[import] {MODULE} OK -> {mod.__file__}")
        hb_types = importlib.import_module(f"{MODULE}.hb_types")
        print(f"[import] hb_types OK -> {hb_types.__file__}")
        names = [n for n in dir(hb_types) if not n.startswith("_")]
        print(f"[hb_types] simbolos: {names}")
    except Exception as e:
        import traceback
        print(f"[import] erro: {e}")
        traceback.print_exc()

    # Salva prefs pra persistir o enable nas proximas sessoes headless
    try:
        bpy.ops.wm.save_userpref()
        print("[prefs] salvas")
    except Exception as e:
        print(f"[prefs] aviso: {e}")


if __name__ == "__main__":
    main()
