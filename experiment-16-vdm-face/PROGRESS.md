# experiment-16-vdm-face — PROGRESS

Última atualização: 2026-05-27

## Objetivo (literal do user)
Usar os pincéis VDM de rosto humano (pack "Human Face VDM") para DESENHAR um
rosto — 2 olhos, 1 nariz, 1 boca — numa geometria (cubo/plano), via Blender
headless, e mandar fotos. Fase 2 futura: pintar rostos em assets gratuitos.

## Pack de brushes
`C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\Human Face VDM Blender 4.3\Saved\Brushes`
30 brushes `Human Face VDM NN.asset.blend`. São VDM (vector displacement) via
textura EXR. sculpt_tool=DRAW, stroke_method=ANCHORED, map_mode interno=AREA_PLANE.

## Identificação dos 30 (por medição do deslocamento dos vértices, script 13)
- BOCAS: 15, 16, 17, 18 (cavidade côncava, zmin ~ -0.34)
- OLHO: 25 (globo + pálpebra, relevo raso ~0.10) — único olho bom do pack
- NARIZES: 1-14, 27-30 (convexo puro, projeção forte)
- ORELHAS: 19, 21, 22, 23, 24 (convexo + concha côncava lateral)

## Mecânica que FUNCIONA
- Carimbo headless: rodar `blender --python script.py` (SEM --background, pra ter
  viewport/GUI), build dentro de `bpy.app.timers` + `quit_blender` no fim.
- Carimbo: `bpy.ops.sculpt.brush_stroke` ANCHORED drag-zero, com temp_override da
  view3d, em vista TOP-DOWN (rv3d.view_rotation=(1,0,0,0)) num PLANO subdividido.
- Escala da feature: setar `tool_settings.unified_paint_settings.unprojected_radius`
  (raio em unidades de mundo). O `size` em px do stroke NÃO controla de forma confiável.
- Visualização do relevo: SÓ fica legível com sombra. Viewport SOLID puro mostra
  liso. Opções: (a) Cycles 24-64 samples + luz SUN rasante (script 07/12), (b)
  viewport SOLID com show_shadows+cavity (script 28), (c) matcap.

## LIMITES REAIS descobertos (não são bugs meus — são da ferramenta/pack)
1. Carimbar na face VERTICAL de um cubo via headless NÃO desloca visível — o ray
   do sculpt atravessa o cubo. Solução: usar PLANO top-down (user autorizou plano).
2. Rotacionar o stamp VDM via API (texture_slot.angle OU roll da view) ENCOLHE a
   feature pra um ponto. Não dá pra orientar pelo pincel.
   → Solução: carimbar cada feature ISOLADA (tamanho cheio), recortar em disco,
     ROTACIONAR + posicionar o OBJETO, e juntar (join). Script 27.
3. Carimbar vários brushes em sequência no MESMO objeto: o 1º define a escala e os
   seguintes encolhem. Por isso a abordagem por objetos isolados (27) é a robusta.
4. As bocas, em roll 0 no plano, saem VERTICAIS (orientação natural). Giro via objeto.

## Estado atual (melhor resultado) — 2026-05-27
`scripts/33_cube_final.py` → rosto plantado numa FACE de um CUBO (pedido literal do
user). Parametrizavel por env: EYE_ROT (graus olho), MOUTH_BRUSH, MOUTH_ROT, TAG.
- `output/cube_a2cube_front.png` / `_3q.png` / `_side.png` (render Cycles)
- `output/cube_a2cube_vp_3q.png` (print viewport solid+cavity, sem Cycles)
- `output/cube_a2cube.blend`
Receita aprovada (do asm_a2): olho b25 rotz=0, nariz b28 rotz=115, boca b15 rotz=-78.
LUZ suave (angle 0.5-0.8) — luz rasante dura estraga os olhos. Smooth 0.5/8.
Plantio no cubo: placa XY rotaciona +90 em X (relevo +Z -> -Y) e cola na face -Y.

### Comparativos gerados (em output/ e output/orient_diag/)
- `catalog30_top.png` — TODOS os 30 brushes top-down, luz rasante (reidentificacao)
- `eye_compare.png` (orient_diag) — olho b25 isolado 0/45/90deg
- `cube_eye_compare.png` — olho 0/45/90deg JA NO ROSTO no cubo (mais util)
- `mouth_compare_3q.png` (orient_diag) — bocas 15/16/17/18 em 3/4

### Achados desta rodada
- Olho b25 isolado: 90deg = horizontal anatomico. MAS no rosto montado no cubo
  (placa rotacionada 90 em X), 0deg le mais natural. A rotacao da placa inverte a
  percepcao. → user precisa escolher o angulo (perguntado).
- "Bocas" 15-18 NAO sao bocas classicas (sem 2 labios+sulco), sao projecoes tipo
  labio. b15 usado. user pode indicar outro brush do catalogo.
- FALLOFF radial no Z pra suavizar bordas: TESTADO, PIOROU (sombras piores). Mantido
  recorte simples em disco. Bordas serrilhadas dos olhos = defeito conhecido tolerado.
- Crash EXCEPTION_ACCESS_VIOLATION no quit_blender e cosmetico — todos os renders
  saem antes. Rodar 1 brush/feature por processo evita crash por acumulo de estado.

## RODADA 2026-05-27 (tarde) — esculpir na MESMA malha (resolveu o "furo")
User apontou: olhos/boca estavam CHAPADOS e "furando a malha" (efeito do approach de
placas recortadas + join). Pediu pra esculpir DIRETO numa malha subdividida.

`scripts/34_sculpt_unified.py` — NOVO approach, resolveu o problema central:
- 1 plano denso (subsurf SIMPLE lvl9 = 263k verts), entra em SCULPT mode UMA vez,
  carimba os 4 brushes em coords diferentes da MESMA superficie. VDM desloca a massa
  existente pra fora -> relevo CONTINUO, sem furo, sem recorte, sem degrau.
- Encolhimento resolvido: reseto `unprojected_radius` antes de cada stroke.
- Olho a 90deg sem encolher: giro a MALHA 90deg em Z em torno do pivot do olho antes
  do stroke e desfaco depois (girar textura/view encolhia o stamp).
- Resultado: `output/sc_v1_*` (vp_3q, vp_front, vp_side, r_3q, r_front, .blend).
  Olhos amendoa horizontal corretos, nariz protrui, tudo brotando da massa.

LIMITE confirmado da BOCA: testei b15/b16/b17 (sc_v1/v3/v4) — todas saem como
projecao VERTICAL de labio. O pack NAO tem boca horizontal classica.
Comparativo: `output/mouth_compare_sculpt.png`. Aguardando user decidir tratamento.

## RODADA 2026-05-27 (noite) — outros brushes + mais protrusao
User pediu: testar outras bocas/olhos/narizes e deixar olhos+boca mais saltados.

`scripts/35_candidates.py` — carimba lista de brushes isolados e renderiza em 3/4
(perfil revela protrusao). Env: CAND_LIST (csv), CAND_FLIP, CAND_RADIUS, CAND_TAG.
Rodar 1 brush por processo (sem --background) senao crasha. Saidas em output/cand/.
Mosaicos: output/cand/eyes_mosaic, noses_mosaic, mouths_mosaic.

`scripts/36_sculpt_protrude.py` — rosto no cubo (herda 34) PARAMETRIZAVEL:
EYE_BRUSH/NOSE_BRUSH/MOUTH_BRUSH, PROTRUDE (mult Z global do relevo+),
EYE_PROTRUDE/MOUTH_PROTRUDE (mult Z por regiao), EYE/NOSE/MOUTH_RADIUS, MOUTH_FLIP
(inverte o Z negativo da faixa da boca -> boca salta em vez de afundar), TAG.
Combos gerados: output/sc_comboA/B/C_* . Melhor = comboC (olho b25 prot1.4,
nariz b28 carnudo, boca b17 flip).

### Achados duros desta rodada (LIMITES do pack, confirmados visualmente)
- PROTRUSAO resolvida: multiplicar Z>0 da malha apos esculpir. 1.4-1.5 bom, 2.0 vira bola.
- OLHOS sem variedade: b21/b25/b26 sao o MESMO olho (globo+palpebra) com variacao
  minima. b25 e o melhor. O pack nao tem outros formatos de olho.
- BOCA: brushes 15-18 sao CONCAVOS (zmin ~-0.34) -> afundam a malha, por isso pareciam
  furo/sem volume. Flip (inverter Z) faz saltar, mas vira protuberancia/bola, nao boca
  de 2 labios. O pack NAO tem boca de verdade. Teto confirmado.
- O pack inteiro e majoritariamente NARIZES e ORELHAS. Forte em nariz, fraco em olho,
  sem boca.

## RODADA 2026-05-27 (fim) — CUBO DE OLHOS + GLOBO OCULAR (so propriedade do pincel)
User apontou (correto): a "protrusao" exagerada do olho na rodada anterior NAO era do
pincel — o script 36 multiplicava v.co.z e invertia Z na boca (flip). Isso e mexer na
malha, PROIBIDO. REGRA TRAVADA agora: so carimbo VDM + so propriedades do pincel.
Zero manipulacao de vertice pos-carimbo.

Pedido novo: cubo com olho em CADA face, cada face variando PROPRIEDADE do pincel; por
uma ESFERA (globo ocular) no meio de um olho, do tamanho do pincel; varios cubos.

`scripts/37_inspect_eye.py` — dump das props do brush b25. Achados (medidos):
- unprojected_radius -> TAMANHO do olho. funciona (0.36..0.58 testado).
- strength -> INTENSIDADE/profundidade do relevo. funciona (1.0 -> z0.105; 0.55 -> z0.032).
- height (param VDM) -> NAO reescala (image-based VDM ignora). 0.40 e 0.62 dao mesmo z.
- rotacao do olho: giro a MALHA antes do carimbo (rigido) e desfaco. 90deg=horizontal.
- TETO de relevo do pincel ~z0.10 no raio cheio. Nao da "mais saltado" sem inflar a
  malha (proibido). So da mais RASO via strength. Reportado ao user.

`scripts/38_eye_cube.py` — CUBO com olho VDM b25 carimbado em cada uma das 6 faces.
Approach: 1 placa densa (subsurf simple lvl8) por face, sculpt mode top-down, 1 carimbo,
depois planta a placa orientada na face do cubo (transform_apply). Variacao por face =
(radius, strength, eye_rot). ESFERA(s) globo ocular: acho o centro real da concavidade
do olho (vertice mais baixo perto da origem), transformo pra mundo via matrix_world da
placa, posiciono a esfera (raio ~0.38*raio_olho) aflorando na palpebra. Env: TAG,
SPHERE_FACES (csv de indices 0-5) ou SPHERE_FACE.
- Cubo 1 (TAG=eyecube, SPHERE_FACE=1): `38_eyecube_r_eyeball.png` (close: olho+globo
  encaixado PERFEITO), `_r_3q.png`, `_vp_3q/front/top.png`, `.blend`.
- Cubo 2 (TAG=eyecube2, SPHERE_FACES=1,2,4): 3 globos em 3 faces, tamanhos distintos.
  `38_eyecube2_r_3q.png` etc.
RESULTADO: olho = 100% pincel VDM, zero deformacao manual. Esfera = unico objeto extra,
encaixada no centro real do olho. Pedido cumprido literalmente.

## A fazer (aguardando user)
- Fechar com combo C, OU tentar boca por 2 carimbos (labio sup+inf), OU FASE 2.
- FASE 2: pintar rosto em asset gratuito (download de modelo + carimbar nas faces).

## Scripts-chave
- 12_catalog_clean / 13_measure — identificação dos brushes (antigo)
- 27_assemble — rosto por objetos rotacionados num PLANO (gerou o asm_a2 aprovado)
- 31_single_feat — carimba 1 brush isolado, parametrizavel (FEAT_BRUSH/ROT/CAM/OUT)
- 33_cube_final — ROSTO NO CUBO por placas recortadas (approach antigo, gerava furo)
- 34_sculpt_unified — ROSTO esculpido na MESMA malha (atual, resolveu o furo). Env:
  MOUTH_BRUSH, MOUTH_ROT, TAG.
