# Aprendizados — Pincéis VDM de rosto no Blender (experiment-16)

> Atualizado: 2026-05-27. Documento de melhores práticas pra carimbar features de
> rosto (olho/nariz/boca) com os pincéis VDM do pack "Human Face VDM Blender 4.3"
> dirigido 100% por Python headless. Este é o doc valioso: ele diz **o que dá pra
> fazer e como**, pra não redescobrir tudo a cada sessão.

---

## 1. O que é o pack e o que ele entrega

Pack: `Human Face VDM Blender 4.3` (30 brushes `.asset.blend` em
`C:\Users\manu\Downloads\BLENDER-FACES-BRUSH\...\Saved\Brushes`).

São **VDM (Vector Displacement Map) brushes**: cada carimbo desloca a malha num
campo vetorial pré-gravado, produzindo uma feature de rosto em 1 stroke. Não é
textura, não é decal — é deslocamento real de geometria.

### Catálogo identificado (por medição do deslocamento real dos vértices)
- **Narizes:** b01–b14, b27–b30. Têm variedade real: b1/b7 finos com narina;
  b28/b30 largos e carnudos (os mais saltados). **É a feature com mais variação.**
- **Bocas:** b15–b18. Saem como lábio; precisam de orientação certa (ver §4).
- **Orelhas:** b19–b24 (concha lateral).
- **Olhos:** b21/b25/b26 — na prática o **mesmo** olho (globo + pálpebra + cantos)
  com variação sutil. **b25 tem a forma mais definida.** O pack NÃO tem variedade
  real de olhos.

---

## 2. A mecânica que FUNCIONA (e por quê)

Regra de ouro descoberta na marra: **carimbar sempre num plano denso, em vista
TOP-DOWN ortográfica, dentro do Sculpt Mode.** Depois plantar o plano na face do
objeto-alvo.

Passo a passo (referência: `scripts/38_eye_cube.py`, `scripts/39b_mouth_rot.py`):

1. `primitive_plane_add(size=2)` + modifier `SUBSURF` SIMPLE level 8, aplicado.
   (Precisa de malha densa pro VDM ter onde deslocar.)
2. View: `view_rotation=(1,0,0,0)`, ORTHO, top-down. **O carimbo só sai em tamanho
   cheio na orientação canônica top-down, roll 0.** Em face vertical / com roll, o
   stamp encolhe ou o ray atravessa a malha.
3. Entrar em `SCULPT` mode com o plano ativo e selecionado.
4. Carregar o brush via `bpy.data.libraries.load`, setá-lo em
   `tool_settings.sculpt.brush`.
5. **Colorspace da imagem do brush = `Non-Color`** (senão o VDM sai distorcido).
6. `texture_slot.map_mode='AREA_PLANE'`.
7. Carimbar com `bpy.ops.sculpt.brush_stroke` (2 pontos no mesmo lugar = 1 stamp).
8. Plantar o plano na face: scale ~0.96, rotation_euler pra alinhar +Z com a normal
   da face, location no offset da face, `transform_apply`.

### Por que NÃO carimbar direto na face vertical do cubo
O ray do sculpt atravessa o cubo e o stamp não pega a face certa, ou a feature
encolhe pra um pontinho. **Sempre carimbar no plano em top-down e depois plantar.**

---

## 3. Controle de PROPRIEDADES (só do pincel — nada de mexer na malha)

Tudo abaixo é propriedade do pincel / setup do stroke. **NUNCA manipular vértice
depois (nada de `v.co.z *= k`, nada de flip, nada de pinçar a malha).** Se o relevo
do brush é raso, é raso — reportar honesto.

| O que controla | Propriedade | Observação |
|---|---|---|
| **Tamanho** da feature | `unified_paint_settings.unprojected_radius` (raio em unidades de mundo) | Setar `use_locked_size='SCENE'` + `use_unified_size=True`. NÃO é o `size` em pixels. |
| **Profundidade/relevo** | `brush.strength` | def 1.0. Strength alto aprofunda o sulco e engrossa o relevo. Mediu: olho/boca escalam linear. |
| **Orientação** | giro RÍGIDO da malha em Z **antes** do stroke, desfeito **depois** | Ver §4. É orientação rígida, não deforma. `texture_slot.angle` e roll da view **NÃO** servem — encolhem o stamp. |
| Altura VDM | `brush.height` | def 0.4. **NÃO reescala** VDM image-based (medido). Não usar pra variar tamanho. |

---

## 4. Orientação — o achado mais importante

O VDM sai numa orientação canônica fixa. Pra rotacionar a feature **sem encolher**,
a única via que funciona é: **girar a malha do plano em Z antes do stroke e desfazer
o giro depois** (`Matrix.Rotation` aplicada aos vértices). Isso é orientação rígida,
não deforma o relevo.

Ângulos certos (confirmados visualmente + pelo user):
- **Olho:** rotação **90°** → olho amêndoa horizontal anatômico (globo + pálpebra +
  cantos). A 0° sai vertical; a 45° sai diagonal/esquisito.
- **Boca:** rotação **90°** → boca horizontal de 2 lábios (lábio superior, linha dos
  lábios, lábio inferior). **Sem o 90° a boca vira uma "folha" vertical ilegível** —
  esse era o "bug" da boca que parecia chapada. Não era a malha, era a orientação.
- **Nariz:** 0° (orientação canônica já sai certo, narina pra baixo).

`texture_slot.angle` e roll da view foram testados e **falham** (qualquer ângulo ≠ 0
encolhe a feature a um ponto). Só o giro rígido da malha funciona.

---

## 5. Globo ocular (esfera no olho)

O olho b25 tem uma concavidade onde encaixa um globo. Receita (script 38):
- Achar o centro da concavidade = vértice mais baixo perto da origem do plano.
- Transformar pra coord de mundo com `plate.matrix_world @ eye_center`.
- Adicionar `uv_sphere` raio ≈ 0.38× o raio do olho, empurrada pela normal da face
  pra aflorar dentro da pálpebra.
- Material branco levemente especular.
- **É o único objeto extra permitido** — o olho em si é 100% pincel.

---

## 6. Limites REAIS do pack (reportar, não esconder)

- **Olhos sem variedade:** b21/b25/b26 são o mesmo olho. Pra variar olho, só dá pra
  mudar tamanho/profundidade via propriedade — não a forma.
- **Boca:** os 4 brushes (15-18) dão a mesma família de lábio. Variar = brush +
  strength + tamanho. Não há "boca aberta" vs "boca sorrindo" etc.
- **Carimbar em face vertical direto não funciona** — sempre via plano top-down.
- **Rotação só via giro rígido da malha** — a API de ângulo do brush não serve.

---

## 7. PROIBIÇÕES (regras travadas pelo user)

- ❌ Manipular vértice depois do carimbo (puxar, pinçar, flip de Z, escalar relevo).
- ❌ Colar a malha do brush manualmente como objeto chumbado.
- ✅ SÓ carimbo VDM + propriedades do pincel + orientação rígida do plano.
- ✅ A feature tem que **brotar da massa** (sculpt na própria malha), não ser placa.

---

## 8. Performance / tempos (máquina do user, 16 CPU, render Cycles baixo)

Medido em `output/39_*.txt`. Pipeline completo de 1 cubo com feature em 6 faces:

| Etapa | Tempo |
|---|---|
| Subir Blender 4.3 + script pronto | **~2.2 s** |
| Carimbar 6 features (6 planos, sculpt) | **~0.6–1.4 s** |
| 3 prints de viewport (640px, OpenGL) | **~0.7 s** |
| 3 renders Cycles baixos (480px, 32 samples) | **~3.9 s** (~1.3 s/frame) |
| **TOTAL ponta a ponta** | **~7–8 s** |

Conclusões práticas:
- **Render baixo (480px/32smp) é barato:** ~1.3 s/frame. Pra ver geometria/protrusão
  não precisa de alta — baixa resolução mostra o relevo perfeitamente.
- **Viewport OpenGL é ~3× mais rápido que Cycles** e suficiente pra validar forma
  antes de renderizar. Workflow: várias iterações em viewport, render só no fim.
- **Subir o Blender domina o custo** quando o trabalho é leve. Pra muitas variações,
  vale fazer tudo num único job (loop interno) em vez de 1 job por variação.
- Carga de máquina desprezível nesses jobs (features pequenas, malha leve).
