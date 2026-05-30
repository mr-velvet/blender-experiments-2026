# experiment-30-grass-soil-variants — PROGRESS

Atualizado: 2026-05-30

## Pedido do user

A partir da cena da casa com capim (exp-29), gerar VARIAS variantes em paralelo
de **grama/mato alto + solo** em volta da casa, com assets free (BlenderKit /
internet), mantendo acesso livre (corredor das portas). User fora por horas ->
autonomia total.

## Estrategia descoberta (a sacada do experimento)

Os assets de "grama/wild grass/weed" do BlenderKit sao BAIXOS (7-26cm) — feitos
pra SCATTER (instanciar milhares -> gramado), nao pra escalar como touceira
alta. Só pampas (exp-29, 2.65m) e bambu (4.1m) sao altos de verdade.

Logo, a abordagem que funciona e DUAS CAMADAS:
- **ground cover**: scatter denso de grama baixa cobrindo o terreno -> vira o
  "solo gramado" de verdade (resolve o pedido de "solo" melhor que textura plana)
- **tall layer**: touceiras altas (pampas/bambu) esparsas por cima -> o "mato alto"

Motor: `06_make_variant.py` (recentra/amplia terreno, 2 camadas, instancias
LINKED, corredor das portas preservado, material de solo fosco por baixo,
config via JSON).

## Assets baixados (headless real, confirmados no disco)

BlenderKit, via pipeline exp-21: Wild Grass Animated (h0.14, scatter),
High grass clump (h0.07), Wild Grass with clover (h0.26), Simple Bamboo (h4.1),
Weed plant (h0.08). + pampas do exp-29.
Solo PolyHaven: a API /assets e /files retornou 0/403 nesta sessao (bloqueio
temporario). Contornado usando grama rasteira como cobertura de solo + material
fosco — ficou melhor que textura plana.

## Variantes geradas (todas com render aereo+eye, validadas por pixel)

- **V2 wildgrass+pampas** (2641 cover + 201 pampas): OTIMA, a melhor. Campo
  gramado denso + plumas altas.
- **V3 bamboo** (2641 cover + 102 bambu): bambuzal. RESSALVA: o mesh do bambu
  free inclui um torrao de terra/raiz colado na base (nao e objeto separavel;
  removi o vaso de pedra 'stone.458' com sucesso, mas o torrao e parte do mesh
  plant.bamboo). Aceitavel mas nao perfeito.
- **V4 clover+pampas** (cover trevo + pampas esparso): prado florido.
- **V5 wild_dry** (3894 cover + 306 pampas): o mais denso (4200 plantas), campo
  selvagem alto, solo seco.

Baseline V1 (so pampas) preservado em exp-29/out/canefield_baseline.blend.

## Disciplina (licao das rodadas anteriores, aplicada)

Conferi CADA asset no disco antes de plantar, CADA render por pixel antes de
afirmar, e NUNCA encadeei sobre output nao verificado. Quando o V3 saiu com
pedras, parei e diagnostiquei por codigo (STONES_IN_SCENE=0) em vez de afirmar
que estava bom ou insistir cego — descobri que o torrao e do mesh, e reportei a
limitacao honestamente em vez de fingir resolver.

## Scripts

01_search_plants · 02_search_soil · 03_download_plants · 04_preview_all ·
05_download_soil · 06_make_variant · 07_render_variant · 08_inspect_bamboo ·
run_variant.ps1.

## Pendente (pro user escolher)

- Qual variante vira a "oficial" pra fechar walkthrough + viewer web.
- Possivel: combinar (ex: V5 densidade + cor do V2), ou misturar especies.
- Solo PBR PolyHaven quando a API destravar (opcional, ja esta bom com grama).

## Notas

- Reusa bl_config_51 + api_key do exp-21. Blender 5.1. Renders saem .jpg.
- canefield_baseline.blend = exp-29 preservado, como o user pediu.
