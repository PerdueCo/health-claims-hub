# CORB Batch Processing Guide
## MarkLogic Enterprise Claims Platform (MECP)

---

## What is CORB?

CORB (Content Reprocessing in Bulk) is MarkLogic's enterprise batch processing
framework. It executes XQuery modules against large sets of documents in parallel,
using multiple threads to maximize throughput.

In the MECP platform, CORB is used to perform bulk updates across all claim
documents — for example, stamping a processedDate field on every claim record
after adjudication.

### Why CORB instead of a single XQuery update?

| Approach | 10 documents | 1,000,000 documents |
|---|---|---|
| Single XQuery | Fast | Timeout risk, memory risk |
| CORB batch | Fast | Fast — parallel, resumable |

CORB is the enterprise standard for bulk document processing in MarkLogic
because it handles millions of documents safely, supports retry on failure,
and provides real-time progress reporting.

---

## Architecture
```
┌─────────────────────────────────────────────────┐
│              CORB Job (Java Client)             │
│                                                 │
│  1. Runs selector.xqy → gets 10 URIs           │
│  2. Distributes URIs across 2 worker threads    │
│  3. Each thread runs transform.xqy per URI      │
│  4. Reports progress and completion             │
└──────────────────┬──────────────────────────────┘
                   │ XCC (port 8041)
                   ▼
┌─────────────────────────────────────────────────┐
│         MarkLogic roxy-content database         │
│                                                 │
│  Before CORB:  claimId, status, amountBilled... │
│  After CORB:   claimId, status, amountBilled... │
│                processedDate: "2026-03-07"      │
└─────────────────────────────────────────────────┘
```

---

## File Inventory

| File | Location | Purpose |
|---|---|---|
| selector.xqy | corb/ and claims-roxy/src/corb/ | Returns count + URIs of all documents to process |
| transform.xqy | corb/ and claims-roxy/src/corb/ | Adds processedDate to each document |
| corb.properties | corb/ | Connection and job configuration |
| run-corb.ps1 | corb/ | Documented execution script |
| marklogic-corb-2.3.2.jar | claims-roxy/deploy/lib/java/ | CORB engine |
| marklogic-xcc-9.0.1.jar | claims-roxy/deploy/lib/java/ | MarkLogic XCC connector |

---

## How to Run

### Prerequisites

Verify Docker is running and platform is healthy before running CORB:
```powershell
.\scripts\verify.ps1
```

All 6 tests must pass before running CORB.

Verify Java is installed:
```powershell
java -version
```

### Run the batch job
```powershell
cd "C:\Users\cash america\documents\projects\health-claims-hub"
.\corb\run-corb.ps1
```

### Expected output
```
==============================================
 MECP CORB Batch Job Starting
==============================================
 Database  : roxy-content
 Selector  : selector.xqy
 Transform : transform.xqy
 Threads   : 2
==============================================

INFO: expecting total 10
INFO: completed all tasks 10/10
INFO: all done

==============================================
 CORB job complete. Verifying results...
==============================================
```

---

## Verify Results

### Check a single claim for processedDate
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?id=CLM-0001"
```

Expected — processedDate field present in response:
```json
{
  "claimId": "CLM-0001",
  "status": "PAID",
  "processedDate": "2026-03-07"
}
```

### Check all 10 claims were updated
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims" | Select-String "processedDate"
```

Expected: processedDate appears 10 times in the output.

---

## Module Reference

### selector.xqy

Returns the total document count followed by all document URIs.
CORB requires the count as the first item in the returned sequence.
```xquery
xquery version "1.0-ml";
let $uris := cts:uris((), (), cts:true-query())
return (fn:count($uris), $uris)
```

### transform.xqy

Receives each URI from the selector and adds a processedDate field.
Idempotent — documents that already have processedDate are skipped.
```xquery
xquery version "1.0-ml";
declare variable $URI as xs:string external;

let $doc   := fn:doc($URI)
let $map   := xdmp:from-json($doc)
let $today := fn:format-date(fn:current-date(), "[Y0001]-[M01]-[D01]")
return
  if (map:contains($map, "processedDate")) then
    $URI
  else
    let $updated := xdmp:to-json(
      map:with($map, "processedDate", $today)
    )
    return xdmp:document-insert($URI, $updated)
```

---

## Configuration Reference

### corb.properties
```properties
XCC-CONNECTION-URI=xcc://admin:admin123@localhost:8041/roxy-content
URIS-MODULE=selector.xqy
PROCESS-MODULE=transform.xqy
THREAD-COUNT=2
MODULE-ROOT=/corb/
MODULES-DATABASE=roxy-modules
```

| Property | Value | Purpose |
|---|---|---|
| XCC-CONNECTION-URI | xcc://admin:admin123@localhost:8041/roxy-content | XCC connection to MarkLogic XDBC server |
| URIS-MODULE | selector.xqy | Module that returns document URIs |
| PROCESS-MODULE | transform.xqy | Module that processes each document |
| THREAD-COUNT | 2 | Parallel worker threads |
| MODULE-ROOT | /corb/ | Path prefix in roxy-modules database |
| MODULES-DATABASE | roxy-modules | Database where XQuery modules are stored |

---

## Troubleshooting

### SEVERE: Uris module does not return total URI count

The selector module must return the count as the first item.

Wrong:
```xquery
for $uri in cts:uris(()) return $uri
```

Correct:
```xquery
let $uris := cts:uris((), (), cts:true-query())
return (fn:count($uris), $uris)
```

### SEVERE: Error initializing CORB For input string

CORB options must be passed as Java system properties using -D flags,
not as positional arguments. See run-corb.ps1 for the correct syntax.

### Connection refused on port 8041

Port 8041 is the XDBC port used by XCC. Verify Docker is running:
```powershell
docker ps
```

MarkLogic must be healthy before CORB can connect.

### Transform ran but processedDate not appearing

The transform module may have found processedDate already present and
skipped the document. This is expected idempotent behavior. To force
a reprocess, remove the guard condition from transform.xqy.

---

## Production Considerations

This CORB job is configured for a 10-document development dataset.
For production scale the following changes would be made:

| Setting | Development | Production |
|---|---|---|
| THREAD-COUNT | 2 | 8-16 depending on server capacity |
| Document scope | All documents | Filtered by date range or status |
| Credentials | Plaintext in properties | Encrypted using CORB PrivateKeyDecrypter |
| Error handling | FAIL-ON-ERROR=true | FAIL-ON-ERROR=false with ERROR-FILE-NAME |
| Scheduling | Manual | Scheduled via cron or enterprise scheduler |

---

## Related Documentation

| Document | Purpose |
|---|---|
| README.md | Platform overview and quick start |
| TESTING.md | Three-level verification guide |
| docs/MECP_RCA_Prevention_Report.docx | Incident root cause analysis |

---

*MarkLogic Enterprise Claims Platform — CORB Batch Processing Guide*
*Built to federal consulting delivery standards*
