# Experimento 12 — Mossify (regras duras, explicitas, nao negociaveis)

**LER INTEIRO ANTES DE QUALQUER ACAO. TODAS AS REGRAS SAO HARD-LOCK.**

---

## O que esse experimento testa (e SO isso)

Duas perguntas. Apenas duas. Em nenhuma hipotese o experimento expande pra alem disso.

### Pergunta 1: O plugin Mossify gera geometria de verdade?

- "Geometria" = mesh real com vertices, faces, triangulos no buffer
- NAO eh textura
- NAO eh shader que parece musgo
- NAO eh displacement em runtime
- NAO eh efeito visual de render
- Tem que ser **mesh concreta**, contavel, exportavel, que existe como `bpy.data.objects` com `data.vertices` populado

**Se sim → user compra o plugin.**

### Pergunta 2: Da pra exportar essa geometria pra fora do Blender?

- Da pra exportar GLB/FBX/OBJ?
- A geometria de musgo gerada continua sendo geometria fora do Blender?
- Materiais sobrevivem (pelo menos parcialmente)?
- O resultado eh consumivel em outro contexto (jogo, three.js, Unity, Unreal, etc)?

**Se sim → user tem certeza que o plugin gera valor que sai do Blender.**

**Se nao sair do Blender, o plugin nao serve pra o caso de uso do user, independente de quao bonito eh o resultado dentro do Blender.**

---

## O que NAO eh esse experimento (PROIBIDO expandir pra qualquer um destes)

- ❌ NAO eh sobre fazer um demo bonito em three.js
- ❌ NAO eh sobre validar pipeline completo de jogo
- ❌ NAO eh sobre otimizar peso de arquivo
- ❌ NAO eh sobre criar UI/HUD
- ❌ NAO eh sobre comparar Mossify com outros plugins
- ❌ NAO eh sobre testar performance
- ❌ NAO eh sobre testar varios assets
- ❌ NAO eh sobre criar player web — se quiser visualizar, abrir GLB exportado num gltf-viewer terceiro **ja existente** (ex: gltf-viewer.donmccurdy.com)
- ❌ NAO eh sobre escolher densidade/parametros — usar defaults do plugin sempre
- ❌ NAO eh sobre testar varios objetos hospedeiros — usar UM unico asset que o user passar

**Se aparecer impulso de fazer qualquer um destes, PARAR. Eh expansao de escopo, e expansao de escopo nesta workspace eh proibida.**

---

## Regras durissimas de execucao

### 1. NAO INFERIR INTENCAO (HARD-LOCK NIVEL MAXIMO)

- O experimento eh literalmente as duas perguntas acima
- Em hipotese alguma "deduzir que o user provavelmente quer X tambem"
- Se houver duvida sobre qualquer coisa, PARAR e perguntar
- A regra master de literalidade do CLAUDE.md da workspace se aplica integralmente
- **Re-leitura obrigatoria do CLAUDE.md (raiz da workspace) antes de comecar**

### 2. NAO CRIAR GEOMETRIA NA MAO

- NAO criar plane, cubo, esfera, nada
- NAO subdividir mesh com Python
- NAO modelar nada via bmesh
- NAO substituir o asset que o user passou por outro "que faz mais sentido"
- O asset que o user passar EH o asset do experimento. Ponto.

### 3. USAR O PLUGIN COMO UM ARTISTA USARIA

- Operators expostos pelo plugin, NAO API interna do GN tree
- Defaults do plugin sao OS defaults — nao escolher parametros sozinho
- Se o plugin faz a coisa de um jeito X, fazer do jeito X
- NUNCA reescrever o que o plugin faz "porque eu sei como funciona internamente"

### 4. RESULTADO ESTRANHO EH RESULTADO VALIDO

- Se o musgo cobrir o telhado todo, eh isso
- Se ficar feio, eh isso
- Se nao funcionar com aquele asset, eh isso
- Reportar fielmente. NAO "consertar" criando outra coisa.

### 5. ANTES DE CODAR — OBRIGATORIO

Escrever ao user a lista enumerada de:
1. Os itens exatos que vao ser testados
2. O que esta fora de escopo (lista explicita)
3. Qualquer duvida residual

Aguardar confirmacao escrita do user. **Se faltou confirmar UM item, esse item nao eh feito ate o user confirmar.**

### 6. SE BATER QUALQUER OBSTACULO, PARAR

- Plugin nao instala headless? PARAR e perguntar.
- Plugin precisa de UI? PARAR e perguntar.
- Operator nao funciona como esperado? PARAR e perguntar.
- Asset nao tem propriedade que parece necessaria? PARAR e perguntar.
- Qualquer coisa que pareca exigir "improviso"? PARAR e perguntar.

Custo de perguntar: 1 mensagem. Custo de improvisar: ja conhecido (horas perdidas, 2 vezes seguidas).

### 7. ESCOPO DE TEMPO

O experimento existe pra responder DUAS perguntas. Se levar mais de X passos pra responder, alguma coisa esta errada — provavelmente expansao de escopo.

Marcadores: instalar plugin → aplicar em UM asset → exportar GLB → abrir GLB em viewer terceiro → contar vertices/poligonos do musgo → CONCLUIR.

Nao tem fase 2. Nao tem otimizacao. Nao tem polish.

---

## Saida esperada

Documento curto respondendo as DUAS perguntas com evidencia objetiva:

1. **"Mossify gera geometria?"** — sim/nao + numero de vertices/poligonos do mesh de musgo gerado + screenshot do resultado dentro do Blender
2. **"Da pra exportar?"** — sim/nao + nome do formato + tamanho do arquivo final + screenshot do GLB aberto em viewer terceiro (gltf-viewer.donmccurdy.com ou similar) + lista de quais materiais sobreviveram

**Nao escrever README elaborado, nao escrever PROGRESS, nao escrever apresentacao. So as respostas.**

---

## Por que essas regras existem

Em 2026-05-21 e 2026-05-22 (dois dias seguidos), o mesmo agente expandiu escopo de experimentos nesta workspace, inferiu intencao do user, criou geometria na mao quando o experimento era sobre testar plugins, e entregou trabalho que o user nao podia usar. Horas perdidas em ambos os casos.

Este experimento existe pra resolver DUAS perguntas baratas e diretas. Qualquer expansao alem dessas duas perguntas eh recorrencia do mesmo padrao destrutivo. Aplicar as regras acima eh inegociavel.

**Repetindo, pra ficar absolutamente claro:**

1. Mossify gera geometria? Sim/nao.
2. Da pra exportar? Sim/nao.

So isso.

So isso.

So isso.

So isso.

So isso.

So isso.

So isso.

So isso.

So isso.

So isso.
