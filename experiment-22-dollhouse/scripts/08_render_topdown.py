"""08_render_topdown.py — planta baixa (top ortho) de um andar pra ver posicoes XY.
  blender --background --python 08_render_topdown.py -- <floor_idx>
"""
import bpy, sys, os, json, math
sys.path.append(os.path.dirname(__file__))
import render_lib as rl

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "out"))
argv=sys.argv; argv=argv[argv.index("--")+1:]; fi=int(argv[0])
meta=json.load(open(os.path.join(OUT_DIR,"rooms.json"),encoding="utf-8"))
W,D=meta["W"],meta["D"]; pitch=meta["floor_pitch"]; ceil=meta["ceil_h"]; z0=fi*pitch

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR,"dollhouse_furnished.blend"))
# esconde objetos de outros andares pra nao aparecerem na vista de cima
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        zc=(o.matrix_world.translation.z)
        # nao escondemos por seguranca; ortho clip cuida
structural=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.materials)==0]
rl.apply_neutral_material(structural)
rl.setup_world(strength=1.0); rl.add_sun(energy=2)
cam=rl.add_camera(location=(W/2, D/2, z0+ceil-0.05), target=(W/2,D/2,z0),
                  ortho=True, ortho_scale=max(W,D)+0.5)
# clip pra so ver esse andar
cam.data.clip_start=0.02; cam.data.clip_end=ceil-0.1
out=os.path.join(OUT_DIR,"preview",f"top_{fi}.png")
rl.render(out, engine='BLENDER_EEVEE', samples=16, res=(900, int(900*D/W)))
print("[top]", fi, out, flush=True)
