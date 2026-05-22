$ErrorActionPreference = 'Stop'
$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$base = "C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\web2"
$bucket = "gs://didlu-imagestore/cardboard-experiment/v2"

Write-Host "[deploy] hub"
& $gcloud storage cp "$base\index.html" "$bucket/index.html"

foreach ($d in @('wear','scale','corrugation','shapes','wild')) {
    if (Test-Path "$base\$d") {
        Write-Host "[deploy] $d"
        & $gcloud storage cp "$base\$d\index.html" "$bucket/$d/index.html"
        Get-ChildItem "$base\$d\*.png" | ForEach-Object {
            Write-Host "  upload $($_.Name)"
            & $gcloud storage cp $_.FullName "$bucket/$d/$($_.Name)"
        }
    }
}

Write-Host "[done]"
