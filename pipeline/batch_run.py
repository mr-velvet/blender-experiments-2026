"""Roda bake_and_export.py para cada combo (forma x material).

Cada combo eh uma invocacao separada do Blender pra isolar estado.
Gera manifest.json no fim com lista de outputs.
"""
import subprocess
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
SCRIPT = ROOT / "pipeline" / "bake_and_export.py"

SHAPES = ["cube", "sphere", "cylinder", "torus", "suzanne"]

MATERIALS = [
    {
        "name": "Cardboard Outer",
        "src": r"C:\Users\manu\Downloads\BLENDER-CARDBOARD\Cardboard Shader 1.2 (Blender 3.4+).blend",
        "slug": "cardboard-outer",
        "label": "Cardboard Outer",
    },
    {
        "name": "Cardboard Inner",
        "src": r"C:\Users\manu\Downloads\BLENDER-CARDBOARD\Cardboard Shader 1.2 (Blender 3.4+).blend",
        "slug": "cardboard-inner",
        "label": "Cardboard Inner",
    },
    {
        "name": "Mat1",
        "src": r"C:\Users\manu\Downloads\BLENDER-CARDBOARD\Cardboard Shader 1.2 (Blender 3.4+).blend",
        "slug": "mat1",
        "label": "Mat1 (text)",
    },
    {
        "name": "Mat2",
        "src": r"C:\Users\manu\Downloads\BLENDER-CARDBOARD\Cardboard Shader 1.2 (Blender 3.4+).blend",
        "slug": "mat2",
        "label": "Mat2 (text)",
    },
]


def run_combo(shape, mat):
    combo_id = f"{shape}_{mat['slug']}"
    glb = ROOT / "out" / "glb" / f"{combo_id}.glb"
    render = ROOT / "out" / "renders" / f"{combo_id}.png"
    tex_dir = ROOT / "out" / "baked_textures"

    if glb.exists() and render.exists():
        print(f"SKIP (cached): {combo_id}")
        return {"shape": shape, "material": mat["label"], "combo_id": combo_id,
                "glb": str(glb), "render": str(render), "status": "cached"}

    cmd = [
        BLENDER, "--background", "--python", str(SCRIPT), "--",
        "--shape", shape,
        "--material", mat["name"],
        "--src-blend", mat["src"],
        "--out-glb", str(glb),
        "--out-render", str(render),
        "--tex-dir", str(tex_dir),
        "--combo-id", combo_id,
        "--bake-res", "1024",
    ]
    print(f"RUN: {combo_id}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    ok = (r.returncode == 0 and glb.exists())
    if not ok:
        print(f"  FAIL rc={r.returncode}")
        print("  STDERR:", r.stderr[-500:])
        print("  STDOUT:", r.stdout[-500:])
    else:
        print(f"  OK  glb={glb.stat().st_size//1024}KB")
    return {
        "shape": shape, "material": mat["label"], "combo_id": combo_id,
        "glb": glb.relative_to(ROOT).as_posix(),
        "render": render.relative_to(ROOT).as_posix(),
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

    manifest = []
    for shape in SHAPES:
        if only_shape and shape != only_shape:
            continue
        for mat in MATERIALS:
            if only_mat and mat["slug"] != only_mat:
                continue
            manifest.append(run_combo(shape, mat))

    out_manifest = ROOT / "out" / "manifest.json"
    with open(out_manifest, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nMANIFEST: {out_manifest}")
    ok = sum(1 for m in manifest if m["status"] in ("ok", "cached"))
    print(f"DONE: {ok}/{len(manifest)} combos OK")


if __name__ == "__main__":
    main()
