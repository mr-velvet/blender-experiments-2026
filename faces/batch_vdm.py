"""Batch 4c: matriz forma x EXR x material Clay Doh."""
import subprocess
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
SCRIPT = HERE / "vdm_stamp.py"
SRC_BLEND_CLAY = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"
EXR_DIR = Path(r"C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Texture")

# (shape, default params adequados por forma)
# Foco: formas com poucas faces grandes onde "rosto no centro de cada face" faz sentido visual
SHAPES = [
    ("cube",      {"stamp_scale": 0.7,  "displace_strength": 0.35, "subdiv_levels": 5}),
    ("icosphere", {"stamp_scale": 0.7,  "displace_strength": 0.35, "subdiv_levels": 4}),  # 20 faces
    ("cylinder",  {"stamp_scale": 0.7,  "displace_strength": 0.3,  "subdiv_levels": 5}),
]

MATERIALS = [
    {"name": "Clay Doh",     "slug": "claydoh",     "label": "Clay Doh (roxo)"},
    {"name": "Bubble Gum",   "slug": "bubblegum",   "label": "Bubble Gum"},
    {"name": "Porcelain",    "slug": "porcelain",   "label": "Porcelain"},
    {"name": "Terracotta",   "slug": "terracotta",  "label": "Terracotta"},
]

# Selecao curada de EXRs (cobre variedade)
EXR_PICKS = [1, 5, 10, 15, 20, 25]

OUT = HERE / "out"
GLB_DIR = OUT / "glb"
RENDER_DIR = OUT / "renders"
TEX_DIR = OUT / "baked_textures"


def run_combo(shape_info, exr_num, mat):
    shape, params = shape_info
    exr_path = EXR_DIR / f"Map_ ({exr_num}).exr"
    combo_id = f"{shape}_map{exr_num:02d}_{mat['slug']}"
    glb = GLB_DIR / f"{combo_id}.glb"
    render = RENDER_DIR / f"{combo_id}.png"

    if glb.exists() and render.exists():
        print(f"SKIP (cached): {combo_id}")
        return {
            "shape": shape, "material": mat["label"], "exr": f"Map_{exr_num}",
            "combo_id": combo_id,
            "glb": glb.relative_to(HERE).as_posix(),
            "render": render.relative_to(HERE).as_posix(),
            "status": "cached",
        }

    cmd = [
        BLENDER, "--background", "--factory-startup",
        "--python", str(SCRIPT), "--",
        "--shape", shape,
        "--exr", str(exr_path),
        "--material", mat["name"],
        "--src-blend", SRC_BLEND_CLAY,
        "--out-glb", str(glb),
        "--out-render", str(render),
        "--tex-dir", str(TEX_DIR),
        "--combo-id", combo_id,
        "--bake-res", "1024",
        "--subdiv-levels", str(params["subdiv_levels"]),
        "--stamp-scale", str(params["stamp_scale"]),
        "--displace-strength", str(params["displace_strength"]),
    ]
    print(f"RUN: {combo_id}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    ok = (r.returncode == 0 and glb.exists())
    if not ok:
        print(f"  FAIL rc={r.returncode}")
        print("  STDERR:", r.stderr[-600:])
    else:
        print(f"  OK  glb={glb.stat().st_size//1024}KB")
    return {
        "shape": shape, "material": mat["label"], "exr": f"Map_{exr_num}",
        "combo_id": combo_id,
        "glb": glb.relative_to(HERE).as_posix() if ok else None,
        "render": render.relative_to(HERE).as_posix() if ok else None,
        "status": "ok" if ok else "fail",
    }


def main():
    GLB_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    TEX_DIR.mkdir(parents=True, exist_ok=True)

    # Pra cada forma: roda matrix curada (forma x 3 EXRs x 2 materiais = 6 por forma, 30 total)
    # Mas vou limitar mais ainda: 1 EXR x 2 materiais por forma = 10 base + extras
    # Decisao: cada forma com 2 EXRs diferentes em 2 materiais = 4 por forma = 20 combos
    manifest = []
    selected_exrs = EXR_PICKS[:3]  # 3 EXRs diferentes
    selected_mats = MATERIALS  # 4 mats
    # 5 formas x 3 exrs x 4 mats = 60 combos. Reduzir: pra cada forma, pega
    # apenas alguns combos diversos
    plan = []
    for i, shape_info in enumerate(SHAPES):
        for j, exr_num in enumerate(selected_exrs):
            # 1 material por combinacao forma+exr (rotaciona)
            mat = selected_mats[(i + j) % len(selected_mats)]
            plan.append((shape_info, exr_num, mat))
    print(f"Plano: {len(plan)} combos")
    for shape_info, exr_num, mat in plan:
        manifest.append(run_combo(shape_info, exr_num, mat))

    out_manifest = OUT / "manifest.json"
    with open(out_manifest, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nMANIFEST: {out_manifest}")
    ok = sum(1 for m in manifest if m["status"] in ("ok", "cached"))
    print(f"DONE: {ok}/{len(manifest)} combos OK")


if __name__ == "__main__":
    main()
