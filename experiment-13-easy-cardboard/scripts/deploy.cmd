@echo off
setlocal
set GCLOUD="C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set ROOT=C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web
%GCLOUD% storage cp "%ROOT%\index.html" gs://didlu-imagestore/cardboard-experiment/v1/index.html
%GCLOUD% storage cp "%ROOT%\cardboard_box.glb" gs://didlu-imagestore/cardboard-experiment/v1/cardboard_box.glb
%GCLOUD% storage objects update gs://didlu-imagestore/cardboard-experiment/v1/index.html --content-type=text/html --cache-control="public,max-age=60"
%GCLOUD% storage objects update gs://didlu-imagestore/cardboard-experiment/v1/cardboard_box.glb --content-type=model/gltf-binary --cache-control="public,max-age=3600"
