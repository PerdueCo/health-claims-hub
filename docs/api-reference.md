# MECP API Reference

Complete endpoint documentation for the MarkLogic Enterprise Claims Platform.
All endpoints are served from port 8040 using Basic authentication.

**Base URL:** `http://localhost:8040`
**Auth:** Basic — username: `admin` password: `admin123`

---

## Endpoints

### GET /v1/resources/claims

Returns all claims in the database. No hardcoded limit — returns every document
in the /claims/ directory regardless of count.

**Request:**
```powershell
curl.exe -u admin:admin123 http://localhost:8040/v1/resources/claims
```

**Response:**
```json
{
  "total": 1010,
  "claims": [ ... ]
}
```

---

### GET /v1/resources/claims?status={STATUS}

Returns claims filtered by status. Valid values: `PAID`, `DENIED`, `PENDING`.

**Request:**
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=PAID"
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=DENIED"
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?status=PENDING"
```

**Response:**
```json
{
  "total": 505,
  "filter": "PAID",
  "claims": [ ... ]
}
```

---

### GET /v1/resources/claims?id={CLAIM_ID}

Returns a single claim by claim ID. Case insensitive.

**Request:**
```powershell
curl.exe -u admin:admin123 "http://localhost:8040/v1/resources/claims?id=CLM-0001"
```

**Response:**
```json
{
  "total": 1,
  "id": "CLM-0001",
  "claims": [
    {
      "claimId": "CLM-0001",
      "memberId": "M-10001",
      "provider": "Peachtree Clinic",
      "serviceDate": "2026-02-25",
      "status": "PAID",
      "amountBilled": 420,
      "amountAllowed": 310,
      "amountPaid": 295,
      "diagnosisCodes": ["Z00.00"],
      "procedureCodes": ["99395"],
      "facility": { "state": "GA", "city": "Atlanta" }
    }
  ]
}
```

---

## XQuery Eval Endpoints

All XQuery endpoints use port 8000 with Digest authentication.

### Document Count
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=cts:estimate(cts:true-query())&database=roxy-content" `
  http://localhost:8000/v1/eval
```

### Status Frequency Distribution
```powershell
curl.exe --digest -u admin:admin123 `
  --data "xquery=for $v in cts:values(cts:json-property-reference('status')) return concat($v,': ',cts:frequency($v))&database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample response:**
```
DENIED: 310
PAID: 505
PENDING: 185
```

---

## SPARQL Endpoints

### Total Billed by Status
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-amount-by-status.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

**Sample response:**
```
Status: DENIED  | Claims: 310 | Total Billed: $1,187,432
Status: PAID    | Claims: 505 | Total Billed: $2,043,217
Status: PENDING | Claims: 185 | Total Billed: $743,891
```

### PENDING Claims by Provider
```powershell
curl.exe --digest -u admin:admin123 `
  --data-urlencode "xquery@corb/sparql-pending-by-provider.xqy" `
  --data "database=roxy-content" `
  http://localhost:8000/v1/eval
```

---

## Port Reference

| Port | Service | Auth | Purpose |
|---|---|---|---|
| 8001 | MarkLogic Admin UI | admin/admin123 | Browser administration |
| 8002 | Manage API | Digest | Health and management |
| 8000 | App Services | Digest | XQuery eval, SPARQL |
| 8040 | MECP REST Server | Basic | Claims API |
| 8041 | XDBC Server | Basic | MLCP bulk ingest, CORB |

---

## Claim Document Schema

| Field | Type | Description |
|---|---|---|
| claimId | string | Unique claim identifier (CLM-XXXX) |
| memberId | string | Member identifier (M-XXXXX) |
| provider | string | Healthcare provider name |
| serviceDate | date | Date service was rendered |
| submittedDate | date | Date claim was submitted |
| status | string | PAID, DENIED, or PENDING |
| amountBilled | number | Total amount billed |
| amountAllowed | number | Allowed amount (PAID claims only) |
| amountPaid | number | Amount paid (PAID claims only) |
| diagnosisCodes | array | ICD-10 diagnosis codes |
| procedureCodes | array | CPT procedure codes |
| facility.state | string | State where service was rendered |
| facility.city | string | City where service was rendered |
| denialReason | string | Denial reason (DENIED claims only) |
| processedDate | date | Date CORB pipeline processed the claim |
| priority | string | LOW, MEDIUM, or HIGH (set by pipeline) |
| highValueReview | boolean | True if amountBilled > $5000 |
| pipelineComplete | boolean | True after CORB 6-step pipeline |
| platformVersion | string | MECP version that processed the claim |

---

*MECP API Reference — v1.1*
