RELATORIO DE ERRO — Easy Cardboard em modelo 3D baixado (casa)

== O QUE ACONTECEU, EM UMA FRASE ==
O Easy Cardboard funciona muito bem em GEOMETRIA FECHADA (as 6 primitivas do
experimento anterior: rosca, esfera, cone, no, etc), mas ESTILHACA modelos de
PAREDE FINA (a casa baixada), porque o plugin foi desenhado pra dar volume a
solidos, nao a cascas de uma face so.

== OS DOIS "ERROS" DESTA SESSAO ==

ERRO 1 — A casa virou um amontoado de laminas (erro de RESULTADO)
  Causa raiz, medida com numeros reais na malha da casa:
    - malha crua: 4337 verts, 3067 faces, 6636 arestas
    - 4071 dessas arestas (61,3%) sao ARESTAS DE BORDA = pertencem a UMA
      face so. Ou seja: a casa e uma CASCA ABERTA, paredes de espessura zero,
      nao um solido.
    - 0 arestas nao-manifold.
  Por que isso quebra o papelao:
    - O Easy Cardboard pega cada "folha" e faz: (a) Solidify pra dar espessura,
      (b) Edge Split por angulo pra separar as abas de papelao, (c) Displacement
      pra ondular a corrugacao. Isso pressupoe que as faces formam um VOLUME
      fechado (uma caixa, uma esfera). Numa casca aberta, cada painel (parede,
      agua do telhado) nao tem vizinho com quem se fundir, entao vira uma lamina
      solta. Empilhadas, dao o look de "cacos".
    - Apos aplicar: 11042 faces (3,6x). Cada face fina virou uma caixinha de
      papelao independente flutuando.
  Conclusao: NAO e bug do plugin. E incompatibilidade de tipo de malha. Solido
  fechado -> otimo. Casca fina aberta -> estilhaca. Dado valido do experimento.

ERRO 2 — A sessao Claude anterior caiu com timeout (erro de INFRA, nao do Blender)
  - Nos logs do topico: "Sessao Claude terminou com erro (exit=-1, timeout)".
  - Causa: o render_model.py renderiza 7 frames (4 orbit + 3 close) em Cycles a
    800px/48 samples. Isso e demorado. A sessao assincrona do Claude tem um teto
    de tempo de execucao por rodada; o Blender ainda estava rendando quando esse
    teto estourou e a sessao foi encerrada a forca.
  - Prova de que o Blender em si NAO falhou: os arquivos tabern_orbit0..3 e
    tabern_close0..2 EXISTEM no disco (output/model_renders/). O render terminou;
    foi a sessao do agente que foi cortada antes de postar o resto.
  - O 1o experimento (6 primitivas) nao caiu porque cada forma renderizava em
    paralelo/lotes menores e cabia na janela de tempo.

== O QUE FOI EFETIVAMENTE TESTADO (honestidade tecnica) ==
  SIM testado:
    - Pipeline headless completo: importar GLB externo -> juntar meshes ->
      normalizar -> smart UV -> append do node group + material do .blend do
      Easy Cardboard -> setar preset AGED via sockets -> aplicar modifier ->
      render Cycles. Tudo 100% automatizado, user nao tocou no Blender.
    - O preset envelhecido (AGED) aplicado de fato (Wear 0.7, Displacement 0.4,
      Fibras 8, Roughness 0.9, Thickness 6mm).
    - Comportamento do plugin em malha aberta de producao (modelo de terceiro).
  NAO testado / fica de fora:
    - Corrugacao legivel em close na CASA: como a forma estilhacou, os close-ups
      mostram cacos, nao a "ondinha" limpa entre cortes. As ondinhas legiveis
      estao nos closes das PRIMITIVAS fechadas do experimento anterior.

== CAMINHOS PRA RESOLVER (se o user quiser a casa de papelao legivel) ==
  Opcao A — Fechar a malha antes do papelao: rodar um Solidify proprio (dar
    espessura real as paredes) ou um "Make Manifold" antes do Easy Cardboard.
    Transforma as cascas em solidos finos -> o plugin passa a tratar como caixa.
  Opcao B — Baixar um modelo que ja seja solido fechado (ex: um modelo low-poly
    "watertight"). Aposta mais segura pra ver o look bom.
  Opcao C — Aceitar como resultado do experimento: "Easy Cardboard nao serve pra
    cascas finas sem pre-processo". Tambem e uma resposta valida pra decisao.

== ARQUIVOS ==
  scripts/preview_glb.py   - render do modelo CRU (o "antes")
  scripts/render_model.py  - pipeline papelao + render (o "depois")
  scripts/diag_model.py    - diagnostico que mediu os 61,3% de arestas de borda
  output/model_preview/    - prints ANTES (tabern_a0/a1)
  output/model_renders/    - prints DEPOIS (tabern_orbit0..3, close0..2)
