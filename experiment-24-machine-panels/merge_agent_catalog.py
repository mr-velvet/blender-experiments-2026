#!/usr/bin/env python3
"""Funde itens EXCLUSIVOS do catalogo paralelo (experiment-24-machine-panel-plugins/data.js)
dentro do data.json oficial, convertendo schema e copiando imagens ja baixadas."""
import json, os, re, shutil, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OTHER = os.path.normpath(os.path.join(HERE, "..", "experiment-24-machine-panel-plugins"))

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return re.sub(r"-+","-", re.sub(r"[^a-z0-9]+","-", s)).strip("-")

with open(os.path.join(HERE,"data.json"),encoding="utf-8") as f:
    data = json.load(f)

# nomes ja presentes (normalizados) + alguns aliases
present = set()
for t in ("free","paid","ai"):
    for i in data[t]:
        present.add(norm(i["name"]))
# aliases manuais (mesma ferramenta, nome diferente)
ALIAS = {
    norm("KIT OPS 2 PRO"), norm("DECALmachine"), norm("MESHmachine"),
    norm("Control Console Kit"), norm("Random Flow"), norm("Plating Generator and Greebles"),
    norm("Procedural Sci-Fi Panel Generator"), norm("Discombobulator"), norm("BY-GEN"),
    norm("ND Non-Destructive"), norm("Industrial Structure Generator"),
    norm("Mech Generator"), norm("Sci-fi Panels"),  # joshuabloemer = meu sci-fi panels
    norm("Geometry Nodes Sci-Fi Squares"),
}
present |= ALIAS
# joshuabloemer "Sci-fi Panel Generator" == meu "Sci-fi Panels"
present.add(norm("Sci-fi Panel Generator joshuabloemer"))
present.add(norm("Hard Ops Boxcutter Bundle"))  # ja tenho BoxCutter
present.add(norm("Greeble Generator One-Click"))  # baixo valor, redundante
present.add(norm("KIT OPS 2 FREE"))  # tenho KIT OPS PRO

js = open(os.path.join(OTHER,"data.js"),encoding="utf-8").read()
js = js[js.index("["):js.rindex("]")+1]
cat = json.loads(js)

def fit_label(n):
    return "Alto" if n>=7 else ("Médio" if n>=4 else "Baixo")

added=[]
for c in cat:
    if norm(c["name"]) in present:
        continue
    src_img = os.path.join(OTHER, c["image"].replace("./",""))
    if not os.path.exists(src_img):
        print("[skip sem img]", c["name"]); continue
    sid = slug(c["name"])
    ext = os.path.splitext(src_img)[1]
    dst = os.path.join(HERE,"img", sid+ext)
    shutil.copy2(src_img, dst)
    item = {
        "id": sid,
        "name": c["name"],
        "vendor": "",  # nao tinha no schema do agente
        "price": ("Grátis" if c["is_free"] else f"US$ {c['price_usd']:g}"),
        "url": c.get("product_url") or c.get("more_url",""),
        "image": f"img/{sid}{ext}",
        "category": c.get("category","").replace("Sci-Fi","Sci-fi"),
        "description": c["desc"],
        "differential": c.get("spec_fit_reason",""),
        "spec": fit_label(c["spec_fit"]),
        "spec_note": c.get("spec_fit_reason",""),
        "nl": "Não",
        "auto": "Provável" if c.get("python_api") else "Desconhecido — orientado a interação/biblioteca de peças.",
        "image_ok": True,
    }
    tab = "free" if c["is_free"] else "paid"
    data[tab].append(item)
    added.append(c["name"])

# reordena cada aba por nota (Alto, Medio, Baixo) mantendo estabilidade
order={"Alto":0,"Médio-alto":0,"Médio":1,"Baixo-médio":2,"Baixo":2}
for t in ("free","paid"):
    data[t].sort(key=lambda i: order.get(i["spec"],1))

with open(os.path.join(HERE,"data.json"),"w",encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"adicionados {len(added)}:")
for a in added: print("  +", a)
print("totais:", {t:len(data[t]) for t in ('free','paid','ai')})
