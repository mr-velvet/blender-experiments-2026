# Experimento 25 — Opções de animação de humanoides no Blender (fora do Mixamo)

**Tipo:** curadoria / levantamento (passo prévio, não experimento de pipeline). Mesma natureza do exp24.

## Pedido (literal)
> "ver que opções tenho pra criar bonecos humanoides com bibliotecas grandes de animações, **fora do Mixamo**, com mais autonomia pra mexer. Inventário free e pago. Relatório HTML com área paga e área gratuita, separando todos os itens. Se achar um bom gratuito, **pode** fazer um experimento criando humanoides com animação e subindo as imagens da renderização."

## Escopo confirmado (4 frentes)
1. **Bibliotecas de clips** — acervo de animações prontas (tipo-Mixamo, fora dele): packs/marketplaces/bancos acadêmicos de mocap (.fbx/.bvh)
2. **Rig / retarget** — addons que dão autonomia de aplicar qualquer biblioteca no humanoide próprio (Auto-Rig Pro, Rigify, Rokoko, Expy Kit, etc)
3. **IA** — geração de movimento text-to-motion / video-to-motion
4. **Humanoide base** — geradores de boneco humanoide para animar (MPFB2, CharMorph, Human Generator, etc)

**Fora de escopo:** Mixamo como item; engines de jogo; instalar/testar plugin (isto é curadoria).

## Método
- 4 agentes de pesquisa paralelos (clips · rig/retarget · IA · humanoide base) → ~55 fontes brutas
- Dedup e consolidação em 2 abas (FREE / PAGO), cada item com sub-categoria (`kind`)
- Validação de imagem: 3 lotes de agentes extraíram og:image **real** das páginas (a maioria dos og:image iniciais eram inferidos e davam 404/403)
- Download local + validação HTTP 200 + magic bytes: **45/46 imagens OK**. Só o KIT Database não tem preview público (card com placeholder)

## Resultado
- **46 itens, 2 abas:** 29 Free + 17 Pago, filtráveis por sub-categoria
- Galeria HTML custom (tema ciano), card = imagem + descrição + diferencial, clique abre detalhe (tipo, preço, formato, licença, diferencial, nota)

### Conclusão para deliberar
- **Caminho free mais sólido (legalmente tranquilo):** Quaternius Universal Animation Library (CC0, 250+ anims, rig universal) + Rigify/MPFB2 (gerar+rigar) + Rokoko/Expy Kit/Retarget BVH (retarget). Mesh2Motion é o "Mixamo aberto" mais direto.
- **Bancos acadêmicos enormes (CMU 2.5k, AMASS 11k, Bandai 3k):** volume gigante, mas AMASS/Bandai/KIT são **não-comerciais**. CMU é livre pra qualquer uso (precisa limpeza).
- **Caminho pago mais completo p/ "meu boneco + biblioteca grande":** Auto-Rig Pro (+Remap) no Blender; ActorCore/MoCap Online/Truebones pro acervo; Character Creator+iClone pro ecossistema externo.
- **IA:** Rokoko Create / DeepMotion SayMotion / Cartwheel (text-to-motion); Move AI / Plask / Wonder Studio (video-to-motion). MoMask é o único text-to-motion 100% free/open/scriptável.
- **Geradores nativos automatizáveis nesta workspace:** MPFB2 e CharMorph (geram mesh+rig Rigify 100% dentro do Blender, via Python).

## Honestidade
- Curadoria, **nenhum plugin instalado/testado** — notas de "headless" são estimativas a confirmar num experimento real.
- 45/46 imagens validadas; para fontes que bloqueiam hotlink (Reallusion, Daz, VRoid, RPM, etc) usei o thumbnail do **vídeo oficial** correspondente (verificado existir). KIT sem imagem (placeholder).
- Bandai = GIF animado real do walk-cycle (5.5MB) — mantido por ilustrar o mocap em movimento.

## Fase 2 (experimento de render) — PENDENTE de decisão do user
O pedido tornou a fase 2 condicional ("pode fazer se achar um bom gratuito"). Perguntei ao user se: (a) entrego o relatório primeiro e ele escolhe a fonte, ou (b) eu já escolho e faço. Aguardando resposta para não escolher a fonte por ele (regra de literalidade).

## Hospedado
https://st.did.lu/blender-exp25-humanoid-animation/v1/index.html

## Arquivos
- `data.json` — 46 itens estruturados
- `index.html` — template (placeholder `__DATA__`)
- `build.py` — injeta data.json → `index_built.html`
- `download_images.py` — valida + baixa imagens (HTTP 200 + magic bytes)
- `img/` — 45 previews validados
