# Experimento 23 — Papelão × Massinha em móveis gratuitos

**Data:** 2026-05-29 (async via agnts)

## Pedido (literal do user)
Pegar móveis 3D gratuitos (sofá, TV, fogão, pia — os mesmos da casinha de bonecas do exp22), colocar lado a lado, e aplicar dois efeitos de render pesado sobre a geometria de cada um: uma cópia com **papelão** (Easy Cardboard) e outra com **massinha** (Clay Doh). Posicionar câmera para pegar de vários ângulos. Intenção: testar quanto dá pra gerar efeitos interessantes aplicando filtros/texturas de render complexas sobre a geometria de assets gratuitos de **densidade variável**.

## O que valida
Aplicar **dois pipelines de render complexos e independentes** (um Geometry Nodes que vira geometria real, um shader procedural com displacement real) sobre malhas de assets reais com densidade muito diferente — tudo headless, render Cycles direto. Não é primitivo, não é trivial.

## Assets
4 móveis BlenderKit já baixados no exp22 (densidade variável):

| Móvel | Asset | Tris (orig) | Tris papelão | Verts massinha (base) |
|---|---|---|---|---|
| Sofá | Taipei Sofa | 78k | ~79k | 39k |
| TV | Old Style CRT TV (42 sub-meshes) | 17k | ~21k | 9k |
| Fogão | Old rusty stove | 11k | ~19k | 8k |
| Pia | Sink | 65k | ~69k | 33k |

## Pipeline (`scripts/`)
- `lib_furniture.py` — biblioteca compartilhada:
  - `import_furniture()` — append do .blend BlenderKit, **descarta o objeto `Cube` 2×2×2** (container de thumbnail do BlenderKit), junta as sub-meshes reais em 1 mesh, aplica transforms
  - `normalize()` — escala por altura-alvo, apoia base em Z=0, centraliza XY
  - `apply_cardboard()` — append node group `📦 Easy Cardboard 3.0` + material `Easy Cardboard 3`; modifier Geometry Nodes com preset (espessura, corrugação, fibras, wear, displacement); **modifier_apply → geometria real**
  - `apply_clay()` — append material `Modeling Clay` (Clay 4.Doh), `displacement_method='BOTH'`, seta cor/displacement/texture-scale no node group; Subdivision modifier com `use_adaptive_subdivision=True` (Cycles) → **relevo real de geometria, não só normal map**
- `04_build_scene.py` — monta os 8 objetos (4 móveis × 2 efeitos) num grid 4 colunas × 2 fileiras (papelão atrás, massinha à frente), chão + luzes (sun + área fill) + world; salva `out/scene_furniture.blend`
- `05_render_angles.py` — abre o .blend, calcula bbox do conjunto, cria 6 câmeras por código orbitando (frente alta, dois 3/4, lateral, planta ortográfica top, nível do olhar), render Cycles com denoising

## Decisão de pipeline (render direto, sem bake/GLB)
O pedido é **render multi-ângulo**, não GLB exportável. Por isso a pipeline aplica os efeitos in-Blender e renderiza em Cycles direto. Isso **preserva a fidelidade total dos dois shaders procedurais** — bake→GLB perderia o relevo de displacement da massinha e a corrugação do papelão (como documentado no exp13/exp20, o exporter glTF não leva node groups complexos). Diferente dos exp3/exp13 que faziam bake porque o alvo era um GLB.

## Gotchas mapeados
1. **Objeto `Cube` container nos blends BlenderKit:** todo .blend de modelo vem com um `Cube` de 8 verts 2×2×2 (thumbnail bounding). Filtrar antes de juntar, senão entra geometria parasita.
2. **Adaptive subdivision no Blender 5.1** fica em `modifier.use_adaptive_subdivision` (não em `obj.cycles`, que não tem o atributo). `mesh.cycles` também não tem. `scene.cycles.feature_set` foi removido — não setar.
3. **Displacement da massinha derrete a forma em móveis grandes:** com `Texture Scale` fixo, peças grandes (sofá, pia) viram blobs. Solução: escalar texture scale ↑ e displacement ↓ por móvel conforme o tamanho. Calibração final: sofá disp 0.07/scale 26, pia disp 0.05/scale 28, fogão/TV intermediário.
4. **`Global Scale` do Easy Cardboard** precisa baixar (~0.5) porque os móveis têm ~0.5–0.9m e a corrugação default é calibrada para metros.

## Resultado
- Cena: 8 peças, ~390k tris no total (papelão é geometria aplicada; massinha ganha tris no render via adaptive subdiv)
- 6 renders Cycles 1600×992, 160 samples + denoising
- **Galeria hospedada:** https://st.did.lu/blender-exp23-cardboard-clay/v1/index.html

## Honestidade técnica
- **Papelão:** 100% do node group Easy Cardboard, aplicado como geometria real (silhueta facetada de caixa muda de verdade). Nada reimplementado.
- **Massinha:** 100% do shader Clay 4.Doh com displacement `BOTH` → relevo de geometria real no Cycles (não normal map fake). Cor de massa setada via input do node group.
- **Câmeras:** criadas por código, enquadradas pelo bbox. Não há câmera de asset envolvida.
- **Layout:** as fileiras se sobrepõem parcialmente na vista frontal (massinha à frente tapa parte do papelão atrás). As vistas 3/4 e a planta-top mostram os pares lado a lado sem oclusão — são os ângulos de comparação.
