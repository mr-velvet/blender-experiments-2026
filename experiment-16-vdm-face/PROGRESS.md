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

## Estado atual (melhor resultado)
`scripts/27_assemble.py` → `output/asm_a2.blend` + renders:
- `output/asm_a2_viewport_tilt.png` (print viewport, sem Cycles) ← melhor
- `output/asm_a2_front.png`, `asm_a2_3q.png` (Cycles)
Rosto reconhecível: 2 olhos (b25) + nariz (b28) + boca (b15). Layout via ASM_PLAN
(env var JSON ou _default no script).

## A fazer
- Suavizar o degrau na borda dos discos das features (shrinkwrap/blend em vez de
  join cru) — hoje aparece sombra dura acima dos olhos.
- Refinar proporções / testar outros olhos.
- FASE 2: pintar rosto em asset gratuito (download de modelo + carimbar nas faces).

## Scripts-chave
- 12_catalog_clean / 13_measure — identificação dos brushes
- 25_face_final — rosto num plano único (unprojected_radius); tem o problema do (3)
- 27_assemble — rosto por objetos rotacionados (ABORDAGEM BOA)
- 28_viewport_shot — print de viewport sem render
