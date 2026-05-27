# experiment-15-house-scene — PROGRESS

Atualizado: 2026-05-26

## Pedido do user

"Monta uma cena, uma casa com assets gratuitos achados na internet. Qualquer
comodo. Quanto mais da casa montar, melhor. Nao precisa ser do mesmo pacote.
Quero ver capacidade de distribuir os itens e montar os espacos dentro de uma
casa em 3D no Blender. Manda imagens."

O experimento testa: **deliberacao + busca/escolha de assets gratis + download
automatico + normalizacao de escala + distribuicao coerente em multiplos
comodos + render** — tudo headless, sem o user tocar no Blender.

## O que foi feito

### Assets (CC0 PolyHaven, via API HTTP, sem login)
27 modelos baixados + 2 texturas PBR (piso de madeira, parede bege).
Manifest em `assets/_manifest.json`. 25 dos 27 usados na cena.
Nao usados: `WoodenChair_01`, `wooden_bowl_01`.

### Casa (build_house.py)
Shell parametrico 13x9m, pe-direito 2.8m, SEM teto (pra ver de cima).
4 comodos divididos por paredes com vaos de passagem:
- SALA (X<0,Y<0): sofa, poltrona, mesa de centro, console+TV, estante, planta, vaso, lustre
- COZINHA/JANTAR (X>0,Y<0): mesa redonda + 4 cadeiras, jogo de cha, fogao, estante metalica, panela, luminaria pendente
- QUARTO (X<0,Y>0): cama, criado-mudo + abajur, armario, planta
- ESCRITORIO (X>0,Y>0): escrivaninha, cadeira, abajur, garrafas de vinho, sofa de leitura

Cada asset normalizado de escala (alguns vinham gigantes) e assentado no chao
via bounding-box (scene_lib.place / place_on).

### Render (render_views.py)
Cycles, 160 samples, 1700x1080, AgX. 7 vistas:
3 overviews (sw, se, top) + 4 closes dollhouse por comodo.

## Pipeline (scripts/)
- download_assets.py / download_textures.py — baixam da API PolyHaven
- scene_lib.py — biblioteca: import gltf+handle, bbox, place/place_on, PBR, camera, luz, render
- build_house.py — monta a casa + salva house.blend
- render_views.py — reabre o blend e renderiza as vistas
- inspect_dims.py / diag_layout.py — diagnostico

## Historico de problemas e fixes

### 2026-05-26 sessao 1 (timeout)
Montou a casa, salvou house.blend (44MB), gerou 7 renders. O relatorio de
timeout sugeriu travamento, mas o trabalho principal JA estava salvo — o
timeout pegou re-execucao depois do save.

### 2026-05-26 sessao 2 (fix cameras)
PROBLEMA: os 4 closes de comodo estavam inuteis — camera na borda externa,
baixa, com a parede entre camera e comodo. Sala/quarto so mostravam parede.
FIX: recalibrei pra vista dollhouse — camera alta (4.7m, acima das paredes de
2.8m) no canto externo do comodo, olhando pra baixo num angulo picado, lente
24mm. Re-renderizei. Closes ficaram bons (comodo inteiro visivel por cima da
parede).

## Estado atual
- house.blend: OK, auditavel
- 7 renders: OK em output/renders/ (3 overviews + 4 closes corrigidos)

### 2026-05-26 sessao 3 (fix lustre + escritorio + curadoria de adensamento)
PROBLEMA 1: lustre da sala (Chandelier_01) pousava EM CIMA da mesa de centro
em vez de pender do teto. Causa: place(on_floor=False, z_offset=2.0) movia a
ORIGEM do handle pra 2.0, nao o topo do bbox. Como o lustre nao tem teto pra
ancorar e a origem ficava baixa, ele assentava na mesa.
FIX: novo helper scene_lib.hang_from_ceiling(handle, x, y, ceiling_z) que
encosta o TOPO do bbox no pe-direito e deixa o corpo pender. Aplicado nas 2
luminarias de teto (Chandelier_01 + modern_ceiling_lamp_01).
PROBLEMA 2: escritorio espalhado. FIX leve: sofa de leitura aproximado do
conjunto escrivaninha (x=3.0,y=3.4,rot=200).
Casa rebuildada (house.blend 14:53). Render da sala revalidado.

## Curadoria de adensamento (opcao b — assets pequenos CC0 PolyHaven)
Pesquisados via API. NAO existe rug/carpet no PolyHaven. Selecionados:
- SALA: throw_pillows_01, book_encyclopedia_set_01, ceramic_vase_01,
  fancy_picture_frame_01, mantel_clock_01
- COZINHA: wooden_bowl_01, food_apple_01, food_pears_asian_01, metal_jug,
  wicker_basket_01
- QUARTO: alarm_clock_01, decorative_book_set_01, potted_plant_02,
  wooden_stool_01
- ESCRITORIO: book_encyclopedia_set_01, brass_candleholders, ceramic_vase_02,
  wooden_lantern_01
Lista em download_assets.py (DENSIFY). Baixar + posicionar quando user
confirmar opcao (b).

## Pendente / proximos passos (aguardando decisao do user)
- **Adensar layout**: comodos de 6x4.5m com mobilia encostada nas paredes ->
  centro vazio. 4 caminhos oferecidos ao user: (a) encolher comodos, (b)
  baixar assets pequenos [RECOMENDADO, curadoria acima pronta], (c) reagrupar
  em ilhas centrais, (d) deixar como esta. Aguardando letra.
