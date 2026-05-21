"""Pipeline autonoma de grama com esqueleto + wind animation.

Estrategia:
- 1 blade de grama = mesh com 3 bones (base/mid/top), skin weighting por altura
- 1 GLB com skin + animation loop de wind sway
- Player Three.js clona N vezes via SkeletonUtils, distribui no plano,
  cada clone com phase offset diferente
- Slider de "vento" em runtime: JS multiplica rotacao dos bones depois do mixer.update()

Tambem exporta um plano (chao) como GLB separado pra cena.

Decisoes tecnicas:
- Cada blade tem 5 segmentos verticais x 2 colunas = 12 verts / 10 tris
- Altura blade = 0.6m, largura base 0.04m, afila pra topo
- 3 bones em cadeia: B0 (base, 0-0.2m), B1 (mid, 0.2-0.4m), B2 (top, 0.4-0.6m)
- Skin: vertice ganha peso pelo bone mais proximo em Z, com falloff suave
- Wind anim: 60 frames @ 30fps = 2s loop. Rotacao dos bones via funcao sinusoidal,
  amplitude crescente do base pro topo (top oscila mais)
- Salva 2 GLBs: blade.glb (mesh+skin+anim) e ground.glb (plano texturizado)
"""
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion

OUT_DIR = Path(__file__).resolve().parent.parent / "out" / "glb"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLADE_HEIGHT = 0.55
BLADE_BASE_WIDTH = 0.07
BLADE_SEGMENTS = 6  # divisoes verticais (mais = curva mais suave)
BLADE_CURL = 0.08   # quanto a blade naturalmente curva pra frente (em metros no topo)
ANIM_FRAMES = 60
ANIM_FPS = 30


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.render.fps = ANIM_FPS
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = ANIM_FRAMES


# ============================================================
# 1) BLADE MESH
# ============================================================

def build_blade_mesh():
    """Constroi mesh de uma unica blade.

    Geometria: quad strip vertical, base larga, topo afilado.
    BLADE_SEGMENTS=5 -> 6 niveis de altura -> 12 verts -> 10 tris
    """
    bm = bmesh.new()

    verts_left = []
    verts_right = []

    for i in range(BLADE_SEGMENTS + 1):
        t = i / BLADE_SEGMENTS  # 0 = base, 1 = topo
        z = t * BLADE_HEIGHT
        # Largura — afila com curva (quadratica) — mais cheia no meio
        # forma: largura = max * (1-t)^0.7 — descida suave, ponta fina
        w_factor = math.pow(1.0 - t, 0.6)
        w = BLADE_BASE_WIDTH * w_factor * 0.5
        # Curl natural — blade vergada pra frente (Y positivo), mais no topo (t^2)
        y_curl = BLADE_CURL * (t * t)
        vl = bm.verts.new((-w, y_curl, z))
        vr = bm.verts.new((w, y_curl, z))
        verts_left.append(vl)
        verts_right.append(vr)

    bm.verts.ensure_lookup_table()

    # Faces (quads)
    for i in range(BLADE_SEGMENTS):
        bm.faces.new([
            verts_left[i], verts_right[i],
            verts_right[i + 1], verts_left[i + 1]
        ])

    mesh = bpy.data.meshes.new("Blade")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Blade", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Shade smooth
    bpy.ops.object.shade_smooth()

    print(f"  blade mesh: verts={len(mesh.vertices)} faces={len(mesh.polygons)}")
    return obj


# ============================================================
# 2) ARMATURE COM 3 BONES (cadeia base->mid->top)
# ============================================================

def build_armature():
    """3 bones empilhados verticalmente, conectados em cadeia."""
    arm_data = bpy.data.armatures.new("BladeArmature")
    arm_obj = bpy.data.objects.new("BladeArmature", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    h = BLADE_HEIGHT
    b0 = eb.new("B0_base")
    b0.head = (0, 0, 0)
    b0.tail = (0, 0, h / 3)

    b1 = eb.new("B1_mid")
    b1.head = (0, 0, h / 3)
    b1.tail = (0, 0, 2 * h / 3)
    b1.parent = b0
    b1.use_connect = True

    b2 = eb.new("B2_top")
    b2.head = (0, 0, 2 * h / 3)
    b2.tail = (0, 0, h)
    b2.parent = b1
    b2.use_connect = True

    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"  armature: bones={len(arm_data.bones)} names={[b.name for b in arm_data.bones]}")
    return arm_obj


# ============================================================
# 3) SKINNING — pesos por altura
# ============================================================

def skin_blade(blade, arm_obj):
    """Cria vertex groups e atribui pesos por altura Z do vertice.

    B0_base influencia 0-0.33h (peso 1 na base, decai pra cima)
    B1_mid  influencia 0.16-0.66h (gaussiano centrado em 0.5h)
    B2_top  influencia 0.5-1h (peso 0 em 0.5h, peso 1 no topo)
    Pesos normalizados pra somar 1.
    """
    # Adiciona armature modifier
    mod = blade.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj

    # Parent (sem auto weights — vamos definir manualmente)
    blade.parent = arm_obj

    # Cria vertex groups
    vg0 = blade.vertex_groups.new(name="B0_base")
    vg1 = blade.vertex_groups.new(name="B1_mid")
    vg2 = blade.vertex_groups.new(name="B2_top")

    h = BLADE_HEIGHT
    for v in blade.data.vertices:
        z = v.co.z
        t = z / h  # 0..1
        # Funcoes de peso por altura — soma = 1
        # base: 1 em t=0, 0 em t>=0.5
        w0 = max(0.0, 1.0 - t * 2.0)
        # top: 0 em t<=0.5, 1 em t=1
        w2 = max(0.0, (t - 0.5) * 2.0)
        # mid: complement
        w1 = max(0.0, 1.0 - w0 - w2)
        # normalizar
        s = w0 + w1 + w2
        if s > 0:
            w0 /= s
            w1 /= s
            w2 /= s
        vg0.add([v.index], w0, "REPLACE")
        vg1.add([v.index], w1, "REPLACE")
        vg2.add([v.index], w2, "REPLACE")

    print(f"  skinned {len(blade.data.vertices)} verts to 3 bones")


# ============================================================
# 4) WIND ANIMATION (loop perfeito)
# ============================================================

def make_wind_animation(arm_obj):
    """Cria animacao de wind sway nos bones em loop perfeito (2s @ 30fps).

    Padrao: rotacao em X (forward/backward sway).
    Top bone oscila com amplitude maior, base quase parado.
    Phase shifts entre bones pra dar look "viscoso" de wind.
    """
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")

    pose = arm_obj.pose
    b0 = pose.bones["B0_base"]
    b1 = pose.bones["B1_mid"]
    b2 = pose.bones["B2_top"]

    for b in (b0, b1, b2):
        b.rotation_mode = "XYZ"

    # Amplitudes (radianos) — base mexe pouco, top mexe muito
    amp_base = math.radians(3)   # ~3 graus
    amp_mid = math.radians(8)    # ~8 graus
    amp_top = math.radians(15)   # ~15 graus

    # Frequency — 1 ciclo completo em ANIM_FRAMES (loop perfeito)
    # Pequeno phase shift entre bones pra wind parecer viscoso
    phase_mid = -0.15
    phase_top = -0.30

    for f in range(1, ANIM_FRAMES + 1):
        t = (f - 1) / ANIM_FRAMES  # 0..1
        # angulo por bone via seno
        a0 = amp_base * math.sin(2 * math.pi * t)
        a1 = amp_mid * math.sin(2 * math.pi * (t + phase_mid))
        a2 = amp_top * math.sin(2 * math.pi * (t + phase_top))
        b0.rotation_euler = (a0, 0, 0)
        b1.rotation_euler = (a1, 0, 0)
        b2.rotation_euler = (a2, 0, 0)
        b0.keyframe_insert("rotation_euler", frame=f)
        b1.keyframe_insert("rotation_euler", frame=f)
        b2.keyframe_insert("rotation_euler", frame=f)

    # Action rename
    if arm_obj.animation_data and arm_obj.animation_data.action:
        arm_obj.animation_data.action.name = "WindSway"

    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"  wind anim: {ANIM_FRAMES} frames @ {ANIM_FPS}fps, loop perfect")


# ============================================================
# 5) MATERIAL DA GRAMA
# ============================================================

def apply_grass_material(blade):
    """Material verde com gradiente base-tipo (procedural simples, mas
    converte pra Principled BSDF puro pra exportar bem).
    Base mais escura (terra), tipo mais clara (luz). Faz gradiente via vertex color.
    """
    # Adicionar vertex color por altura
    mesh = blade.data
    if not mesh.color_attributes:
        cattr = mesh.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    else:
        cattr = mesh.color_attributes[0]

    h = BLADE_HEIGHT
    base_color = (0.06, 0.18, 0.04)  # verde bem escuro (raiz/terra)
    tip_color = (0.28, 0.42, 0.10)   # verde medio (nao muito claro)
    for i, v in enumerate(mesh.vertices):
        t = v.co.z / h
        r = base_color[0] * (1 - t) + tip_color[0] * t
        g = base_color[1] * (1 - t) + tip_color[1] * t
        b = base_color[2] * (1 - t) + tip_color[2] * t
        cattr.data[i].color = (r, g, b, 1.0)

    mat = bpy.data.materials.new("GrassBlade")
    mat.use_nodes = True
    nt = mat.node_tree
    # Clear default
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    vcol = nt.nodes.new("ShaderNodeAttribute")
    vcol.attribute_name = "Col"

    bsdf.inputs["Roughness"].default_value = 0.9
    # Sheen off — estava saturando em branco no GLB
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.0

    # double-sided pra blade fina aparecer dos dois lados
    mat.use_backface_culling = False

    nt.links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mesh.materials.clear()
    mesh.materials.append(mat)
    print(f"  material: GrassBlade (vertex color gradient)")


# ============================================================
# 6) GROUND (plano texturizado)
# ============================================================

def build_ground():
    """Plano grande de chao."""
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Ground"

    mat = bpy.data.materials.new("Ground")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.18, 0.13, 0.08, 1.0)  # terra
        bsdf.inputs["Roughness"].default_value = 0.95

    plane.data.materials.clear()
    plane.data.materials.append(mat)
    return plane


# ============================================================
# 7) EXPORT
# ============================================================

def export_blade_glb(out_path, blade, arm_obj):
    bpy.ops.object.select_all(action="DESELECT")
    blade.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

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
        export_def_bones=False,  # nao tem DEF prefix — exporta todos os 3
    )
    sz = out_path.stat().st_size / 1024
    print(f"  exported blade: {out_path.name} ({sz:.1f}KB)")


def export_ground_glb(out_path, plane):
    bpy.ops.object.select_all(action="DESELECT")
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane

    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_animations=False,
        export_skins=False,
    )
    sz = out_path.stat().st_size / 1024
    print(f"  exported ground: {out_path.name} ({sz:.1f}KB)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("BUILD GRASS BLADE (mesh + 3-bone armature + wind anim)")
    print("=" * 60)

    reset_scene()

    print("\n[1] Building blade mesh...")
    blade = build_blade_mesh()

    print("\n[2] Applying grass material...")
    apply_grass_material(blade)

    print("\n[3] Building armature (3 bones)...")
    arm_obj = build_armature()

    print("\n[4] Skinning blade to armature (weighted by height)...")
    skin_blade(blade, arm_obj)

    print("\n[5] Creating wind sway animation...")
    make_wind_animation(arm_obj)

    print("\n[6] Exporting blade GLB...")
    blade_path = OUT_DIR / "blade.glb"
    export_blade_glb(blade_path, blade, arm_obj)

    # Limpar e construir ground em scene separada
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    print("\n[7] Building ground plane...")
    plane = build_ground()

    print("\n[8] Exporting ground GLB...")
    ground_path = OUT_DIR / "ground.glb"
    export_ground_glb(ground_path, plane)

    # Salvar .blend pra inspecao
    blend_path = OUT_DIR.parent / "grass_blade.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"\n  blend saved: {blend_path.name}")

    print("\n[DONE]")


if __name__ == "__main__":
    main()
