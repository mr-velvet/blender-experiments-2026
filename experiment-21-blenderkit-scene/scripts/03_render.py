"""
03_render.py — abre o .blend com a scene appendada e renderiza um still
pela camera do proprio asset, pra validar visualmente que subiu certo.

Roda via:
  blender --background <blend> --python 03_render.py -- <out_png> <engine> <samples> <res>
"""
import bpy
import sys
import os

argv = sys.argv
argv = argv[argv.index("--") + 1:]
out_png = argv[0]
engine = argv[1] if len(argv) > 1 else "BLENDER_EEVEE_NEXT"
samples = int(argv[2]) if len(argv) > 2 else 64
res = int(argv[3]) if len(argv) > 3 else 1280


def log(*a):
    print("[render]", *a, flush=True)


# escolhe a scene do asset (nao a "Scene" vazia padrao)
target = None
for s in bpy.data.scenes:
    if s.name == "The Lonely Outpost":
        target = s
        break
if target is None:
    # fallback: a primeira com camera
    for s in bpy.data.scenes:
        if s.camera:
            target = s
            break
if target is None:
    target = bpy.context.scene

bpy.context.window.scene = target
sc = target
log("scene:", sc.name, "| objects:", len(sc.objects), "| camera:", sc.camera.name if sc.camera else "NONE")

# engine
try:
    sc.render.engine = engine
except Exception as e:
    log("engine set failed, fallback EEVEE:", e)
    sc.render.engine = "BLENDER_EEVEE_NEXT"
log("engine:", sc.render.engine)

if sc.render.engine == "CYCLES":
    sc.cycles.samples = samples
    # usa GPU se disponivel
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.get_devices()
        for dtype in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                prefs.compute_device_type = dtype
                break
            except Exception:
                continue
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
        log("cycles device:", sc.cycles.device, "| type:", prefs.compute_device_type)
    except Exception as e:
        log("GPU setup skipped:", e)
else:
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass

# resolucao
sc.render.resolution_x = res
sc.render.resolution_y = int(res * 9 / 16)
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = out_png

if not sc.camera:
    log("WARNING: no camera, render will fail")

log(f"rendering {res}x{sc.render.resolution_y} {sc.render.engine} samples={samples} -> {out_png}")
bpy.ops.render.render(write_still=True)
log("rendered. exists:", os.path.exists(out_png),
    "size:", os.path.getsize(out_png) if os.path.exists(out_png) else 0)
log("DONE")
