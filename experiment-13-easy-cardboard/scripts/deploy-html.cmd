@echo off
"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" storage cp "C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web\index.html" gs://didlu-imagestore/cardboard-experiment/v1/index.html
"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" storage objects update gs://didlu-imagestore/cardboard-experiment/v1/index.html --content-type=text/html --cache-control="public,max-age=60"
