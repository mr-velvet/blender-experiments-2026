"""Renderiza stills do GLB-fonte do Rokoko PURO (sem retarget) pra validar o movimento."""
import bpy, sys, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUTDIR = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = arm.animation_data.action
sc.frame_start, sc.frame_end = int(act.frame_range[0]), int(act.frame_range[1])

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
# material limpo
mat = bpy.data.materials.new("M"); mat.use_nodes = True
mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.8, 0.62, 0.5, 1)
for m in meshes:
    m.data.materials.clear(); m.data.materials.append(mat)

# centro
c = mathutils.Vector((0, 0, 0)); n = 0; zmin = 1e9
for m in meshes:
    for v in m.bound_box:
        w = m.matrix_world @ mathutils.Vector(v); c += w; n += 1; zmin = min(zmin, w.z)
c /= n

bpy.ops.mesh.primitive_plane_add(size=20, location=(c.x, c.y, zmin))

cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam)
cam.location = (c.x + 3.2, c.y - 3.8, c.z + 0.6)
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam

for nm, loc, e in [("K", (c.x+3, c.y-3, c.z+4), 5000), ("F", (c.x-4, c.y-1, c.z+2), 2500)]:
    ld = bpy.data.lights.new(nm, 'AREA'); ld.energy = e; ld.size = 5
    o = bpy.data.objects.new(nm, ld); o.location = loc
    o.rotation_euler = (c - o.location).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(o)

if sc.world is None: sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 1.0
sc.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.3, 0.34, 0.4, 1)

sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'JPEG'
for f in [1, 24, 42, 60, 72]:
    sc.frame_set(f); sc.render.filepath = f"{OUTDIR}/src_{f:03d}.jpg"
    bpy.ops.render.render(write_still=True); print("[src] frame", f)
