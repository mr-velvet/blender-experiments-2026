# Proposta — bake do Easy Cardboard 3.0 pra GLB (geometria + textura)

> Doc pra retomar numa janela de contexto nova. Resume o que JÁ FUNCIONA, o que
> NÃO funciona, e o que PRECISA ser investigado de verdade — sem chutes.

## O que está PROVADO que funciona

1. **Geometria**: Easy Cardboard 3.0 gera geometria real headless (solidify +
   edge split 3D + displacement + wear via Smart Solidify 2.0). Confirmado:
   945v→2033v. 17 presets documentados em `output/presets/PRESETS.md`.
   Favoritos do user: `15_used_box` e `04_wear_10`.

2. **Shader EC vivo no viewport (via MCP)**: a corrugação aparece CERTA — só
   nas faces de quina expostas, faces planas ficam lisas. Screenshot real
   confirmou. **Esse é o look-alvo.** (Era o `preview` MCP antes do bake.)

3. **Bake roda** (Cycles, headless ou MCP). Gera os 3 PNGs (color/normal/rough).

## O que NÃO funciona

**Depois do bake + swap pro Principled BSDF, a textura aplica errada**: faces
planas saem com listras de corrugação que deviam estar só nas quinas. Testado
em 3 variações, todas com o mesmo defeito:

- **A** — bake na UV nativa do plugin (alongada u=0..17), textura 17408×1024,
  GLB 36MB. Errado.
- **B** — escalar UV pra [0,1], bake 2048², GLB 5.4MB. Errado.
- **C** — 2 UVs (UVMap pra leitura do shader + UV_BakeTarget smart_project pra
  escrita), GLB 2.8MB. Errado (pior).

## ⚠️ Honestidade sobre o diagnóstico

**Não sabemos a causa raiz.** As "explicações" dadas durante as tentativas
(foi o swap / foi o naming / foi o active_render) foram chutes pós-fato, não
verificados. Não repetir esse padrão na próxima janela: **medir antes de
afirmar.**

## A nota oficial do autor (literal)

> "EASY CARDBOARD IS A TEXTURE BASED MODIFIER. IT DOES NOT CREATE CORRUGATION
> GEOMETRY. IT SOLIDIFIES YOUR OBJECT AND APPLIES TEXTURE TO IT. SO JUST BAKE
> YOUR TEXTURES AND - GAME READY! EASY CARDBOARD 3 CURRENTLY REQUIRES A UV MAP."

O autor afirma que bake é o caminho e funciona. Então o erro é **nosso setup**,
não o plugin. A pergunta não respondida: **qual setup de UV/bake o autor
assume** quando diz "just bake"?

## Hipóteses NÃO testadas (pra investigar com método na próxima janela)

Cada uma deve ser CONFIRMADA por medição, não assumida:

1. **UV boa ANTES do EC.** "REQUIRES A UV MAP" pode significar que o EC quer
   uma UV sã de entrada (smart_project em [0,1]) ANTES de ser aplicado, não a
   UV alongada que o Simple Box Creator cospe. (Caminho D — estava pra rodar
   quando paramos. `scripts/15_pipeline_D.py`.)

2. **O EC tem botão/operador de bake próprio.** Muitos addons preparam o bake
   internamente. Verificar se há `bpy.ops` registrado pelo addon, ou um node de
   "bake output" dentro dos 44 node groups. NÃO foi verificado.

3. **O `Direction Mask` é puramente posicional (normal/tangent), não bakeável
   em UV.** Se o mask lê a NORMAL da face em runtime (não a UV), então nenhuma
   textura UV-mapeada vai reproduzir — precisaria bakear em world/object space,
   ou aceitar que esse efeito específico não exporta. INVESTIGAR o node tree
   `📦 Easy Cardboard 3.0` → quais inputs o direction mask realmente usa.

4. **Triplanar.** A nota diz "TRIPLANAR OPTION WILL COME OUT SOON" — sugere que
   o EC HOJE depende de UV de forma frágil. Talvez a fidelidade dependa de uma
   projeção que só o shader vivo faz.

5. **Versão do Blender.** O .blend do asset NÃO abre em 4.3 ("from a newer
   version"). 4.4 local está corrompido. Só temos 5.1. O autor pode testar em
   5.2+. Não dá pra descartar regressão de bake do 5.1 sem outra versão.

## Método proposto pra próxima janela (não chutar)

1. **Isolar o que o direction mask usa.** Abrir `📦 Easy Cardboard 3.0`,
   rastrear o input do nó que decide corrugação on/off. Se for UV → bake em UV
   resolve. Se for Normal/Geometry → bake em UV NUNCA vai resolver, e a resposta
   pra "por que vem cagada" é essa.

2. **Antes de qualquer bake novo, validar a UV visualmente**: exportar a UV
   layout como PNG e comparar com onde a corrugação aparece no shader vivo. Isso
   mostra se a UV alinha com o efeito ou não — responde a causa raiz por
   observação, não por chute.

3. **Só depois disso** escolher o caminho de bake. Possivelmente é o D, mas
   confirmar com a medição do passo 1/2 antes de rodar.

## Arquivos relevantes

- `scripts/12_full_pipeline.py` — caminho A (UV nativa alongada)
- `scripts/13_pipeline_B.py` — caminho B (UV escalada [0,1])
- `scripts/14_pipeline_C.py` — caminho C (2 UVs)
- `scripts/15_pipeline_D.py` — caminho D (UV smart antes do EC) — NÃO RODADO
- `output/mcp_bake/` — todos os GLBs/PNGs/previews das tentativas
- `output/mcp_bake/bake_state.blend` — estado MCP salvo (53MB, com EC aplicado)
- `output/presets/PRESETS.md` — 17 presets de geometria (essa parte funciona)
- página do asset: https://superhivemarket.com/products/easy-cardboard
  (Cloudflare bloqueia WebFetch — precisa screenshot manual do user)

## Limite de competência do agente (registrar e respeitar)

O gargalo real NÃO é o bake. É a UV. E UV bom nesta peça exige **decisão sobre
geometria**: onde marcar seams, como abrir cada island, como orientar a island
na direção do corrugado.

**O agente não faz decisão espacial sobre geometria.** Não decide onde cortar,
não avalia se uma UV "ficou boa", não localiza a região corrugada num layout
de UV. Operações `bpy.ops.uv.*` (smart_project, cube_project) rodam, mas são
heurística cega — não resolvem porque não têm intenção direcional. O loop de
TD (marcar seam → olhar → ajustar) o agente não fecha sozinho.

Isso não é "talvez com critério X". É limite. Não tentar contornar com pipeline
nova de bake — já foram 4 (A/B/C/D), todas falham pela mesma raiz: UV ruim de
entrada.

## Único caminho com chance real: addon de auto-unwrap de produção

Transforma "decidir seams" (agente não faz) em "rodar ferramenta + validar
saída" (agente faz). Candidatos a avaliar — NÃO avaliados ainda:

- **Ministry of Flat** — auto-unwrap total sem marcar seam, padrão produção,
  tem CLI headless. Provável melhor fit.
- **RizomUV** — padrão de estúdio, headless/scriptável, pago.
- **Zen UV** (~$30) — auto-seam por ângulo + orientação automática, addon Blender.
- **TexTools** (free) — retificar/orientar, meio-termo.
- UV-Packer (free) — só empacota, NÃO decide seam. Não serve.

Critérios pra avaliar cada um: (1) decide seam sozinho, (2) roda headless via
CLI/Python, (3) preserva/controla orientação direcional da island (o corrugado
precisa), (4) preço.

## Resumo de uma linha

Geometria: ✅ resolvido. Bake: roda. UV: ❌ é o bloqueio, exige decisão
geométrica que o agente não faz. Próximo passo: avaliar addon de auto-unwrap
(Ministry of Flat / RizomUV / Zen UV), não tentar mais pipeline de bake.
