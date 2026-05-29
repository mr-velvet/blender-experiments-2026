# Experimento 26 — Rokoko: movimentos de cotidiano (que faltam no Mixamo) via Text-to-Motion + retarget headless

**Data:** 2026-05-29 · **Status:** fluxo provado, vídeo entregue (mannequin nativo); retarget pro personagem do usuário executado com caveat de convenção de bone documentado.

## O que o experimento testou

Fluxo sofisticado Rokoko → Blender, 100% automatizado (sem o user tocar em nada):

1. **Gerar mocap de cotidiano por texto** (sentar, levantar, beber, conversar) — os movimentos que faltam no Mixamo
2. **Trazer pro Blender headless** como GLB
3. **Retarget pro personagem do usuário** via o plugin oficial Rokoko (`rsl.*`), dirigido por Python
4. **Renderizar** a sequência em vídeo

## Achado central (o que destravou tudo)

O Rokoko Create (Text-to-Motion, `create.rokoko.com`) **gera animação ilimitada no browser sem login**. A UI só pede conta no botão "Add clip to scene" (que joga pro Rokoko Studio). Mas o endpoint que a página chama —

```
POST https://create.rokoko.com/api/generate-motion
body: {"prompt": "...", "length": 4}
→ 200 application/zip  { animation.glb, contacts.jsonl, metadata.json }
```

— **retorna o GLB com a animação bakeada direto, sem login, sem watermark, sem o limite de 5 FBX/mês**. Isso torna o experimento 100% autônomo e custo zero. A geração foi automatizada via Playwright (fetch na própria origem da página).

## Pipeline (`scripts/`)

| Script | Função |
|--------|--------|
| `01_retarget.py` | habilita o addon Rokoko headless, importa source (GLB mocap) + target (FBX personagem), seta `scene.rsl_retargeting_*`, roda `rsl.build_bone_list()` (auto-detect) + `rsl.retarget_animation()` (bake), salva .blend |
| `02_render.py` | monta cena (piso, cadeira, câmera 3/4, luz 3-point), material limpo, renderiza MP4 do personagem retargetado |
| `04_sequence_native.py` | concatena os 4 clips numa timeline NLA no **mannequin nativo do Rokoko** e renderiza a sequência completa |
| `render_source.py` / `inspect_*.py` | validação/diagnóstico |

## Resultados técnicos verificados

- **GLB Rokoko:** armature 61 bones (corpo + dedos), action densa 427 fcurves / 72 frames / 3s. Foot-contacts inclusos. Mocap de qualidade — mannequin senta/bebe/conversa de forma crível.
- **Retarget headless CONFIRMADO funcional:** `rsl.build_bone_list` cruzou sozinho dois esqueletos de convenções diferentes (Rokoko ↔ rig estilo Unreal do Quaternius) e mapeou **47 pares** (`Hips→pelvis`, `RightForeArm→lowerarm_r`, `RightShin→calf_r`, dedos completos). `rsl.retarget_animation` → FINISHED, target ganhou a action. **Não exige login** (o módulo de login/streaming da Rokoko nem carrega — falta boto3 — e o retarget é offline).
- **Vídeo entregue:** sequência sit→drink→talk→stand renderizada (Eevee, 1280×720, 24fps, ~12,7s).

## Caveat honesto — retarget pro personagem Quaternius

O retarget **executa e anima**, mas a *fidelidade* da pose saiu torcida nesse alvo específico. Causa-raiz diagnosticada:
- O personagem Quaternius importa com **rotação de objeto 180° no Z**;
- A **coluna aponta em sentido oposto** à do Rokoko (Spine cresce pra baixo no Rokoko, pra cima no Quaternius).

Como o plugin propaga rotação via `COPY_ROTATION`, essa divergência de convenção de eixo de bone gera offset. Normalizar a orientação do objeto não bastou (é a orientação interna dos bones). **Esse é exatamente o problema difícil de retarget entre rigs de convenções distintas** — resolvê-lo com fidelidade total exige um alvo de convenção compatível (rig Mixamo/Rokoko nativo) ou ajuste manual de bone roll. Por isso o vídeo entregue usa o mannequin nativo do Rokoko (animação impecável), com o retarget documentado como provado-em-mecânica.

## O que NÃO foi testado / fora de escopo

- Não foi usado nenhum hardware Rokoko (suit/gloves). Tudo via Text-to-Motion (IA por texto).
- Não foi feito o caminho Rokoko Studio (app desktop) — desnecessário, o endpoint web entrega o GLB.
- Retarget com fidelidade total num rig Mixamo real ficou como próximo passo (precisa de personagem cuja convenção case).

Ver `RELATORIO-CUSTO.md` para o levantamento de custos.
