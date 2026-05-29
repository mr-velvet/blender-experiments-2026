# Relatório de custo — setup de mocap com Rokoko

Pedido do user: "quanto custaria ter um setup usando essa tecnologia, e talvez câmeras para gravar movimentação de humanoide".

Há **dois caminhos** bem distintos de custo. O experimento usou o primeiro.

---

## Caminho A — IA por texto/vídeo (o que foi usado neste experimento)

**Não precisa de hardware nenhum.** Movimento gerado por prompt de texto (ou por vídeo de uma câmera comum).

### Software Rokoko Studio (assinatura, preços anuais)

| Plano | Preço (anual) | Text-to-Motion | Vídeo-to-Motion | Export FBX |
|-------|---------------|----------------|-----------------|------------|
| **Starter (Free)** | **US$ 0** | ilimitado gerar + 5 imports Studio/mês | vídeos < 15s | ilimitado |
| Basic | US$ 10/mês | ilimitado + 100 imports/mês | ilimitado | ilimitado |
| Plus | US$ 20/mês | ilimitado + 1.000 imports/mês | ilimitado | ilimitado |
| Pro | US$ 50/mês | tudo ilimitado | ilimitado | ilimitado |
| Enterprise | a partir de US$ 100/mês | custom | custom | custom |

### Custo real do que este experimento fez: **US$ 0**
O endpoint `create.rokoko.com/api/generate-motion` entrega o GLB de cada movimento **sem login e sem limite**. Para um volume baixo/médio de clips, o caminho é literalmente gratuito. Se quiser usar o Rokoko Studio oficial (edição, retarget visual, mais imports/mês), o Basic a **US$ 10/mês** já cobre 100 clips/mês.

### Vídeo-to-Motion (mocap por câmera comum)
A Rokoko faz mocap markerless a partir de **vídeo de celular/webcam** (sem hardware dedicado). No Free: clipes < 15s; nos pagos: ilimitado. É a opção "gravar movimentação de humanoide com câmera" mais barata — custo = só a assinatura (US$ 0–20/mês) + uma câmera que você já tem.

---

## Caminho B — captura por sensores (hardware Rokoko)

Para captura de **alta fidelidade em tempo real** (ator vestindo suit). Preços de referência (confirmar no site, podem variar com câmbio/promoção):

| Item | Preço aprox. (USD) | Para quê |
|------|--------------------|----------|
| Smartsuit Pro II | **US$ 2.295** | corpo inteiro, 19 sensores inerciais |
| Smartgloves II | ~US$ 995/par | dedos e mãos |
| Coil Pro | ~US$ 1.495 | elimina drift/oclusão, posição global |
| Headcam (face) | ~US$ 995 | captura facial |
| **Bundle full performance** | ~US$ 4.500–6.000 | corpo + dedos + face + Coil |

Software: o Studio para usar os sensores em tempo real normalmente exige plano pago (Plus/Pro), some à assinatura acima.

### Quando o Caminho B se justifica
Só quando você precisa de **performance ao vivo de um ator** com qualidade de produção (cinema/jogos AAA). Para gerar uma biblioteca de movimentos de cotidiano que faltam no Mixamo — o caso deste experimento — **o Caminho A (texto/vídeo) resolve a custo zero ou quase**.

---

## Recomendação

| Necessidade | Caminho | Custo/mês |
|-------------|---------|-----------|
| Gerar clips de cotidiano (sit/stand/drink/talk/idles) por texto | A — Text-to-Motion | **US$ 0** (endpoint web) ou US$ 10 (Studio Basic) |
| Capturar movimento de uma pessoa real com câmera comum | A — Vídeo-to-Motion | US$ 0–20 |
| Performance de ator em tempo real, qualidade de produção | B — Smartsuit | ~US$ 2.300+ one-time + assinatura |

**Para o objetivo descrito (preencher a lacuna de movimentos de cotidiano do Mixamo), o setup recomendado é o Caminho A: US$ 0 a US$ 10/mês, sem hardware.** O retarget pro personagem alvo roda headless no Blender via o plugin oficial gratuito da Rokoko.
