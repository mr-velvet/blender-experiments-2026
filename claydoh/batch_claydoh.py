"""Batch Clay Doh: forma x material, 1 combo por processo do Blender.

Output em claydoh/out/{glb,renders,baked_textures}/, manifest em claydoh/out/manifest.json.
"""
import subprocess
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
SCRIPT = ROOT / "pipeline" / "bake_and_export.py"
SRC_BLEND = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"

SHAPES = ["sphere", "cylinder", "torus", "suzanne"]

# Selecao curada: variedade de looks (procedural classico, image-based, especiais).
MATERIALS = [
    {"name": "Clay Doh",        "slug": "claydoh",       "label": "Clay Doh (base)"},
    {"name": "Bubble Gum",      "slug": "bubblegum",     "label": "Bubble Gum"},
    {"name": "Porcelain",       "slug": "porcelain",     "label": "Porcelain"},
    {"name": "Crackle",         "slug": "crackle",       "label": "Crackle"},
    {"name": "Glitter Clay",    "slug": "glitter",       "label": "Glitter Clay"},
    {"name": "Plasticine",      "slug": "plasticine",    "label": "Plasticine (img)"},
    {"name": "Pottery Clay",    "slug": "pottery",       "label": "Pottery Clay (img)"},
    {"name": "Terracotta",      "slug": "terracotta",    "label": "Terracotta (img)"},
]

OUT = HERE / "out"
GLB_DIR = OUT / "glb"
RENDER_DIR = OUT / "renders"
TEX_DIR = OUT / "baked_textures"


def run_combo(shape, mat):
    combo_id = f"{shape}_{mat['slug']}"
    glb = GLB_DIR / f"{combo_id}.glb"
    render = RENDER_DIR / f"{combo_id}.png"

    if glb.exists() and render.exists():
        print(f"SKIP (cached): {combo_id}")
        return {
            "shape": shape, "material": mat["label"], "combo_id": combo_id,
            "glb": glb.relative_to(HERE).as_posix(),
            "render": render.relative_to(HERE).as_posix(),
            "status": "cached",
        }

    cmd = [
        BLENDER, "--background", "--factory-startup",
        "--python", str(SCRIPT), "--",
        "--shape", shape,
        "--material", mat["name"],
        "--src-blend", SRC_BLEND,
        "--out-glb", str(glb),
        "--out-render", str(render),
        "--tex-dir", str(TEX_DIR),
        "--combo-id", combo_id,
        "--bake-res", "1024",
    ]
    print(f"RUN: {combo_id}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    ok = (r.returncode == 0 and glb.exists())
    if not ok:
        print(f"  FAIL rc={r.returncode}")
        print("  STDERR:", r.stderr[-600:])
        print("  STDOUT:", r.stdout[-600:])
    else:
        size_kb = glb.stat().st_size // 1024
        print(f"  OK  glb={size_kb}KB")
    return {
        "shape": shape, "material": mat["label"], "combo_id": combo_id,
        "glb": glb.relative_to(HERE).as_posix() if ok else None,
        "render": render.relative_to(HERE).as_posix() if ok else None,
        "status": "ok" if ok else "fail",
    }


def main():
    only_shape = None
    only_mat = None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--shape":
            only_shape = sys.argv[i + 2]
        if a == "--material":
            only_mat = sys.argv[i + 2]

    GLB_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    TEX_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    for shape in SHAPES:
        if only_shape and shape != only_shape:
            continue
        for mat in MATERIALS:
            if only_mat and mat["slug"] != only_mat:
                continue
            manifest.append(run_combo(shape, mat))

    out_manifest = OUT / "manifest.json"
    with open(out_manifest, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nMANIFEST: {out_manifest}")
    ok = sum(1 for m in manifest if m["status"] in ("ok", "cached"))
    print(f"DONE: {ok}/{len(manifest)} combos OK")


if __name__ == "__main__":
    main()
