"""lista cada movel colocado: pivot, posicao mundo e bbox real (vertices)."""
import bpy, os, json
from mathutils import Vector
OUT_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","out"))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR,"dollhouse_furnished.blend"))
deps=bpy.context.evaluated_depsgraph_get()

def vbbox(children):
    xs,ys,zs=[],[],[]
    for o in children:
        if o.type!='MESH': continue
        oe=o.evaluated_get(deps)
        try: me=oe.to_mesh()
        except Exception: continue
        mw=oe.matrix_world
        for v in me.vertices:
            w=mw@v.co; xs.append(w.x);ys.append(w.y);zs.append(w.z)
        oe.to_mesh_clear()
    if not xs: return None
    return (min(xs),min(ys),min(zs),max(xs),max(ys),max(zs))

pivots=[o for o in bpy.context.scene.objects if o.name.startswith("piv_")]
for p in sorted(pivots, key=lambda o:o.name):
    kids=[c for c in p.children_recursive]
    bb=vbbox(kids)
    if bb:
        sx,sy,sz=bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2]
        cx,cy,cz=(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,(bb[2]+bb[5])/2
        print(f"[insp] {p.name:32s} c=({cx:.1f},{cy:.1f},{cz:.1f}) size=({sx:.2f},{sy:.2f},{sz:.2f})", flush=True)
print("[insp] DONE", flush=True)
