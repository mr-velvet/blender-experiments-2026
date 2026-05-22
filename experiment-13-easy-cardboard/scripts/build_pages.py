"""Build 4 HTML pages from the template + matrices."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = open(os.path.join(ROOT, 'web2', '_template.html'), encoding='utf-8').read()

PAGES = [
    {
        'slug': 'wear',
        'matrix': 'wear.json',
        'title': 'Wear — desgaste progressivo',
        'description': 'O slider <strong>Wear ⏰</strong> do Easy Cardboard 3.0 controla o estado da caixa: papelao novo, mexido, surrado. A mesma malha procedural recebe diferentes valores e o plugin reconfigura o shader + as deformacoes.',
        'control_title': 'Wear (0 → 0.9)',
        'label_fn': lambda v: f"Wear {int(v['name'].split('_')[1])/100:.2f}",
    },
    {
        'slug': 'scale',
        'matrix': 'scale.json',
        'title': 'Global Scale — granularidade do papelao',
        'description': 'O <strong>Global Scale</strong> afeta o tamanho aparente da granulacao do papel + fibras + dano de borda. Valores baixos: papelao "grosso/cardstock". Valores altos: papelao "fino/embalagem". Resolve a duvida sobre se o look estranho vem de escala errada.',
        'control_title': 'Global Scale (0.25 → 3.0)',
        'label_fn': lambda v: f"Scale {int(v['name'].split('_')[1])/100:.2f}",
    },
    {
        'slug': 'corrugation',
        'matrix': 'corrugation.json',
        'title': 'Corrugacao — Type, Direction Mask, Invert',
        'description': 'O plugin tem duas variacoes de corrugacao (<strong>Type 0/1</strong>) e um threshold de mascara direcional que decide onde o corrugado aparece em funcao da UV. <strong>Direction Mask Threshold</strong> alto = corrugado so nas quinas; baixo = espalha mais. <strong>Invert</strong> inverte essa selecao.',
        'control_title': 'Type + Direction Mask',
        'label_fn': lambda v: v['name'].replace('corr_', '').replace('_', ' ').upper(),
    },
    {
        'slug': 'shapes',
        'matrix': 'shapes.json',
        'title': 'Box Shapes — Simple Box Creator',
        'description': 'O <strong>Simple Box Creator</strong> (segundo node group do asset) gera a forma da caixa parametrica: Width × Length × Height + Flap Length + Gaps. Cada combinacao produz uma caixa diferente (cubica, alta, achatada, longa, flaps grandes/pequenos).',
        'control_title': 'Box dimensions',
        'label_fn': lambda v: v['name'].replace('shape_', '').replace('_', ' ').title(),
    },
    {
        'slug': 'wild',
        'matrix': 'wild.json',
        'title': 'Wild combos — todo o plugin junto',
        'description': 'Combinacoes complexas variando simultaneamente Box dimensions + Wear + Global Scale + Fibers + Displacement. Mostram o range do asset quando varios sliders trabalham juntos.',
        'control_title': 'Combo',
        'label_fn': lambda v: v['name'].replace('wild_', '').title(),
    },
]

def gen_label(slug, var):
    name = var['name']
    if slug == 'wear':
        v = int(name.split('_')[1])/100
        return f"Wear {v:.2f}"
    if slug == 'scale':
        v = int(name.split('_')[1])/100
        return f"Scale {v:.2f}"
    if slug == 'corrugation':
        return name.replace('corr_', '').replace('_', ' ').upper()
    if slug == 'shapes':
        return name.replace('shape_', '').replace('_', ' ').title()
    if slug == 'wild':
        return name.replace('wild_', '').title()
    return name

for page in PAGES:
    slug = page['slug']
    matrix_path = os.path.join(ROOT, 'matrices', page['matrix'])
    matrix = json.load(open(matrix_path, encoding='utf-8'))

    variations = []
    for var in matrix:
        variations.append({
            'img': f"{var['name']}.png",
            'label': gen_label(slug, var),
        })

    html = TPL
    html = html.replace('__TITLE__', page['title'])
    html = html.replace('__DESCRIPTION__', page['description'])
    html = html.replace('__CONTROL_TITLE__', page['control_title'])
    html = html.replace('__MAX__', str(len(variations) - 1))
    html = html.replace('__FIRST_IMG__', variations[0]['img'])
    html = html.replace('__FIRST_LABEL__', variations[0]['label'])
    html = html.replace('__VARIATIONS_JSON__', json.dumps(variations))

    out_dir = os.path.join(ROOT, 'web2', slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Wrote {out_path}")

# also an index linking to all 4
INDEX = '''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8" /><title>Easy Cardboard — Experiments</title>
<style>
body{background:#1a120b;color:#f3e3c3;font-family:Inter,system-ui,sans-serif;padding:60px 40px;max-width:900px;margin:0 auto;}
h1{font-size:36px;font-weight:700;margin-bottom:8px;}
.sub{color:#a08a6b;margin-bottom:40px;font-size:14px;line-height:1.6;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;}
a.card{background:rgba(20,14,8,.78);border:1px solid rgba(212,154,74,.28);border-radius:14px;padding:24px;text-decoration:none;color:#f3e3c3;transition:transform .15s, border-color .15s;}
a.card:hover{transform:translateY(-2px);border-color:#d49a4a;}
a.card h2{color:#d49a4a;font-size:18px;margin-bottom:6px;}
a.card p{color:#a08a6b;font-size:13px;line-height:1.5;}
.badge{display:inline-block;background:rgba(20,14,8,.78);border:1px solid rgba(212,154,74,.28);padding:4px 10px;border-radius:999px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#d49a4a;}
</style></head>
<body>
<span class="badge">Experiment 13 · cardboard</span>
<h1 style="margin-top:14px;">Easy Cardboard 3.1 — exploration matrix</h1>
<p class="sub">Quatro demos isoladas, cada uma variando uma dimensao do plugin Geometry Nodes do asset. Renders Cycles 100% headless, pipeline a partir do .blend comprado.</p>
<div class="grid">
  <a class="card" href="wear/index.html"><h2>Wear ⏰</h2><p>6 niveis de desgaste — do papelao novo ao surrado.</p></a>
  <a class="card" href="scale/index.html"><h2>Global Scale</h2><p>7 valores — granulacao fina ate "papelao grosso".</p></a>
  <a class="card" href="corrugation/index.html"><h2>Corrugation</h2><p>Type 0/1 × Direction Mask × Invert.</p></a>
  <a class="card" href="shapes/index.html"><h2>Box Shapes</h2><p>Caixas diferentes via Simple Box Creator.</p></a>
  <a class="card" href="wild/index.html"><h2>Wild combos</h2><p>Box + Wear + Scale + Fibers todos combinados.</p></a>
</div>
</body></html>
'''
with open(os.path.join(ROOT, 'web2', 'index.html'), 'w', encoding='utf-8') as f:
    f.write(INDEX)
print("Wrote web2/index.html (hub)")
