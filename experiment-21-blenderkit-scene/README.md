# Experimento 21 — BlenderKit: baixar asset-scene e subir numa cena (headless)

## Pergunta do experimento
Dá pra dirigir o **addon BlenderKit** (v3.19.2) de forma 100% automatizada/headless — instalar, autenticar, buscar, baixar e fazer append de um asset — **sem o user clicar no asset bar**? Asset alvo: scene **"The Lonely Outpost"** (Toby Noby), free, `asset_base_id d0e9d8ad-a61f-4b85-849a-6f8e53635b05`.

## Resposta: SIM, com gotchas

O pipeline roda inteiro via `blender --background --python`. O ponto crítico validado é que o BlenderKit **não baixa dentro do Blender** — ele sobe um **client daemon separado** (binário `blenderkit-client-*.exe` embutido no zip) que conversa com o addon por HTTP local (`127.0.0.1:62485`). Search/download são assíncronos via polling de reports. Dirigir isso headless exige replicar o fluxo sem os timers/operadores modais.

## Etapa crítica que o experimento prova
Dirigir a arquitetura **addon ↔ daemon ↔ servidor** programaticamente: subir o daemon por código, disparar o download via `download.download()`, fazer **polling manual** de `client_lib.get_reports(pid)` (em headless os timers modais do addon não rodam), e chamar `append_link.append_scene()` no `.blend` baixado. Nada feito à mão, nada de asset bar.

## Pipeline (`scripts/`)
1. **`01_install_addon.py`** — `addon_install` do zip + `addon_enable` + seta `api_key` nas preferences + `save_userpref`. Usa `BLENDER_USER_RESOURCES` apontado pra um config isolado do experimento (não polui o Blender do user). BlenderKit v3.x é addon **legacy** (tem `bl_info`), não extension.
2. **`02_download_and_append.py`** — coração:
   - `client_lib.start_blenderkit_client()` sobe o daemon; espera ele responder ao `/report`
   - search via REST público (`/api/v1/search`) com `Authorization: Bearer <key>` → `asset_data`
   - `download.download(asset_data, resolution="blend", model_location=..., model_rotation=...)`
   - loop de `client_lib.get_reports(os.getpid())` (retorna **lista** de tasks dict) até `status=="finished"`; pega `result.file_paths[-1]`
   - `append_link.append_scene(blend_path, link=False)` → nova Scene
   - inventário + `save_as_mainfile`
3. **`03_render.py`** — render still pela câmera do próprio asset (Cycles), validação visual.

## Resultado
- Scene **"The Lonely Outpost"** appendada: **55 objetos** (1 CAMERA, 42 MESH, 9 CURVE, 2 EMPTY, 1 LIGHT), com câmera e world próprios.
- `.blend` baixado: 54.5 MB. Resultante salvo em `out/lonely_outpost_appended.blend`.
- Render Cycles 1280×720, 96 samples (CPU, ~7 min): cabana de madeira na encosta, flores, árvore, montanhas, céu nublado — **fiel ao asset original**.

## Gotchas mapeados (o valor real do experimento)
1. **Versão do Blender importa pro unpack.** Depois de baixar, o daemon faz um passo de **unpack** que **reabre o `.blend` num sub-Blender** (`blender --background <blend> --python unpack_asset_bg.py`). Se o asset foi salvo numa versão mais nova que o Blender usado, dá `Error: Cannot read blend file ... incomplete header, may be from a newer version`. O asset "The Lonely Outpost" (jan/2026) só desempacotou no **Blender 5.1** — falhou no 4.3. **Regra: usar Blender ≥ versão em que o asset foi salvo.**
2. **Download exige autenticação mesmo pra asset free.** Search é público; o endpoint de download retorna **403** sem `api_key`. A key sai de `blenderkit.com/profile` (web, sem abrir Blender).
3. **Daemon trava entre execuções.** Um daemon iniciado por uma run anterior pode ficar preso na porta 62485 (`CloseWait`), e o `start_blenderkit_client` da próxima run não estabelece — `get_reports` dá timeout. Fix: matar o PID específico do daemon antes de re-rodar.
4. **Headless não tem timers modais.** O addon processa reports via `bpy.app.timers` que só rodam com GUI. Em `--background` é preciso fazer o polling de `get_reports` num loop próprio e chamar `append_scene` direto — não dá pra confiar no `BlenderkitDownloadOperator` modal.
5. **`BLENDER_USER_RESOURCES` isola o experimento.** Instalar o addon + salvar a key nos userprefs sem mexer no Blender real do user. (Esses dirs ficam gitignored — contêm a key.)

## Como rodar
```powershell
$env:BLENDER_USER_RESOURCES = "<exp>\bl_config_51"
$BL = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
# 1. instalar addon + key (1x)
& $BL --background --python scripts\01_install_addon.py -- <zip> <api_key>
# 2. baixar + append
& $BL --background --python scripts\02_download_and_append.py -- d0e9d8ad-a61f-4b85-849a-6f8e53635b05 <out>
# 3. render
& $BL --background <out>\lonely_outpost_appended.blend --python scripts\03_render.py -- <out>\render.png CYCLES 96 1280
```

## Honestidade técnica
- O download e o append são **100% do addon BlenderKit** (daemon + `append_scene`), não reimplementados.
- A api_key é do user, guardada em `secret/` (gitignored), nunca commitada nem postada.
- Variante feita: **(a)** baixar e abrir a scene como veio. Não foi feita a variante (b) (mesclar objetos em outra cena).
