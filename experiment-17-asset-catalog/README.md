# Experimento 17 — Catálogo de Assets de Geometria

Tarefa de curadoria (não-pipeline): varredura extensiva da web por pincéis e plugins do Blender que **manipulam geometria**, montados num catálogo HTML navegável.

## Resultado
- **105 assets** com imagem real do efeito (39 gratuitos / 66 pagos)
- 11 categorias: Generators, Sculpt/VDM Brushes, Mesh Tools, Geometry Nodes, Hard Surface, Architecture, Terrain/Landscape, Trees/Vegetation, Scatter/Distribution, Cloth/Soft, Destruction/Fracture
- 3 abas: Gratuitos · Pagos · Índice de valores (tabela ordenável por preço/nome/categoria + faixa de preço)
- Categorias em accordions colapsáveis dentro das abas Gratuitos/Pagos
- Cada card: imagem + nome + categoria + preço + link de compra/baixar + link "ver mais"
- Busca por nome/categoria/descrição

**Hospedado:** https://st.did.lu/blender-asset-catalog/v1/index.html

## Método
1. 5 agentes de pesquisa em paralelo varreram Superhive/Blender Market, Gumroad, extensions.blender.org (oficial), GitHub, BlenderKit — divididos por eixo (geo nodes pago, addons free oficiais, sculpt/VDM brushes, sim/destruição/cloth/terrain, hard-surface pago)
2. `validate_images.py` — testou HTTP de cada `image_url` (status 200 + content-type de imagem)
3. `download_images.py` — baixou todas as imagens localmente em `img/` (evita hotlink/CORS/referer quebrando no browser). Asset cuja imagem não baixou = descartado (1 caso: QuickAssembly, placeholder)
4. GIFs gigantes (Reptile VDM 116MB, Sorcar 13MB) reduzidos a 1 frame JPG representativo
5. `index.html` + `data.js` — front auto-contido, dark theme, componentes 100% custom (sem select/scrollbar nativos)
6. Validação visual via Playwright nas 3 abas, deploy GCS, re-validação na URL pública

## Caveats da curadoria
- Superhive e ArtStation têm proteção anti-bot (Cloudflare) — preços desses packs são aproximados de listagens públicas, devem ser confirmados na página de compra. Para esses, a imagem veio de mirror editorial/oficial (BlenderNation, blender-addons.org, site do produto)
- "Name your price" classificado como gratuito (US$ 0)
- Critério: efeito na geometria (gera/deforma/fratura/esculpe malha), não shaders puros

## Arquivos
- `scripts/assets_raw.json` — coleta bruta consolidada e deduplicada
- `scripts/validate_images.py` → `assets_valid.json`
- `scripts/download_images.py` → `assets_final.json` (com caminho local de imagem)
- `data.js` — JSON embutido no front
- `index.html` — catálogo
- `img/` — 105 imagens (gitignored; reproduzível via scripts)
