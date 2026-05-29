"""Renderiza 4 stills da cena ja montada (reaproveita 02_render para montar) em frames-chave."""
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
OUT_DIR = argv[0]
frames = [1, 24, 42, 60, 72]
sc = bpy.context.scene
sc.render.image_settings.file_format = 'JPEG'
for f in frames:
    sc.frame_set(f)
    sc.render.filepath = f"{OUT_DIR}/still_{f:03d}.jpg"
    bpy.ops.render.render(write_still=True)
    print("[stills] frame", f)
