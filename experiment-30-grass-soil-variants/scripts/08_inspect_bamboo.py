# -*- coding: utf-8 -*-
"""inspeciona os meshes do bambu pra identificar o vaso (baixo+largo) vs bambu (alto).
blender --background --python 08_inspect_bamboo.py -- <bamboo_blend>"""
import bpy, sys, mathutils
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
B=argv[0]
bpy.ops.wm.read_homefile(use_empty=True)
sc=bpy.context.scene
with bpy.data.libraries.load(B, link=False) as (src,dst):
    dst.objects=list(src.objects)
app=[o for o in dst.objects if o is not None]
for o in app:
    try: sc.collection.objects.link(o)
    except Exception: pass
def wbb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return ([min(c[i] for c in cs) for i in range(3)],[max(c[i] for c in cs) for i in range(3)])
for o in app:
    if o.type!='MESH':
        print("NON-MESH",o.name,o.type); continue
    a,b=wbb(o)
    h=b[2]-a[2]; w=max(b[0]-a[0],b[1]-a[1])
    z0=a[2]
    print("MESH name=%-22s h=%.2f w=%.2f z0=%.2f verts=%d ratio_h/w=%.2f"%(
        o.name[:22],h,w,z0,len(o.data.vertices), h/w if w>0 else 0))
print("INSPECT_DONE")
