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

## Pendente / proximos passos (aguardando decisao do user)
- **Adensar layout**: comodos de 6x4.5m com mobilia encostada nas paredes ->
  centro vazio. Nao e falta de asset (25/27 usados); e que os comodos sao
  grandes. Para adensar: encolher comodos OU reposicionar mobilia pro centro
  OU baixar mais assets pequenos (tapetes, quadros, objetos de mesa). Exige
  re-montar a casa. NAO feito ainda — depende de o user querer.
