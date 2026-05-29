#!/usr/bin/env python3
"""Injeta data.json dentro do index.html (placeholder __DATA__) gerando index_built.html.
Mantem itens sem imagem (image_ok=false) — a galeria os renderiza com placeholder."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
    data = json.load(f)
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
    html = f.read()
html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
with open(os.path.join(HERE, "index_built.html"), "w", encoding="utf-8") as f:
    f.write(html)
total = len(data["free"]) + len(data["paid"])
withimg = sum(1 for t in ("free", "paid") for i in data[t] if i.get("image_ok") is not False)
print(f"index_built.html gerado: {total} cards ({data['free'].__len__()} free + {data['paid'].__len__()} pago), {withimg} com imagem")
