$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$base = "C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web3"
$bucket = "gs://didlu-imagestore/cardboard-experiment/pair"

& $gcloud storage cp "$base\index.html" "$bucket/index.html"
& $gcloud storage cp "$base\before.glb" "$bucket/before.glb"
& $gcloud storage cp "$base\after.glb"  "$bucket/after.glb"

& $gcloud storage objects update "$bucket/index.html" --content-type=text/html --cache-control="public,max-age=60"
& $gcloud storage objects update "$bucket/before.glb" --content-type=model/gltf-binary --cache-control="public,max-age=300"
& $gcloud storage objects update "$bucket/after.glb"  --content-type=model/gltf-binary --cache-control="public,max-age=300"

Write-Host "[done]"
