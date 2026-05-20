"""Extrai cada asset (folha de hierarquia 2 niveis abaixo de root) como GLB separado.
Estrutura esperada: ROOT_EMPTY (BUILDINGS/ANIMALS) > CATEGORIA (Empty) > ASSET (Empty ou Mesh) > [meshes...]

Uso:
  blender --background --python extract_assets.py -- \
    --src <blend_file> \
    --out-dir <dst_root> \
    --root-name BUILDINGS \
    [--dry-run] \
    [--only <asset_name>] \
    [--skip-existing]

Saida:
  <out-dir>/<categoria>/<AssetName>.glb
  <out-dir>/_manifest.json
"""
import bpy, sys, json, os, traceback
from pathlib import Path
from mathutils import Vector

# -------- args --------
def parse_args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"src": None, "out_dir": None, "root_name": None, "dry_run": False, "only": None, "skip_existing": False}
    i = 0
    while i < len(a):
        if a[i] == "--src": out["src"] = a[i+1]; i += 2
        elif a[i] == "--out-dir": out["out_dir"] = a[i+1]; i += 2
        elif a[i] == "--root-name": out["root_name"] = a[i+1]; i += 2
        elif a[i] == "--dry-run": out["dry_run"] = True; i += 1
        elif a[i] == "--only": out["only"] = a[i+1]; i += 2
        elif a[i] == "--skip-existing": out["skip_existing"] = True; i += 1
        else: i += 1
    return out

args = parse_args()
SRC = args["src"]; OUT_DIR = Path(args["out_dir"]); ROOT_NAME = args["root_name"]
DRY = args["dry_run"]; ONLY = args["only"]; SKIP_EXISTING = args["skip_existing"]
if not SRC or not OUT_DIR or not ROOT_NAME:
    raise SystemExit("faltam args: --src, --out-dir, --root-name")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -------- carrega blend (open_mainfile preserva collections originais) --------
print(f"[load] {SRC}")
bpy.ops.wm.open_mainfile(filepath=SRC)

# garante que todas as layer_collections estao visiveis e nao excluidas
def unexclude(lc):
    if lc.exclude: lc.exclude = False
    if lc.hide_viewport: lc.hide_viewport = False
    if lc.collection.hide_viewport: lc.collection.hide_viewport = False
    for ch in lc.children:
        unexclude(ch)
unexclude(bpy.context.view_layer.layer_collection)
print(f"[viewlayer] unexcluded todas layer_collections")

# UNLINK os objetos da Scene Collection raiz que ESTAO TAMBEM em uma sub-collection
# (a cena raiz tem todos objetos duplicados — vamos manter so na sub-collection)
scene_coll = bpy.context.scene.collection
n_before = len(scene_coll.objects)
removed = 0
for o in list(scene_coll.objects):
    # se o objeto esta em alguma OUTRA collection alem da scene raiz, podemos desligar da raiz
    other_colls = [c for c in o.users_collection if c != scene_coll]
    if other_colls:
        scene_coll.objects.unlink(o)
        removed += 1
print(f"[clean] removidos {removed}/{n_before} da Scene Collection raiz (mantidos nas sub-collections)")

root = bpy.data.objects.get(ROOT_NAME)
if root is None:
    raise SystemExit(f"root '{ROOT_NAME}' nao achado no .blend")

print(f"[root] {root.name} - {len(root.children)} categorias")

# -------- coleta assets --------
def gather_descendants(obj, acc):
    acc.append(obj)
    for c in obj.children:
        gather_descendants(c, acc)
    return acc

assets = []  # [(categoria, asset_obj, [descendantes])]
for cat in root.children:
    cat_name = cat.name
    for asset in cat.children:
        descendants = []
        gather_descendants(asset, descendants)
        descendants = [d for d in descendants if d.type in ('MESH', 'EMPTY', 'ARMATURE', 'CURVE')]
        if not any(d.type == 'MESH' for d in descendants):
            print(f"[skip] {cat_name}/{asset.name} - sem mesh")
            continue
        assets.append((cat_name, asset, descendants))

print(f"[plan] {len(assets)} assets pra exportar")

if DRY:
    for cat, ast, descs in assets:
        n_mesh = sum(1 for d in descs if d.type == 'MESH')
        print(f"  {cat:20s} {ast.name:30s}  meshes={n_mesh}  desc={len(descs)}")
    raise SystemExit(0)

# -------- helpers --------
def safe_name(s):
    return s.replace(" ", "_").replace("/", "_").replace("\\", "_")

manifest = {"src": SRC, "root": ROOT_NAME, "items": []}

# -------- export loop --------
# estrategia: pra cada asset, criar uma scene temporaria so com os descendentes do asset.
# isso garante que o exporter glTF nao "veja" outros objetos (mesmo que estejam em collections compartilhadas).
for idx, (cat_name, asset_obj, descendants) in enumerate(assets, 1):
    safe_cat = safe_name(cat_name)
    safe_asset = safe_name(asset_obj.name)
    if ONLY and safe_asset != ONLY and asset_obj.name != ONLY:
        continue
    cat_dir = OUT_DIR / safe_cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    glb_path = cat_dir / f"{safe_asset}.glb"

    if SKIP_EXISTING and glb_path.exists() and glb_path.stat().st_size > 0:
        print(f"[{idx:3d}/{len(assets)}] SKIP existente {glb_path.name}")
        manifest["items"].append({
            "category": cat_name, "asset": asset_obj.name, "glb": str(glb_path.relative_to(OUT_DIR)).replace("\\","/"),
            "n_meshes": sum(1 for d in descendants if d.type == 'MESH'),
            "skipped": True,
        })
        continue

    temp_scene = None
    try:
        # calcula bbox global dos meshes
        mesh_descs = [d for d in descendants if d.type == 'MESH' and d.data and len(d.data.vertices) > 0]
        if mesh_descs:
            bb_min = Vector(( 1e18,  1e18,  1e18))
            bb_max = Vector((-1e18, -1e18, -1e18))
            for m in mesh_descs:
                mw = m.matrix_world
                for v in m.data.vertices:
                    wp = mw @ v.co
                    for k in range(3):
                        bb_min[k] = min(bb_min[k], wp[k])
                        bb_max[k] = max(bb_max[k], wp[k])
            cx = (bb_min.x + bb_max.x) * 0.5
            cy = (bb_min.y + bb_max.y) * 0.5
            cz_floor = bb_min.z
            offset = Vector((-cx, -cy, -cz_floor))
        else:
            offset = Vector((0, 0, 0))

        # aplica offset em TODOS descendentes (matrix_world)
        for d in descendants:
            mw = d.matrix_world.copy()
            mw.translation = mw.translation + offset
            d.matrix_world = mw
        bpy.context.view_layer.update()

        # HIDE todos os objetos exceto os do asset, exporta com use_visible=True
        descendant_set = set(descendants)
        hidden_objs = []
        for o in bpy.data.objects:
            if o not in descendant_set:
                if not o.hide_render:
                    o.hide_render = True
                    hidden_objs.append(o)
                if not o.hide_viewport:
                    o.hide_viewport = True
                    if o not in hidden_objs: hidden_objs.append(o)

        # garante que os do asset estao visiveis
        for d in descendants:
            d.hide_render = False
            d.hide_viewport = False

        # seleciona
        bpy.ops.object.select_all(action='DESELECT')
        for d in descendants:
            try: d.select_set(True)
            except RuntimeError: pass
        for d in descendants:
            bpy.context.view_layer.objects.active = d
            break

        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            use_selection=True,
            use_visible=True,
            use_active_scene=True,
            export_format='GLB',
            export_apply=True,
            export_yup=True,
            export_materials='EXPORT',
            export_image_format='AUTO',
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_morph=False,
            export_skins=False,
        )

        # restaura visibilidade
        for o in hidden_objs:
            o.hide_render = False
            o.hide_viewport = False

        size = glb_path.stat().st_size
        n_mesh = sum(1 for d in descendants if d.type == 'MESH')
        print(f"[{idx:3d}/{len(assets)}] OK  {safe_cat}/{safe_asset}.glb  ({size/1024:.0f} KB, {n_mesh} mesh)")
        manifest["items"].append({
            "category": cat_name, "asset": asset_obj.name,
            "glb": str(glb_path.relative_to(OUT_DIR)).replace("\\","/"),
            "size_kb": round(size/1024, 1),
            "n_meshes": n_mesh,
            "ok": True,
        })

        # reverte offset
        for d in descendants:
            mw = d.matrix_world.copy()
            mw.translation = mw.translation - offset
            d.matrix_world = mw
        bpy.context.view_layer.update()

    except Exception as e:
        print(f"[{idx:3d}/{len(assets)}] ERR {safe_cat}/{safe_asset}: {e}")
        traceback.print_exc()
        manifest["items"].append({
            "category": cat_name, "asset": asset_obj.name,
            "error": str(e), "ok": False,
        })

manifest_path = OUT_DIR / "_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print(f"\n[manifest] {manifest_path}")
ok = sum(1 for i in manifest["items"] if i.get("ok"))
sk = sum(1 for i in manifest["items"] if i.get("skipped"))
er = sum(1 for i in manifest["items"] if not i.get("ok") and not i.get("skipped"))
print(f"[summary] ok={ok} skipped={sk} err={er} total={len(manifest['items'])}")
