$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$bucket = "gs://didlu-imagestore/cardboard-experiment/v2"

foreach ($d in @('','wear/','scale/','corrugation/','shapes/','wild/')) {
    Write-Host "[meta] ${d}index.html"
    & $gcloud storage objects update "${bucket}/${d}index.html" --content-type=text/html --cache-control="public,max-age=60"
}
