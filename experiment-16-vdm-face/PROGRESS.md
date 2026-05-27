# experiment-16-vdm-face — PROGRESS

Última atualização: 2026-05-26

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

## A fazer (aguardando user)
- Confirmar angulo dos olhos (0/45/90) e se troca o brush da boca.
- Suavizar serrilhado das bordas dos olhos via shrinkwrap (se user quiser).
- FASE 2: pintar rosto em asset gratuito (download de modelo + carimbar nas faces).

## Scripts-chave
- 12_catalog_clean / 13_measure — identificação dos brushes (antigo)
- 27_assemble — rosto por objetos rotacionados num PLANO (gerou o asm_a2 aprovado)
- 31_single_feat — carimba 1 brush isolado, parametrizavel (FEAT_BRUSH/ROT/CAM/OUT)
- 33_cube_final — ROSTO NO CUBO, versao atual (EYE_ROT/MOUTH_BRUSH/MOUTH_ROT/TAG)
