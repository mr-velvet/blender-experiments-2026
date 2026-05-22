@echo off
"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" storage cp "C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web\cardboard_box.glb" gs://didlu-imagestore/cardboard-experiment/v1/cardboard_box.glb
"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" storage objects update gs://didlu-imagestore/cardboard-experiment/v1/cardboard_box.glb --content-type=model/gltf-binary --cache-control="public,max-age=3600"
"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" storage objects update gs://didlu-imagestore/cardboard-experiment/v1/index.html --content-type=text/html --cache-control="public,max-age=60"
