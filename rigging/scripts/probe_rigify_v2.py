"""Sonda v2: importar rigify direto e procurar a funcao add_metarig"""
import bpy
import addon_utils
import importlib

addon_utils.enable("rigify", default_set=True, persistent=True)

import rigify
print(f"rigify module: {rigify}")
print(f"rigify dir: {[x for x in dir(rigify) if not x.startswith('_')]}")

# Submodules?
import pkgutil, os
rig_path = os.path.dirname(rigify.__file__)
print(f"\nrigify path: {rig_path}")
print("rigify submodules:")
for finder, name, ispkg in pkgutil.iter_modules(rigify.__path__):
    print(f"  {'P' if ispkg else 'M'} {name}")

# Procurar metarig humanoide
try:
    from rigify import metarigs
    print(f"\nmetarigs submodules:")
    for finder, name, ispkg in pkgutil.iter_modules(metarigs.__path__):
        print(f"  {'P' if ispkg else 'M'} {name}")
except ImportError as e:
    print(f"erro importing metarigs: {e}")

# Tentar achar human metarig
try:
    from rigify.metarigs.Basic import basic_human
    print(f"\nbasic_human: {basic_human}")
    print(f"dir: {[x for x in dir(basic_human) if not x.startswith('_')]}")
except Exception as e:
    print(f"basic_human ERR: {e}")

try:
    from rigify.metarigs.Human import human as human_mod
    print(f"\nhuman: {human_mod}")
    print(f"dir: {[x for x in dir(human_mod) if not x.startswith('_')]}")
except Exception as e:
    print(f"human ERR: {e}")

# Inspecionar funcoes em basic_human
try:
    from rigify.metarigs import Basic
    print(f"\nBasic dir: {[x for x in dir(Basic) if not x.startswith('_')]}")
    print(f"Basic path: {Basic.__path__}")
    for finder, name, ispkg in pkgutil.iter_modules(Basic.__path__):
        print(f"  Basic/{name}")
except Exception as e:
    print(f"Basic ERR: {e}")

print("\n[DONE]")
