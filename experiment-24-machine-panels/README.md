# Experimento 24 — Levantamento: plugins de "máquinas & painéis"

**Tipo:** curadoria/levantamento (não experimento de pipeline). Passo prévio pedido pelo user antes de escolher o que de fato implementar.

## Pedido do user
Encontrar plugins do Blender (grátis e pagos) pra criar **coisas que parecem máquinas** — painéis com botões, alavancas, mostradores. Foco no caso de uso: **passar uma especificação** (descrever um painel e suas partes móveis) e o plugin **gerar a geometria base** pra incorporar num asset. Entregar relatório + mini-galeria HTML com aba grátis/aba paga, card por plugin com imagem, descrição e diferencial; clicar no card mostra detalhe.

## Método
4 agentes de pesquisa em paralelo (Superhive/Blender Market, Gumroad/ArtStation, extensions.blender.org+GitHub, geo-nodes+IA text-to-3D) → ~50 candidatos brutos → dedup → 3 agentes validando 1 imagem REAL por finalista (HTTP 200 + magic bytes, sem inventar padrão de CDN) → download local das 28 imagens (`download_images.py`) → galeria HTML custom.

**Critério-chave aplicado em cada card:** nota "spec → geometria" (Alto/Médio/Baixo) = quão perto chega de "você descreve/parametriza e ele gera o painel mecânico". Também marcado: aceita linguagem natural? (`nl`), dá pra dirigir headless via Python? (`auto`).

## Resultado
44 plugins/ferramentas, 3 abas (ordenadas por nota spec→geo):
- **Grátis (17):** Discombobulator (nativo), Tissue (nativo), BoltFactory (nativo), Spaceship Generator (nativo a1studmuffin), Sci-fi Panels (MIT), Simple Sci-Fi Panel (maxmax), RandoMesh, Scifi Panel 23-styles, BY-GEN, ND, Mech Generator, Industrial Structure Generator, GeoPipes, Pipes Generator (bruchansky), Piperator, GridBreaker, JMesh Tools
- **Pago (21):** Random Flow, Plating Generator, Procedural Sci-Fi Panel (Pamir Bal), Pipe Systems Generator, SynthGen V1, NanoMesh, Platform Generator, Spaceship Generator, KIT OPS 2 PRO, Control Console Kit, Cablerator, Greeble Generator, Mechanical Greeble Master Pack, Industrial Kitbash V3, Fluent, BoxCutter, MESHmachine, DECALmachine, Sci-Fi Squares, Construction Lines, 110 Sci-Fi Panels Kitbash
- **IA · texto→3D (6):** 3D-Agent, Sloyd, Hyper3D Rodin, Meshy 6, Tripo v3.1, Hunyuan3D

> Nota: durante a pesquisa, um dos agentes paralelos montou um segundo catálogo independente (32 itens) com itens da cauda do nicho que a minha lista não tinha (SynthGen, BoltFactory, Cablerator, geradores de pipe, GridBreaker, NanoMesh, etc). Em vez de descartar, fundi os exclusivos na galeria oficial (`merge_agent_catalog.py`) e removi a pasta duplicada — resultado: 28 → 44 itens.

## Conclusão do levantamento (pra deliberar)
- Nenhum plugin de marketplace aceita **linguagem natural** — todos são paramétricos ou bibliotecas de kitbash.
- "Descrevo em texto → sai painel" só existe na aba **IA**, com ressalva de topologia (malha densa/triangulada que pede retopo). Os mais promissores pro caso do user: **3D-Agent** (gera + escreve Python no Blender) e **Sloyd** (modo template = malha limpa).
- Caminho mais sólido hoje pra "spec → geometria limpa de painel": os de nota **Alto** baseados em Geometry Nodes / operadores Python (Sci-fi Panels, Plating Generator, Random Flow, Tissue) — também os mais automatizáveis headless nesta workspace.
- Pra "painel de controle literal com botões/alavancas/mostradores prontos": **Control Console Kit** (biblioteca de peças), montável por script.

## Honestidade
- 28/28 imagens baixadas e validadas como imagem real. 2 são representação do efeito (não card exato do produto), marcado no detalhe: Mechanical Greeble Master (thumbnail do canal do vendor) e Sci-Fi Squares (tutorial de terceiro mostrando o mesmo efeito) — Superhive/ArtStation bloqueiam fetch.
- Preços de packs em portais anti-bot são aproximados (confirmar na página).
- Nenhum plugin foi instalado/testado ainda — é levantamento. As notas `auto` (headless via Python) são estimativas baseadas na arquitetura (geo-nodes/operadores vs modais), a confirmar no experimento real.

## Arquivos
- `data.json` — dataset (fonte única)
- `index.html` — galeria com placeholder `__DATA__`
- `build.py` — injeta data.json → `index_built.html`
- `download_images.py` — baixa+valida imagens em `img/`
- `img/` — 28 imagens locais

## Hospedado
- v2 (44 itens, atual): https://st.did.lu/blender-exp24-machine-panels/v2/index.html
- v1 (28 itens, inicial): https://st.did.lu/blender-exp24-machine-panels/v1/index.html
