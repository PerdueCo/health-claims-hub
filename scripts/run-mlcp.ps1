# =============================================================================
# run-mlcp.ps1
# MLCP Bulk Load ? MarkLogic Enterprise Claims Platform (MECP)
# =============================================================================
#
# PURPOSE:
#   Loads 1000 bulk claim JSON documents into the roxy-content database
#   using MarkLogic Content Pump (MLCP).
#
# PREREQUISITES:
#   - Docker must be running (docker compose up -d)
#   - verify.ps1 must pass before running this script
#   - MLCP must be installed at C:\mlcp\mlcp-12.0.1-bin\mlcp-12.0.1
#
# USAGE:
#   cd "C:\Users\cash america\documents\projects\health-claims-hub"
#   .\scripts\run-mlcp.ps1
#
# EXPECTED OUTPUT:
#   INFO: MLCP completed successfully
#   Document count after load: 1010
#
# NOTE:
#   MLCP is a client-side tool that runs on the local machine and streams
#   documents into MarkLogic over XCC (port 8041). It is not part of the
#   Docker container. The original 10 seed claims are loaded automatically
#   by Roxy on every docker compose up. The 1000 bulk claims require MLCP.
# =============================================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\cash america\documents\projects\health-claims-hub"
$MlcpBat     = "C:\mlcp\mlcp-12.0.1-bin\mlcp-12.0.1\bin\mlcp.bat"
$InputDir    = "$ProjectRoot\data\bulk-claims"

Write-Host ""
Write-Host "=============================================="
Write-Host " MECP MLCP Bulk Load Starting"
Write-Host "=============================================="
Write-Host " Source    : data/bulk-claims/ (1000 files)"
Write-Host " Database  : roxy-content"
Write-Host " URI prefix: /claims/"
Write-Host " Collection: bulk-claims"
Write-Host " Threads   : 4"
Write-Host "=============================================="
Write-Host ""

& $MlcpBat import `
  -host localhost `
  -port 8041 `
  -username admin `
  -password admin123 `
  -input_file_path "$InputDir" `
  -input_file_type documents `
  -document_type json `
  -output_uri_prefix "/claims/" `
  -output_uri_replace ".*bulk-claims,''" `
  -output_collections "bulk-claims" `
  -database roxy-content `
  -thread_count 4

Write-Host ""
Write-Host "=============================================="
Write-Host " Load complete. Verifying document count..."
Write-Host "=============================================="
Write-Host ""

curl.exe --digest -u admin:admin123 `
  --data "xquery=cts:estimate(cts:true-query())&database=roxy-content" `
  http://localhost:8000/v1/eval

Write-Host ""
Write-Host "Expected: 1010 (10 seed + 1000 bulk)"
