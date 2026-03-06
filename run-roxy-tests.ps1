Write-Host "=== STEP 0: Fix local.properties (localhost -> marklogic) ==="

(Get-Content .\claims-roxy\deploy\local.properties) `
  -replace 'localhost','marklogic' `
  | Set-Content .\claims-roxy\deploy\local.properties -Encoding UTF8

Write-Host "=== STEP 1: Show current Roxy host settings ==="
Get-Content .\claims-roxy\deploy\local.properties | Select-String "mlHost|xccHost|localhost"

Write-Host "=== STEP 2: Testing Roxy -> MarkLogic connectivity ==="
docker compose run --rm roxy sh -lc `
"apk add --no-cache busybox-extras >/dev/null 2>&1; \
echo TESTING; \
nc -zv marklogic 8000; \
nc -zv marklogic 8041"

Write-Host "=== STEP 3: Deploy modules ==="
docker compose run --rm -w /work/claims-roxy roxy ./ml local deploy modules