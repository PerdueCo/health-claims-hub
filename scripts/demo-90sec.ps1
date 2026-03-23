$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host "  MarkLogic Enterprise Claims Platform - 90 Second Demo"
Write-Host "============================================================"
Write-Host ""

function Step($text) {
    Write-Host ""
    Write-Host "------------------------------------------------------------"
    Write-Host "  $text"
    Write-Host "------------------------------------------------------------"
}

function Pass($text) {
    Write-Host "[PASS] $text" -ForegroundColor Green
}

function Fail($text) {
    Write-Host "[FAIL] $text" -ForegroundColor Red
}

function Info($text) {
    Write-Host "       $text"
}

$baseUrl = "http://localhost:8040"
$evalUrl = "http://localhost:8000/v1/eval"
$user = "admin:admin123"

$passCount = 0
$failCount = 0

try {
    Step "1. Check Claims Endpoint"

    $claimsAll = curl.exe -s -u $user "$baseUrl/v1/resources/claims?limit=5" | ConvertFrom-Json
    if ($claimsAll.claims.Count -ge 1) {
        Pass "Claims endpoint is reachable and returning data."
        Info ("Returned sample rows: " + $claimsAll.claims.Count)
        $passCount++
    }
    else {
        Fail "Claims endpoint returned no data."
        $failCount++
    }

    Step "2. Check Filtered Status Queries"

    $paid    = curl.exe -s -u $user "$baseUrl/v1/resources/claims?status=PAID&limit=5"    | ConvertFrom-Json
    $pending = curl.exe -s -u $user "$baseUrl/v1/resources/claims?status=PENDING&limit=5" | ConvertFrom-Json
    $denied  = curl.exe -s -u $user "$baseUrl/v1/resources/claims?status=DENIED&limit=5"  | ConvertFrom-Json

    $paidOk    = ($paid.claims | Where-Object { $_.status -ne "PAID" }).Count -eq 0
    $pendingOk = ($pending.claims | Where-Object { $_.status -ne "PENDING" }).Count -eq 0
    $deniedOk  = ($denied.claims | Where-Object { $_.status -ne "DENIED" }).Count -eq 0

    if ($paidOk -and $pendingOk -and $deniedOk) {
        Pass "Status filters are working correctly."
        Info ("PAID total: " + $paid.total + " | returned: " + $paid.returned)
        Info ("PENDING total: " + $pending.total + " | returned: " + $pending.returned)
        Info ("DENIED total: " + $denied.total + " | returned: " + $denied.returned)
        $passCount++
    }
    else {
        Fail "One or more status filters returned mixed results."
        $failCount++
    }

    Step "3. Check Limit Handling"

    $limit25 = curl.exe -s -u $user "$baseUrl/v1/resources/claims?status=PENDING&limit=25" | ConvertFrom-Json

    if ($limit25.returned -eq 25 -and $limit25.claims.Count -eq 25) {
        Pass "Limit parameter works correctly."
        Info ("PENDING total: " + $limit25.total + " | returned: " + $limit25.returned)
        $passCount++
    }
    else {
        Fail "Limit parameter did not behave as expected."
        $failCount++
    }

    Step "4. Verify Database Status Distribution"

    $xq = @'
for $v in cts:values(cts:json-property-reference("status"))
order by $v
return concat($v, " : ", cts:frequency($v))
'@

    $tempFile = "status-check.xqy"
    $xq | Set-Content $tempFile

    $evalRaw = curl.exe --digest -s -u $user `
        --data-urlencode "xquery@$tempFile" `
        --data-urlencode "database=roxy-content" `
        $evalUrl

    Remove-Item $tempFile -ErrorAction SilentlyContinue

    $paidCount    = [int]([regex]::Match($evalRaw, 'PAID\s*:\s*(\d+)').Groups[1].Value)
    $pendingCount = [int]([regex]::Match($evalRaw, 'PENDING\s*:\s*(\d+)').Groups[1].Value)
    $deniedCount  = [int]([regex]::Match($evalRaw, 'DENIED\s*:\s*(\d+)').Groups[1].Value)

    if ($paidCount -gt 0 -and $pendingCount -gt 0 -and $deniedCount -gt 0) {
        Pass "Direct database verification succeeded."
        Info ("PAID: $paidCount | PENDING: $pendingCount | DENIED: $deniedCount")
        $passCount++
    }
    else {
        Fail "Could not verify database status distribution."
        $failCount++
    }

    Step "5. Cross-Check API Totals vs Database Totals"

    if ($paid.total -eq $paidCount -and $pending.total -eq $pendingCount -and $denied.total -eq $deniedCount) {
        Pass "API totals match direct MarkLogic database counts."
        $passCount++
    }
    else {
        Fail "API totals do not match database counts."
        Info ("API PAID=$($paid.total) DB PAID=$paidCount")
        Info ("API PENDING=$($pending.total) DB PENDING=$pendingCount")
        Info ("API DENIED=$($denied.total) DB DENIED=$deniedCount")
        $failCount++
    }

    Step "6. Final Demo Summary"

    Write-Host ""
    Write-Host "============================================================"
    Write-Host ("  Result: {0} PASSED | {1} FAILED" -f $passCount, $failCount)
    if ($failCount -eq 0) {
        Write-Host "  Platform is READY for demonstration" -ForegroundColor Green
    }
    else {
        Write-Host "  Platform needs attention before demonstration" -ForegroundColor Yellow
    }
    Write-Host "============================================================"
    Write-Host ""
}
catch {
    Fail $_.Exception.Message
    Write-Host ""
    Write-Host "============================================================"
    Write-Host ("  Result: {0} PASSED | {1} FAILED" -f $passCount, ($failCount + 1))
    Write-Host "  Demo script terminated early" -ForegroundColor Red
    Write-Host "============================================================"
    Write-Host ""
    exit 1
}