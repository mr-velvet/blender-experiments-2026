"""Pipeline completa autonoma de rigging + animacao:

1. Cria um humanoide stylized do zero (mesh juntando cilindros e esferas)
2. Adiciona metarig Rigify humano (basic_human)
3. Posiciona metarig sobre o mesh
4. Faz parent com automatic weights
5. Anima bones com walk cycle procedural (pernas + bracos)
6. Exporta GLB com armature + skin + animation

Workaround critico Blender 5.1: os ops bpy.ops.object.armature_human_metarig_add
e bpy.ops.pose.rigify_generate nao registram em headless. Solucao:
- Chamar rigify.metarigs.Basic.basic_human.create() direto pro metarig
- Chamar rigify.generate.generate_rig() direto pro generate
"""
import math
import sys
from pathlib import Path

import bpy
import bmesh
import addon_utils
from mathutils import Vector, Matrix, Quaternion

OUT_DIR = Path(__file__).resolve().parent.parent / "out" / "glb"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# UTIL
# ============================================================

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    # Set render engine to ensure consistent baking environment
    bpy.context.scene.render.fps = 30


def add_uv_sphere(name, location, radius=1.0, segments=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=segments, ring_count=rings, location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def add_cylinder(name, location, radius=1.0, depth=2.0, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, vertices=vertices,
        location=location, rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def add_cube_box(name, location, size=1.0):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def join_objects(objs, target_name):
    """Une todos objs num so. Retorna o mesh resultante."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    target = objs[0]
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()
    target.name = target_name
    return target


# ============================================================
# 1) MESH HUMANOIDE STYLIZED
# ============================================================

def build_humanoid_mesh():
    """
    Cria humanoide simplificado tipo bonequinho de massinha.
    Proporcoes humanas (1.75m total):
    - head: esfera 0.13 raio
    - torso: cilindro 0.6 alt
    - bracos: 2 cilindros + esferas (ombros, cotovelos)
    - pernas: 2 cilindros + esferas (quadris, joelhos)
    - bbox final em coordenadas mundo
    """
    parts = []

    # Cabeca em y=1.65
    head = add_uv_sphere("Head", (0, 0, 1.62), radius=0.13)
    parts.append(head)

    # Pescoco
    neck = add_cylinder("Neck", (0, 0, 1.48), radius=0.05, depth=0.08)
    parts.append(neck)

    # Torso (peito)
    chest = add_cube_box("Chest", (0, 0, 1.32), size=0.32)
    chest.scale = (1.0, 0.6, 0.7)
    parts.append(chest)

    # Abdomen
    abdomen = add_cube_box("Abdomen", (0, 0, 1.10), size=0.26)
    abdomen.scale = (1.0, 0.7, 0.7)
    parts.append(abdomen)

    # Quadris
    hips = add_cube_box("Hips", (0, 0, 0.94), size=0.30)
    hips.scale = (1.0, 0.7, 0.5)
    parts.append(hips)

    # Braco D (right = positivo X em Blender se MIRROR)
    # Em Blender padrao, R do char eh -X (espelhado)
    # ombros: esferas
    sh_l = add_uv_sphere("ShoulderL", (0.18, 0, 1.40), radius=0.07)
    sh_r = add_uv_sphere("ShoulderR", (-0.18, 0, 1.40), radius=0.07)
    parts.extend([sh_l, sh_r])
    # bracos superiores (em A-pose, leve angulo lateral)
    arm_up_l = add_cylinder("UpperArmL", (0.27, 0, 1.20), radius=0.045, depth=0.32,
                             rotation=(0, math.radians(15), 0))
    arm_up_r = add_cylinder("UpperArmR", (-0.27, 0, 1.20), radius=0.045, depth=0.32,
                             rotation=(0, math.radians(-15), 0))
    parts.extend([arm_up_l, arm_up_r])
    # cotovelos
    el_l = add_uv_sphere("ElbowL", (0.35, 0, 1.02), radius=0.05)
    el_r = add_uv_sphere("ElbowR", (-0.35, 0, 1.02), radius=0.05)
    parts.extend([el_l, el_r])
    # antebracos
    arm_lo_l = add_cylinder("ForeArmL", (0.42, 0, 0.82), radius=0.04, depth=0.32,
                             rotation=(0, math.radians(15), 0))
    arm_lo_r = add_cylinder("ForeArmR", (-0.42, 0, 0.82), radius=0.04, depth=0.32,
                             rotation=(0, math.radians(-15), 0))
    parts.extend([arm_lo_l, arm_lo_r])
    # maos
    hand_l = add_uv_sphere("HandL", (0.50, 0, 0.65), radius=0.06)
    hand_l.scale = (1.0, 1.0, 1.3)
    hand_r = add_uv_sphere("HandR", (-0.50, 0, 0.65), radius=0.06)
    hand_r.scale = (1.0, 1.0, 1.3)
    parts.extend([hand_l, hand_r])

    # Pernas
    # quadris (esferas pra junta)
    hp_l = add_uv_sphere("HipL", (0.10, 0, 0.85), radius=0.08)
    hp_r = add_uv_sphere("HipR", (-0.10, 0, 0.85), radius=0.08)
    parts.extend([hp_l, hp_r])
    # coxas
    th_l = add_cylinder("ThighL", (0.10, 0, 0.60), radius=0.07, depth=0.45)
    th_r = add_cylinder("ThighR", (-0.10, 0, 0.60), radius=0.07, depth=0.45)
    parts.extend([th_l, th_r])
    # joelhos
    kn_l = add_uv_sphere("KneeL", (0.10, 0, 0.38), radius=0.06)
    kn_r = add_uv_sphere("KneeR", (-0.10, 0, 0.38), radius=0.06)
    parts.extend([kn_l, kn_r])
    # canelas
    sh_low_l = add_cylinder("ShinL", (0.10, 0, 0.18), radius=0.05, depth=0.40)
    sh_low_r = add_cylinder("ShinR", (-0.10, 0, 0.18), radius=0.05, depth=0.40)
    parts.extend([sh_low_l, sh_low_r])
    # pes
    ft_l = add_cube_box("FootL", (0.10, 0.05, 0.025), size=0.10)
    ft_l.scale = (0.7, 2.0, 0.5)
    ft_r = add_cube_box("FootR", (-0.10, 0.05, 0.025), size=0.10)
    ft_r.scale = (0.7, 2.0, 0.5)
    parts.extend([ft_l, ft_r])

    # Aplicar transformacoes em todos antes de juntar
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Juntar tudo num so mesh
    body = join_objects(parts, "Body")

    # Suavizar
    bpy.ops.object.shade_smooth()

    # Adicionar Subsurf modifier? Nao, deixar low poly pra ficar leve no GLB

    print(f"  body mesh: verts={len(body.data.vertices)} tris={len(body.data.polygons)}")
    return body


# ============================================================
# 2) METARIG RIGIFY
# ============================================================

def add_rigify_metarig():
    """
    Cria metarig humanoide chamando direto a funcao rigify.metarigs.Basic.basic_human.create()
    em vez de bpy.ops.object.armature_human_metarig_add() (que falha em headless).
    """
    addon_utils.enable("rigify", default_set=True, persistent=True)

    # Cria objeto armature vazio primeiro
    arm_data = bpy.data.armatures.new("metarig")
    arm_obj = bpy.data.objects.new("metarig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)

    # Chamar a funcao create do rigify
    from rigify.metarigs.Basic import basic_human

    # basic_human.create() espera (obj) com obj ja em EDIT mode
    bpy.ops.object.mode_set(mode="EDIT")
    basic_human.create(arm_obj)
    bpy.ops.object.mode_set(mode="OBJECT")

    print(f"  metarig bones: {len(arm_obj.data.bones)}")
    return arm_obj


# ============================================================
# 3) ALINHAR METARIG AO MESH
# ============================================================

def fit_metarig_to_mesh(metarig, mesh):
    """
    Mesh humanoide ja foi construido em proporcoes humanas (1.75m altura).
    Metarig basic_human do Rigify vem com altura ~1.85m por default.
    Ajustar scale uniform.
    """
    # bbox do mesh em world coords
    mesh_min_z = min((mesh.matrix_world @ v.co).z for v in mesh.data.vertices)
    mesh_max_z = max((mesh.matrix_world @ v.co).z for v in mesh.data.vertices)
    mesh_height = mesh_max_z - mesh_min_z

    # bbox do metarig (em edit mode usar head e tail)
    bpy.context.view_layer.objects.active = metarig
    bpy.ops.object.mode_set(mode="EDIT")
    e_min_z = min(b.head.z for b in metarig.data.edit_bones)
    e_max_z = max(b.tail.z for b in metarig.data.edit_bones)
    rig_height = e_max_z - e_min_z
    bpy.ops.object.mode_set(mode="OBJECT")

    scale = mesh_height / rig_height
    print(f"  mesh h={mesh_height:.3f} rig h={rig_height:.3f} scale={scale:.3f}")

    metarig.scale = (scale, scale, scale)
    metarig.location = (0, 0, mesh_min_z)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


# ============================================================
# 4) GENERATE RIG
# ============================================================

def generate_rig(metarig):
    """
    Gera o rig real chamando rigify.generate.generate_rig direto.
    Em headless bpy.ops.pose.rigify_generate falha.
    """
    bpy.context.view_layer.objects.active = metarig
    bpy.ops.object.select_all(action="DESELECT")
    metarig.select_set(True)

    # Em algumas versoes da gente eh preciso ativar o modo OBJECT primeiro
    bpy.ops.object.mode_set(mode="OBJECT")

    from rigify import generate

    # generate_rig(context, metarig) - cria um novo armature "rig"
    try:
        generate.generate_rig(bpy.context, metarig)
    except Exception as e:
        print(f"  generate ERR: {type(e).__name__}: {e}")
        raise

    # rig criado eh o active object agora (ou objeto chamado "rig")
    rig = bpy.data.objects.get("rig")
    if not rig:
        # fallback: ultimo objeto criado
        rig = bpy.context.active_object

    print(f"  rig: {rig.name} bones={len(rig.data.bones)}")
    return rig


# ============================================================
# 5) PARENT WITH AUTOMATIC WEIGHTS
# ============================================================

def parent_mesh_to_rig(mesh, rig):
    """
    Parent mesh -> armature, com Automatic Weights.
    """
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig  # rig deve ser active

    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    # Verificar vertex groups criados
    vg_count = len(mesh.vertex_groups)
    print(f"  vertex groups apos parent: {vg_count}")

    # Verificar armature modifier
    mods = [m for m in mesh.modifiers if m.type == "ARMATURE"]
    print(f"  armature modifiers: {len(mods)}")


# ============================================================
# 6) ANIMACAO: WALK CYCLE PROCEDURAL
# ============================================================

def make_walk_cycle(rig, duration_sec=1.5, fps=30):
    """
    Cria walk cycle simples nos bones de controle do rig Rigify.
    Rigify cria bones IK/FK; vou usar IK pra pes (foot_ik.L/R) e os bracos via FK.

    Pattern: 4 keyframes principais (contact L, passing R, contact R, passing L)
    + 1 keyframe pra fechar o loop = 5 frames distribuidos em duration_sec
    """
    scene = bpy.context.scene
    scene.render.fps = fps
    total_frames = int(duration_sec * fps)
    scene.frame_start = 1
    scene.frame_end = total_frames

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")

    bones = rig.pose.bones

    # Listar bones disponiveis pra debug
    bone_names = sorted(bones.keys())
    print(f"  rig bones (sample): {bone_names[:15]} ... total={len(bone_names)}")

    # CRITICO: setar IK->FK switch. Rigify comeca em IK_FK=0 (IK ativo),
    # entao DEF bones seguem IK controls. Como animei FK, preciso virar pra FK (=1.0).
    fk_switches = ["thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"]
    for sw_name in fk_switches:
        b = bones.get(sw_name)
        if b and "IK_FK" in b:
            b["IK_FK"] = 1.0
            # keyframar no frame 1 pra ficar permanente
            b.keyframe_insert('["IK_FK"]', frame=1)
            print(f"    {sw_name}.IK_FK -> 1.0 (FK mode)")
        else:
            print(f"    WARN: {sw_name} sem prop IK_FK")

    # Bones que Rigify cria (basic_human gera o set padrao):
    # - root, torso, hips, chest, neck, head
    # - upper_arm_fk.L/R, forearm_fk.L/R, hand_fk.L/R (FK arm)
    # - thigh_fk.L/R, shin_fk.L/R, foot_fk.L/R (FK leg)
    # - foot_ik.L/R, hand_ik.L/R (IK targets)
    # - shoulder.L/R
    # - upper_arm_parent.L/R (switches)

    def get_bone(name):
        b = bones.get(name)
        return b

    def kf_rot(bone, frame, euler_deg):
        if not bone:
            return
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = tuple(math.radians(a) for a in euler_deg)
        bone.keyframe_insert("rotation_euler", frame=frame)

    def kf_loc(bone, frame, loc):
        if not bone:
            return
        bone.location = loc
        bone.keyframe_insert("location", frame=frame)

    # Frames-chave de um ciclo de caminhada (4-pose pattern + loop close)
    # passo 1: pe L atras, pe R frente
    # passo 2: pe L passa por baixo, pe R recebe
    # passo 3: pe L frente, pe R atras
    # passo 4: pe R passa por baixo, pe L recebe
    # passo 5 = passo 1
    f1 = 1
    f2 = total_frames // 4
    f3 = total_frames // 2
    f4 = (3 * total_frames) // 4
    f5 = total_frames

    # Torso: sobe e desce duas vezes por ciclo (passing poses), leve sway lateral
    torso = get_bone("torso")
    if torso:
        # bob vertical: alto em f2 e f4 (passing), baixo em f1, f3, f5 (contact)
        bob = 0.04
        sway = 0.025
        # locations em local (torso bone)
        kf_loc(torso, f1, (sway, 0, 0))         # leve direita
        kf_loc(torso, f2, (0, 0, bob))           # alto, centro
        kf_loc(torso, f3, (-sway, 0, 0))         # leve esquerda
        kf_loc(torso, f4, (0, 0, bob))
        kf_loc(torso, f5, (sway, 0, 0))

    # Pelvis sway (counter)
    hips = get_bone("hips")
    if hips:
        kf_rot(hips, f1, (0, 0, 5))
        kf_rot(hips, f2, (0, 0, 0))
        kf_rot(hips, f3, (0, 0, -5))
        kf_rot(hips, f4, (0, 0, 0))
        kf_rot(hips, f5, (0, 0, 5))

    # Spine: leve rotacao counter ao hips
    chest = get_bone("spine_fk.001") or get_bone("chest")
    if chest:
        kf_rot(chest, f1, (0, 0, -5))
        kf_rot(chest, f2, (0, 0, 0))
        kf_rot(chest, f3, (0, 0, 5))
        kf_rot(chest, f4, (0, 0, 0))
        kf_rot(chest, f5, (0, 0, -5))

    # Pernas FK (mais simples que IK pra walk cycle proceduralmente)
    thigh_L = get_bone("thigh_fk.L")
    thigh_R = get_bone("thigh_fk.R")
    shin_L = get_bone("shin_fk.L")
    shin_R = get_bone("shin_fk.R")
    foot_L = get_bone("foot_fk.L")
    foot_R = get_bone("foot_fk.R")

    # Walk: thigh angula X (pivot quadril), shin estende/contrai (joelho)
    # Lado L: f1 frente, f3 atras
    # Lado R: f1 atras, f3 frente
    # X positivo = perna pra frente (depende da orientacao do bone)

    if thigh_L:
        kf_rot(thigh_L, f1, (-25, 0, 0))   # L atras
        kf_rot(thigh_L, f2, (0, 0, 0))     # passing
        kf_rot(thigh_L, f3, (35, 0, 0))    # L frente
        kf_rot(thigh_L, f4, (10, 0, 0))    # contact
        kf_rot(thigh_L, f5, (-25, 0, 0))
    if thigh_R:
        kf_rot(thigh_R, f1, (35, 0, 0))    # R frente
        kf_rot(thigh_R, f2, (10, 0, 0))
        kf_rot(thigh_R, f3, (-25, 0, 0))
        kf_rot(thigh_R, f4, (0, 0, 0))
        kf_rot(thigh_R, f5, (35, 0, 0))

    # Joelhos: dobram quando perna vai recuar (passa por baixo)
    if shin_L:
        kf_rot(shin_L, f1, (15, 0, 0))     # L atras dobra leve
        kf_rot(shin_L, f2, (60, 0, 0))     # passing: max bend
        kf_rot(shin_L, f3, (5, 0, 0))      # L frente esticada
        kf_rot(shin_L, f4, (15, 0, 0))
        kf_rot(shin_L, f5, (15, 0, 0))
    if shin_R:
        kf_rot(shin_R, f1, (5, 0, 0))
        kf_rot(shin_R, f2, (15, 0, 0))
        kf_rot(shin_R, f3, (15, 0, 0))
        kf_rot(shin_R, f4, (60, 0, 0))     # passing R
        kf_rot(shin_R, f5, (5, 0, 0))

    # Pe: leve rotacao pra acompanhar contacto
    if foot_L:
        kf_rot(foot_L, f1, (10, 0, 0))
        kf_rot(foot_L, f2, (-15, 0, 0))
        kf_rot(foot_L, f3, (-20, 0, 0))
        kf_rot(foot_L, f4, (5, 0, 0))
        kf_rot(foot_L, f5, (10, 0, 0))
    if foot_R:
        kf_rot(foot_R, f1, (-20, 0, 0))
        kf_rot(foot_R, f2, (5, 0, 0))
        kf_rot(foot_R, f3, (10, 0, 0))
        kf_rot(foot_R, f4, (-15, 0, 0))
        kf_rot(foot_R, f5, (-20, 0, 0))

    # Bracos: contra-balanco (opostos as pernas)
    # Quando perna L vai pra tras, braco L vai pra frente
    upper_arm_L = get_bone("upper_arm_fk.L")
    upper_arm_R = get_bone("upper_arm_fk.R")
    forearm_L = get_bone("forearm_fk.L")
    forearm_R = get_bone("forearm_fk.R")

    if upper_arm_L:
        kf_rot(upper_arm_L, f1, (30, 0, 0))   # L frente
        kf_rot(upper_arm_L, f2, (0, 0, 0))
        kf_rot(upper_arm_L, f3, (-30, 0, 0))  # L tras
        kf_rot(upper_arm_L, f4, (0, 0, 0))
        kf_rot(upper_arm_L, f5, (30, 0, 0))
    if upper_arm_R:
        kf_rot(upper_arm_R, f1, (-30, 0, 0))
        kf_rot(upper_arm_R, f2, (0, 0, 0))
        kf_rot(upper_arm_R, f3, (30, 0, 0))
        kf_rot(upper_arm_R, f4, (0, 0, 0))
        kf_rot(upper_arm_R, f5, (-30, 0, 0))

    # Cotovelos: leve dobra constante (braco humano walking)
    if forearm_L:
        kf_rot(forearm_L, f1, (30, 0, 0))
        kf_rot(forearm_L, f3, (45, 0, 0))
        kf_rot(forearm_L, f5, (30, 0, 0))
    if forearm_R:
        kf_rot(forearm_R, f1, (45, 0, 0))
        kf_rot(forearm_R, f3, (30, 0, 0))
        kf_rot(forearm_R, f5, (45, 0, 0))

    # Cabeca: leve bob
    head = get_bone("head")
    if head:
        kf_rot(head, f1, (0, 0, 2))
        kf_rot(head, f3, (0, 0, -2))
        kf_rot(head, f5, (0, 0, 2))

    # Renomear action (Blender 5.x usa layered actions)
    if rig.animation_data and rig.animation_data.action:
        action = rig.animation_data.action
        action.name = "WalkCycle"
        # No Blender 5.x, fcurves estao em layers[].strips[].channelbag(slot).fcurves
        # Iteracao defensiva:
        try:
            for layer in action.layers:
                for strip in layer.strips:
                    for slot in action.slots:
                        cb = strip.channelbag(slot, ensure=False)
                        if cb:
                            for fc in cb.fcurves:
                                for kp in fc.keyframe_points:
                                    kp.interpolation = "BEZIER"
        except Exception as e:
            print(f"  (warn) ajuste de interpolation falhou: {e}")

    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"  walk cycle: frames 1-{total_frames} @ {fps}fps, action={rig.animation_data.action.name if rig.animation_data else 'none'}")


# ============================================================
# 7) MATERIAL
# ============================================================

def apply_clay_material(mesh, color=(0.95, 0.55, 0.45, 1.0)):
    mat = bpy.data.materials.new("ClayBody")
    mat.use_nodes = True
    nt = mat.node_tree
    # Pegar Principled BSDF
    bsdf = nt.nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.65
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.3
    mesh.data.materials.clear()
    mesh.data.materials.append(mat)


# ============================================================
# 8) EXPORT GLB
# ============================================================

def export_glb(out_path, mesh, rig):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig

    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_yup=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_step=1,
        export_optimize_animation_size=False,
        export_skins=True,
        export_def_bones=True,  # exporta apenas DEF bones (Rigify deformation bones)
        export_armature_object_remove=False,
    )
    sz = out_path.stat().st_size / 1024
    print(f"  exported: {out_path.name} ({sz:.1f}KB)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("BUILD CHARACTER + RIG + WALK CYCLE")
    print("=" * 60)

    reset_scene()

    print("\n[1] Building humanoid mesh...")
    body = build_humanoid_mesh()

    print("\n[2] Applying material...")
    apply_clay_material(body)

    print("\n[3] Adding Rigify metarig...")
    metarig = add_rigify_metarig()

    print("\n[4] Fitting metarig to mesh...")
    fit_metarig_to_mesh(metarig, body)

    print("\n[5] Generating rig...")
    rig = generate_rig(metarig)

    print("\n[6] Parenting mesh to rig (automatic weights)...")
    parent_mesh_to_rig(body, rig)

    print("\n[7] Creating walk cycle...")
    make_walk_cycle(rig, duration_sec=1.5, fps=30)

    print("\n[8] Exporting GLB...")
    out_path = OUT_DIR / "character_walk.glb"
    export_glb(out_path, body, rig)

    # Salvar tambem o .blend pra debug
    blend_path = OUT_DIR / "character_walk.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"  blend saved: {blend_path.name}")

    print("\n[DONE]")


if __name__ == "__main__":
    main()
