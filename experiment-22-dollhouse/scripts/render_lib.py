"""render_lib.py — camera/luz/material/render reaproveitavel pro exp22."""
import bpy
import math
import os
from mathutils import Vector


def world_bbox(objects):
    """Bounding box em coords de mundo de uma lista de objetos mesh."""
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    found = False
    for o in objects:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            wc = o.matrix_world @ Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], wc[i])
                maxs[i] = max(maxs[i], wc[i])
            found = True
    if not found:
        return Vector((0, 0, 0)), Vector((1, 1, 1))
    return mins, maxs


def add_sun(energy=3.0, angle_deg=(50, 0, 35)):
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_data.energy = energy
    light = bpy.data.objects.new("Sun", light_data)
    bpy.context.scene.collection.objects.link(light)
    light.rotation_euler = tuple(math.radians(a) for a in angle_deg)
    return light


def add_area_fill(location, size=6.0, energy=200.0, name="Fill"):
    """Luz de area pra iluminar dentro dos comodos abertos (o corte dollhouse)."""
    ld = bpy.data.lights.new(name, type='AREA')
    ld.energy = energy
    ld.size = size
    obj = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj


def setup_world(strength=0.6, color=(0.85, 0.88, 0.95)):
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*color, 1.0)
        bg.inputs[1].default_value = strength


def look_at(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def add_camera(location, target, lens=40, ortho=False, ortho_scale=10):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    if ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    look_at(cam, target)
    bpy.context.scene.camera = cam
    return cam


def apply_neutral_material(objects, color=(0.8, 0.78, 0.74), name="Neutral"):
    """Material Principled neutro pros objetos sem material (estrutura)."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.85
    for o in objects:
        if o.type != 'MESH':
            continue
        if len(o.data.materials) == 0:
            o.data.materials.append(mat)


def render(filepath, engine='CYCLES', samples=64, res=(1280, 960), transparent=False):
    scene = bpy.context.scene
    scene.render.engine = engine
    if engine == 'CYCLES':
        scene.cycles.samples = samples
        try:
            scene.cycles.device = 'GPU'
        except Exception:
            pass
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = filepath
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return filepath
