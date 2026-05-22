@echo off
set GCLOUD="C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
set BASE=C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web2
set BUCKET=gs://didlu-imagestore/cardboard-experiment/v2

%GCLOUD% storage cp "%BASE%\index.html" %BUCKET%/index.html
%GCLOUD% storage cp "%BASE%\wear\index.html" %BUCKET%/wear/index.html
%GCLOUD% storage cp "%BASE%\wear\*.png" %BUCKET%/wear/
%GCLOUD% storage cp "%BASE%\scale\index.html" %BUCKET%/scale/index.html
%GCLOUD% storage cp "%BASE%\scale\*.png" %BUCKET%/scale/
%GCLOUD% storage cp "%BASE%\corrugation\index.html" %BUCKET%/corrugation/index.html
%GCLOUD% storage cp "%BASE%\corrugation\*.png" %BUCKET%/corrugation/
%GCLOUD% storage cp "%BASE%\shapes\index.html" %BUCKET%/shapes/index.html
%GCLOUD% storage cp "%BASE%\shapes\*.png" %BUCKET%/shapes/
%GCLOUD% storage cp "%BASE%\wild\index.html" %BUCKET%/wild/index.html
%GCLOUD% storage cp "%BASE%\wild\*.png" %BUCKET%/wild/
