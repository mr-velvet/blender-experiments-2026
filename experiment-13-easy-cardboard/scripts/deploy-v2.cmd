@echo off
set GCLOUD="C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set BASE=C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web2
set BUCKET=gs://didlu-imagestore/cardboard-experiment/v2

%GCLOUD% storage cp "%BASE%\index.html" %BUCKET%/index.html

for %%D in (wear scale corrugation shapes wild) do (
  if exist "%BASE%\%%D" (
    %GCLOUD% storage cp -r "%BASE%\%%D\*" %BUCKET%/%%D/
  )
)

%GCLOUD% storage objects update %BUCKET%/index.html --content-type=text/html --cache-control="public,max-age=60"
%GCLOUD% storage objects update "%BUCKET%/**/index.html" --content-type=text/html --cache-control="public,max-age=60"
%GCLOUD% storage objects update "%BUCKET%/**/*.png" --content-type=image/png --cache-control="public,max-age=3600"
