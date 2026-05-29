#!/usr/bin/env python3
"""Injeta data.json dentro do index.html (placeholder __DATA__) gerando index_built.html."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"data.json"),encoding="utf-8") as f:
    data = json.load(f)
# so cards com imagem ok
for t in ("free","paid","ai"):
    data[t] = [i for i in data[t] if i.get("image_ok")!=False]
with open(os.path.join(HERE,"index.html"),encoding="utf-8") as f:
    html = f.read()
html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
with open(os.path.join(HERE,"index_built.html"),"w",encoding="utf-8") as f:
    f.write(html)
print("index_built.html gerado:", sum(len(data[t]) for t in ("free","paid","ai")), "cards")
