#!/usr/bin/env python3
"""Baixa todas as imagens do data.json localmente em img/, valida que sao imagens
reais (magic bytes), e reescreve data.json com caminhos locais. Cards cuja imagem
nao baixar ou nao for imagem valida sao marcados image_ok=False."""
import json, os, urllib.request, ssl, sys

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

MAGIC = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"RIFF": "webp",  # checa WEBP no offset 8
}

def sniff(data):
    for sig, ext in MAGIC.items():
        if data.startswith(sig):
            if ext == "webp":
                if data[8:12] == b"WEBP":
                    return "webp"
                continue
            return ext
    return None

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return r.read()

def main():
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    for tab in ("free", "paid", "ai"):
        for item in data[tab]:
            url = item["image"]
            if url.startswith("img/"):
                item["image_ok"] = True
                continue
            try:
                raw = fetch(url)
                ext = sniff(raw)
                if not ext:
                    print(f"[FAIL nao-imagem] {item['id']} <- {url[:60]}")
                    item["image_ok"] = False
                    continue
                fn = f"{item['id']}.{ext}"
                with open(os.path.join(IMG, fn), "wb") as out:
                    out.write(raw)
                item["image"] = f"img/{fn}"
                item["image_ok"] = True
                print(f"[OK {ext} {len(raw)//1024}KB] {item['id']}")
            except Exception as e:
                print(f"[FAIL {type(e).__name__}] {item['id']} <- {url[:60]}: {e}")
                item["image_ok"] = False
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    ok = sum(1 for t in ("free","paid","ai") for i in data[t] if i.get("image_ok"))
    tot = sum(len(data[t]) for t in ("free","paid","ai"))
    print(f"\n{ok}/{tot} imagens OK")

if __name__ == "__main__":
    main()
