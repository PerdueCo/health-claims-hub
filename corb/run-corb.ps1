# =============================================================================
# run-corb.ps1
# CORB Batch Processing ? MarkLogic Enterprise Claims Platform (MECP)
# =============================================================================
#
# PURPOSE:
#   Runs CORB (Content Reprocessing in Bulk) against the roxy-content database.
#   Adds a processedDate field to all claim documents that do not already have one.
#
# PREREQUISITES:
#   - Docker must be running (docker compose up -d)
#   - MarkLogic must be healthy (verify.ps1 must pass)
#   - Java must be installed (java -version)
#
# USAGE:
#   cd "C:\Users\cash america\documents\projects\health-claims-hub"
#   .\corb\run-corb.ps1
#
# SAFE TO RUN MULTIPLE TIMES:
#   Transform checks for existing processedDate ? already processed docs skipped.
# =============================================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\cash america\documents\projects\health-claims-hub"
$CorbJar     = "$ProjectRoot\claims-roxy\deploy\lib\java\marklogic-corb-2.3.2.jar"
$XccJar      = "$ProjectRoot\claims-roxy\deploy\lib\java\marklogic-xcc-9.0.1.jar"

Write-Host ""
Write-Host "=============================================="
Write-Host " MECP CORB Batch Job Starting"
Write-Host "=============================================="
Write-Host " Database  : roxy-content"
Write-Host " Selector  : selector.xqy"
Write-Host " Transform : transform.xqy"
Write-Host " Threads   : 2"
Write-Host "=============================================="
Write-Host ""

java `
  -cp "$CorbJar;$XccJar" `
  "-DXCC-CONNECTION-URI=xcc://admin:admin123@localhost:8041/roxy-content" `
  "-DURIS-MODULE=selector.xqy" `
  "-DPROCESS-MODULE=transform.xqy" `
  "-DTHREAD-COUNT=2" `
  "-DMODULE-ROOT=/corb/" `
  "-DMODULES-DATABASE=roxy-modules" `
  com.marklogic.developer.corb.Manager

Write-Host ""
Write-Host "=============================================="
Write-Host " CORB job complete. Verifying results..."
Write-Host "=============================================="
Write-Host ""
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?id=CLM-0001"
