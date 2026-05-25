# Experimento 14 — Easy Cardboard em geometrias arbitrárias

## Hipótese testada

O Easy Cardboard 3.0 (Superhive) foi feito para caixas. Ele funciona com
**geometrias arbitrárias / improváveis de serem papelão** (superfícies curvas,
fechadas, orgânicas) sem quebrar?

## O que valida nesta workspace

- Estressa um **addon comercial complexo** (44 geo node groups + shader com UV
  Direction Mask) com inputs muito diferentes do caso de uso projetado.
- Pipeline 100% headless: `blender --background --python` gera a malha,
  faz smart UV, aplica o modifier e renderiza — sem nenhuma operação manual.
- Render direto com o **shader nativo do asset** (sem bake, sem GLB), porque o
  objetivo era só inspecionar visualmente como o plugin se comporta.

## Formas testadas

| Forma | Base verts | Pós-modifier | Observação |
|---|---|---|---|
| torus (rosca) | 1536 | 3736 | corrugação acompanha a curva, ótimo resultado |
| knot (nó) | 14080 | 38019 | skin+subsurf deu volume bulboso; quinas rasgadas |
| sphere | ~3000 | — | ilhas de UV viram painéis de papelão com abas |
| monkey (Suzanne) | ~8000 | — | geometria orgânica; segurou bem o look cardboard |
| cone | ~1700 | — | faces grandes planas → corrugação sutil |
| spiral (mola) | 14080 | — | voltas fundem num "rolo" empilhado |

## Pipeline

`scripts/render_shape.py <shape> [res] [samples]`:

1. Append node group `📦 Easy Cardboard 3.0` + material `Easy Cardboard 3` do
   asset em `experiment-13-easy-cardboard/assets/easy-cardboard-3.1.blend`
2. Gera a malha da forma (primitivos + skin/subsurf para knot/spiral)
3. Smart UV project (o asset **exige** UV map — a corrugação é mapeada via UV
   Direction Mask)
4. Atribui o material, adiciona GeometryNodes modifier, configura sockets
   (Thickness 3mm, Wear 0.08, Displacement 0.15, etc — mesmos do exp 13)
5. Aplica o modifier (congela)
6. Monta cena (3 area lights key/fill/rim, world escuro), câmera orbital
7. Render Cycles 640px / 24 samples + denoise, 4 ângulos por forma

## Resultado

**O plugin aguentou todas as 6 geometrias arbitrárias sem erro.** O modifier
solidifica e aplica corrugação/fibras/dano-de-quina em qualquer malha com UV,
não só em caixas. O caráter do resultado varia com a geometria:

- **Superfícies curvas suaves** (torus, sphere) → corrugação em listras
  segue a curva, abas onde as ilhas de UV se encontram. Visualmente o mais
  "papelão de verdade".
- **Geometria orgânica** (monkey) → vira escultura de papelão com quinas
  rasgadas; surpreendentemente convincente.
- **Faces grandes e planas** (cone) → corrugação fica sutil porque há poucos
  vincos; precisa de mais subdivisão pra carregar detalhe.

## Limitação observada

A densidade de detalhe depende da densidade de malha de entrada: o cone
(poucas faces laterais) ficou mais liso que o torus (malha densa). O `Global
Scale` controla o tamanho das células de corrugação mas não compensa malha
esparsa. Para uma forma arbitrária renderizar bem, vale subdividir antes.

## Stack

- Blender 5.1.2 headless, Cycles
- Asset comercial Easy Cardboard 3.1 (reusado do exp 13)
