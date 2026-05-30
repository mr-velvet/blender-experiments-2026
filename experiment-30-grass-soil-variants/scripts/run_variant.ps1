# roda 1 variante (monta + render) — chamado pelo orquestrador
param([string]$Tag, [string]$CfgJson)
$BL = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
$env:BLENDER_USER_RESOURCES = "C:\Users\manu\ved\blender-experiments-2026\experiment-21-blenderkit-scene\bl_config_51"
$house = "C:\Users\manu\ved\blender-experiments-2026\experiment-21-blenderkit-scene\out\edited\lonely_B_floor.blend"
$d = "C:\Users\manu\ved\blender-experiments-2026\experiment-30-grass-soil-variants"
$blend = "$d\out\variants\$Tag.blend"
$mk = "$d\scripts\06_make_variant.py"
$rv = "$d\scripts\07_render_variant.py"
$rcheck = "$d\out\renders"
& $BL --background $house --python $mk -- $blend $CfgJson *>&1 | Select-String -Pattern "ground x|scattered|TOTAL|saved|VARIANT_DONE|Error|Traceback" | ForEach-Object { $_.Line }
& $BL --background $blend --python $rv -- $rcheck $Tag *>&1 | Select-String -Pattern "^R |RV_DONE|Error|Traceback" | ForEach-Object { $_.Line }
"DONE $Tag"
