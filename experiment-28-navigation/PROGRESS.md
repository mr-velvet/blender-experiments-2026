# experiment-28-navigation — PROGRESS

Atualizado: 2026-05-30

## Pergunta do experimento

Testar autonomia do agente em: (1) localizar um experimento passado (casa do
BlenderKit editada — grama removida + plano liso), (2) **se orientar por
coordenadas visuais sem visao em tempo real** pra achar as portas da casa, (3)
montar um trajeto de camera entrando por uma porta, cruzando o interior e saindo
pela outra, (4) renderizar isso como video em modo render no Blender, e (5)
exportar um viewer HTML/JS onde o user controla a camera gravada.

Tudo headless (`blender --background --python`), sem o user tocar no Blender.

## Asset / cena de origem

`experiment-21-blenderkit-scene/out/edited/lonely_B_floor.blend` — casa "The
Lonely Outpost" (BlenderKit, Toby Noby), variante B (campo gramado removido,
chao liso `FlatGround`, montanhas/ceu do asset mantidos).

Medidas: bbox casa x[-2.28, 8.32] y[20.99, 31.11] z[-2.17, 3.71]. Centro
(3.0, 26.0). Piso interno z=-1.73. Cabana de **ripas de bambu** (vazada), 2
aberturas nos lados curtos (eixo Y): porta principal + DECK na parede SUL
(-Y, y~21), saida na parede NORTE (+Y, y~31). Passagem reta em x~3.1.

## Como o agente se orientou (o ponto do experimento)

Sem visao em tempo real, substituicao por **render -> analiso -> ajusto**:
- `01_inspect.py` — dump de geometria/bbox (acha footprint, nao a porta).
- `02/02b_orient` — 8 azimutes nivel do olho + topo (le a estrutura).
- `05_facecloseups.py` — 12 closeups girando: **decisivo**, revelou a porta
  dupla + deck na fachada sul e a abertura na norte.
- `10_elevation.py` — elevacao ortografica frontal das fachadas com **regua de
  X sobreposta** -> cravou x~3 das portas. Leitura direta na escala.

### O que NAO funcionou (honestidade tecnica)

Detectores automaticos de coordenada da porta por **raycast** (`04_occupancy`,
`06_doors`, `07_doors2`, `09_find_deck`) deram resultado lixo: casa de ripas
vazadas -> raios "entram fundo" em quase todo lugar -> detector ve porta nas 4
paredes (falso positivo). Abandonados. A coordenada confiavel veio da elevacao
com regua (leitura visual assistida por escala desenhada), nao de raycast.

## Entregas

1. **Video renderizado** (modo render, EEVEE, 1280x720, 30fps, 14s, 420 frames):
   `out/tour/walkthrough.mp4` (5.1MB, libx264). Camera entra pela porta sul
   cruzando o deck, atravessa o interior, sai pela abertura norte. Movimento
   suave (bezier auto, look-ahead via Track-To em Empty animado).
   Script: `11_tour.py`.
   - Gotcha 1: cascas `clouds`/`mist` envolvem a cena -> camera por dentro ->
     frames pretos. Fix: `hide_render` nelas + sol de apoio.
   - Gotcha 2: este build do Blender 5.1 nao expoe `FFMPEG` no enum de saida ->
     renderizo PNG sequence e encodo MP4 com `imageio-ffmpeg` (instalado no py).

2. **Viewer web interativo**: `out/web/index.html` + `house.glb` (4.9MB —
   export cru saia 68MB; reduzi via gltf-transform: Draco + texturas WEBP +
   scale 1024) + `campath.json` (mesmo trajeto, Blender Z-up -> Three.js Y-up).
   Three.js com DRACOLoader, 4 modos: Reproduzir tour (scrub), Orbita livre,
   Andar 1a pessoa (WASD), Reiniciar. Validado abrindo a URL hospedada (v2) em
   browser: GLB carrega, tour roda, zero erro (so 404 de favicon).
   - Gotcha 3: GLB Draco precisa de DRACOLoader no viewer, senao
     "No DRACOLoader instance provided" e a casa nao carrega. Adicionado.

## Links hospedados (GCS / st.did.lu, v2) — abertos e validados em browser

- Viewer:  https://st.did.lu/blender-exp28-navigation/v2/index.html
- Video:   https://st.did.lu/blender-exp28-navigation/v2/walkthrough.mp4

(v1 ficou com GLB de 68MB e, depois, um GLB Draco sem DRACOLoader no viewer
— quebrado. v2 e a boa: GLB 4.9MB Draco + viewer com DRACOLoader. Cache do GCS
e agressivo, por isso a URL nova em vez de sobrescrever v1.)

## Pipeline (scripts/)

01_inspect · 02/02b_orient · 03_floorplan · 04_occupancy · 05_facecloseups ·
06/07_doors(2) · 08_plan_grid · 09_find_deck · 10_elevation · 11_tour ·
12_export_glb. (04/06/07/09 = raycast, ficam como registro do que falhou.)

## Notas de sessao

- Sessao inicial crashou (~11min) por loop de excecao do runtime supercli (EOF
  write) — nao foi erro do experimento. A rodada seguinte recomecou do zero;
  por isso o user viu mensagens "de varios agentes" (sempre o mesmo agente, em
  sessoes efemeras distintas).
- Blender 5.1 obrigatorio (asset so desempacota nessa versao; ver exp-21).
- `agnts-cli` so via caminho absoluto `C:\Users\manu\.local\bin\agnts-cli.cmd`,
  e `post` recebe UM unico argumento entre aspas (here-string multi-arg quebra).

## Proximos passos possiveis

- Render em Cycles (mais fiel/cinematografico, mais lento) pra hero shot.
- Colisao + altura de cabeca no modo "Andar" do viewer (hoje e voo livre).
- Incluir `Landscape` (montanhas) no GLB pra paisagem ao fundo pelas portas.
